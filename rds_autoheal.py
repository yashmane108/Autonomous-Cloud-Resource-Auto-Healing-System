import boto3
from datetime import datetime, timedelta
import time

rds = boto3.client('rds')
cloudwatch = boto3.client('cloudwatch')

MAX_REPLICAS = 3


# ---------------- METRIC FUNCTIONS ----------------
def get_metric(db_id, metric, minutes, period):
    response = cloudwatch.get_metric_statistics(
        Namespace='AWS/RDS',
        MetricName=metric,
        Dimensions=[{'Name': 'DBInstanceIdentifier', 'Value': db_id}],
        StartTime=datetime.utcnow() - timedelta(minutes=minutes),
        EndTime=datetime.utcnow(),
        Period=period,
        Statistics=['Average']
    )
    return sorted(response.get('Datapoints', []), key=lambda x: x['Timestamp'])


# ---------------- HUMAN READABLE SLIDING LOG ----------------
def print_decision_windows(datapoints, window_size=3, scale_threshold=80, high_threshold=90):

    values = [round(p['Average'], 2) for p in datapoints]
    times  = [p['Timestamp'] for p in datapoints]

    print("\n===== SLIDING DECISION ANALYSIS =====")

    if len(values) < window_size:
        print("Not enough data")
        return

    for i in range(len(values) - window_size + 1):

        window_vals = values[i:i+window_size]
        start = times[i]
        end   = times[i+window_size-1]

        avg = sum(window_vals) / len(window_vals)

        if avg > high_threshold:
            decision = "🔥 SCALE UP (HIGH LOAD)"
        elif avg > scale_threshold:
            decision = "⚡ SCALE UP (1 replica)"
        else:
            decision = "✅ NO SCALE"

        print(f"\n{start.strftime('%H:%M')} → {end.strftime('%H:%M')}")
        print(f"Values: {window_vals}")
        print(f"Avg: {round(avg,2)} → {decision}")


# ---------------- MAIN ----------------
def lambda_handler(event, context):

    dbs = rds.describe_db_instances()['DBInstances']

    for db in dbs:

        db_id = db['DBInstanceIdentifier']
        arn = db['DBInstanceArn']

        print(f"\n==============================")
        print(f"Processing DB: {db_id}")
        print(f"==============================")

        # ---------------- TAG CHECK ----------------
        tags = rds.list_tags_for_resource(ResourceName=arn)['TagList']
        autoheal = any(t['Key'] == 'AutoHeal' and t['Value'] == 'True' for t in tags)

        if not autoheal:
            continue

        # ---------------- STATUS CHECK ----------------
        if db['DBInstanceStatus'] != "available":
            print("DB not available → skip")
            continue

        # ---------------- METRICS ----------------
        cpu_short_dp = get_metric(db_id, 'CPUUtilization', 5, 60)
        cpu_long_dp  = get_metric(db_id, 'CPUUtilization', 45, 300)
        conn_long_dp = get_metric(db_id, 'DatabaseConnections', 45, 300)

        if not cpu_short_dp or not cpu_long_dp:
            print("No metrics → skip")
            continue

        cpu_short = [p['Average'] for p in cpu_short_dp]
        cpu_long  = [p['Average'] for p in cpu_long_dp]
        conn_long = [p['Average'] for p in conn_long_dp] if conn_long_dp else []

        avg_cpu_short = sum(cpu_short) / len(cpu_short)
        avg_cpu_long  = sum(cpu_long) / len(cpu_long)
        avg_conn_long = sum(conn_long) / len(conn_long) if conn_long else 0

        print(f"\n📊 SUMMARY")
        print(f"CPU short avg (5 min): {round(avg_cpu_short,2)}")
        print(f"CPU long avg (45 min): {round(avg_cpu_long,2)}")
        print(f"Connections avg: {round(avg_conn_long,2)}")

        # 🔥 ADD THIS LINE
        print(f"Max CPU in window: {round(max(cpu_short),2)}")

        # 🔥 HUMAN READABLE LOGS
        print_decision_windows(cpu_short_dp, window_size=3)

        # ---------------- REPLICA INFO ----------------
        replicas = db.get('ReadReplicaDBInstanceIdentifiers', [])
        ready_replicas = []
        creating = False

        for r in replicas:
            try:
                info = rds.describe_db_instances(DBInstanceIdentifier=r)['DBInstances'][0]

                if info['DBInstanceStatus'] == 'available':
                    ready_replicas.append(r)

                elif info['DBInstanceStatus'] == 'creating':
                    creating = True
                    print(f"{r} still creating → skip scaling")

            except Exception as e:
                print("Replica check error:", str(e))

        replica_count = len(ready_replicas)
        print(f"\nReplica count: {replica_count}")

        # ---------------- LOCK ----------------
        if creating:
            print("Replica already creating → no action")
            continue

        # ---------------- MAX LIMIT ----------------
        if replica_count >= MAX_REPLICAS:
            print("Max replicas reached → no scaling")
            continue

        # ======================================================
        # 🚨 EMERGENCY SPIKE
        # ======================================================
        if max(cpu_short) > 85:
            print("🚨 Emergency spike detected")

            new_name = f"{db_id}-replica-{int(time.time())}"

            try:
                print(f"Creating replica: {new_name}")
                rds.create_db_instance_read_replica(
                    DBInstanceIdentifier=new_name,
                    SourceDBInstanceIdentifier=db_id
                )
            except Exception as e:
                print("Create error:", str(e))

            continue

        # ======================================================
        # 🔥 NORMAL SCALE-UP
        # ======================================================
        if avg_cpu_short > 70 and avg_cpu_long > 50:
            print("⚡ Normal scale-up triggered")

            new_name = f"{db_id}-replica-{int(time.time())}"

            try:
                print(f"Creating replica: {new_name}")
                rds.create_db_instance_read_replica(
                    DBInstanceIdentifier=new_name,
                    SourceDBInstanceIdentifier=db_id
                )
            except Exception as e:
                print("Create error:", str(e))

            continue

        # ======================================================
        # 🔻 SCALE DOWN (SAFE)
        # ======================================================
        if avg_cpu_long < 20 and avg_conn_long < 10:

            print("Low usage detected")

            # Step 1: reduce gradually
            if replica_count > 1:
                replica_to_delete = ready_replicas[-1]

                print(f"Deleting extra replica: {replica_to_delete}")

                try:
                    rds.delete_db_instance(
                        DBInstanceIdentifier=replica_to_delete,
                        SkipFinalSnapshot=True
                    )
                except Exception as e:
                    print("Delete error:", str(e))

            # Step 2: protect last replica
            elif replica_count == 1:

                if avg_cpu_short < 10:
                    print(f"Deleting last replica: {ready_replicas[0]}")

                    try:
                        rds.delete_db_instance(
                            DBInstanceIdentifier=ready_replicas[0],
                            SkipFinalSnapshot=True
                        )
                    except Exception as e:
                        print("Delete error:", str(e))
                else:
                    print("Keeping 1 replica as buffer")

    return "Auto-heal cycle completed"
