 Project 

Just Basic Overview I will Be update detailed steps very sonn till check my other project
https://github.com/yashmane108/Autonomous-Cloud-Resource-Auto-Healing-System


# Phase 1
**EC2 Auto-Healing system**

We will build this architecture:

```
EC2 Instance
     │
     │ (CPU > 40%)
     ▼
CloudWatch Alarm
     │
     ▼
Lambda Function
     │
     ▼
Reboot EC2 Instance
```
---

# Step 1 — Create EC2 Instance
Go to:

**EC2 → Launch Instance**

Settings:

| Setting | Value |
| ----- | ----- |
| Name | AutoHeal-Server |
| AMI | Amazon Linux 2 |
| Instance type | t2.micro |
| Key pair | create or select |
| Security group | allow SSH |
Launch the instance.

After launch copy the **Instance ID**
Example:

```
i-0abc123456789xyz
```
Save it.

---

# Step 2 — Create Lambda IAM Role
Go to:

**IAM → Roles → Create Role**

Choose:

```
AWS service
```
Service:

```
Lambda
```
Next → Attach policies:

Add:

```
AmazonEC2FullAccess
AWSLambdaBasicExecutionRole
```
Role name:

```
lambda-ec2-autoheal-role
```
Create role.

---

# Step 3 — Create Lambda Function
Go to:

**Lambda → Create Function**

Settings:

| Setting | Value |
| ----- | ----- |
| Function name | ec2-autoheal |
| Runtime | Python 3.10 |
| Execution role | lambda-ec2-autoheal-role |
Create function.

---

# Step 4 — Add Lambda Code
paste this for reboot:

```
import boto3
from datetime import datetime, timedelta

ec2 = boto3.client('ec2')
cloudwatch = boto3.client('cloudwatch')

CPU_THRESHOLD = 50

def lambda_handler(event, context):

    instances = ec2.describe_instances(
        Filters=[
            {'Name': 'tag:AutoHeal', 'Values': ['True']},
            {'Name': 'instance-state-name', 'Values': ['running']}
        ]
    )

    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:

            instance_id = instance['InstanceId']

            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[
                    {
                        'Name': 'InstanceId',
                        'Value': instance_id
                    }
                ],
                StartTime=datetime.utcnow() - timedelta(minutes=5),
                EndTime=datetime.utcnow(),
                Period=300,
                Statistics=['Average']
            )

            datapoints = response['Datapoints']

            if datapoints:
                cpu = datapoints[-1]['Average']

                print(f"{instance_id} CPU = {cpu}")

                if cpu > CPU_THRESHOLD:
                    print(f"Stopping instance {instance_id}")

                    ec2.stop_instances(
                        InstanceIds=[instance_id]
                    )
```


Click **Deploy**.

# Click **Add permissions skip this **
![image.png](https://eraser.imgix.net/workspaces/vreiCe9sB3JnOVNTjdgY/kLYgtkRdl2MQtyG05vVHxbkQ5ua2/image_PxJuYBlIIfyV-0CdFv1p4.png?ixlib=js-3.8.0 "image.png")



Click:

**Add permissions**

---

# Choose **AWS Service**
![image.png](https://eraser.imgix.net/workspaces/vreiCe9sB3JnOVNTjdgY/kLYgtkRdl2MQtyG05vVHxbkQ5ua2/image_NMFsVYlAcs7_OyxxJzE0v.png?ixlib=js-3.8.0 "image.png")



![image.png](https://eraser.imgix.net/workspaces/vreiCe9sB3JnOVNTjdgY/kLYgtkRdl2MQtyG05vVHxbkQ5ua2/image_CF5M8FGEf3jioAntYjOm_.png?ixlib=js-3.8.0 "image.png")

A form will open.

Fill it exactly like this:

**Principal**

```
AWS Service
```
**Service**

```
EventBridge (CloudWatch Events)
```
**Source ARN**

Paste your alarm ARN:

```
arn:aws:cloudwatch:us-east-1:362552858462:alarm:AutoHeal-CPU-Alarm
```
**Statement ID**

```
AllowCWAlarmInvoke
```
Then click:

✅ **Save**

---

# Step 3 — Verify it appears
After saving you should see something like:

| Statement ID | Principal | Action |
| ----- | ----- | ----- |
| AllowCWAlarmInvoke | cloudwatch.amazonaws.com | lambda:InvokeFunction |
If this appears → **permission is correct**.

![image.png](https://eraser.imgix.net/workspaces/vreiCe9sB3JnOVNTjdgY/kLYgtkRdl2MQtyG05vVHxbkQ5ua2/image_f1rSWNKASE9Q2AUBs9v70.png?ixlib=js-3.8.0 "image.png")



direct to cloud shell

```
aws lambda add-permission \
--function-name ec2-autoheal \
--statement-id cloudwatch-alarm \
--action lambda:InvokeFunction \
--principal cloudwatch.amazonaws.com \
--source-arn arn:aws:cloudwatch:us-east-1:362552858462:alarm:AutoHeal-CPU-Alarm
```
---

# Very Important (for your resume project)
Your architecture will now be:

```
EC2 Instance
     │
     ▼
CloudWatch Metric (CPUUtilization)
     │
     ▼
CloudWatch Alarm
     │
     ▼
Lambda Function
     │
     ▼
Stop EC2 Instance
```
This is the **core Auto-Healing System**.

---

# Step 5 — Create CloudWatch Alarm
Go to:

**CloudWatch → Alarms → Create Alarm**

Select metric:

```
EC2 → Per-Instance Metrics → CPUUtilization
```
Choose your instance.

Set:

| Setting | Value |
| ----- | ----- |
| Threshold | >= 40 |
| Period | 1 minute |
| Evaluation periods | 1 |
---



---





```
aws lambda add-permission \
--function-name ec2-autoheal \
--statement-id AllowCloudWatchInvoke \
--action lambda:InvokeFunction \
--principal cloudwatch.amazonaws.com \
--source-arn arn:aws:cloudwatch:us-east-1:362552858462:alarm:ec2_autoheal_alarm \
--region us-east-1
```
















![image.png](https://eraser.imgix.net/workspaces/vreiCe9sB3JnOVNTjdgY/kLYgtkRdl2MQtyG05vVHxbkQ5ua2/image_4xR2UoFfJMzJL8h05kUkF.png?ixlib=js-3.8.0 "image.png")











---

# Step 1 — Create EC2 Instance
Go to:

```
EC2 → Launch instance
```
Recommended settings:

```
Name: autoheal-test
AMI: Amazon Linux
Instance type: t2.micro
```
Launch the instance.

Note the **Instance ID**, e.g.:

```
i-xxxxxxxxxxxx
```
---

# Step 2 — Create IAM Role for Lambda
Go to:

```
IAM → Roles → Create role
```
Choose:

```
Trusted entity: AWS service
Use case: Lambda
```
Attach policy:

```
AmazonEC2FullAccess
AWSLambdaBasicExecutionRole
```
Role name:

```
lambda-ec2-autoheal-role
```
Create role.

---

# Step 3 — Create Lambda Function
Go to:

```
Lambda → Create function
```
Settings:

```
Function name: ec2-autoheal
Runtime: Python 3.10
Execution role: Use existing role
Role: lambda-ec2-autoheal-role
```
---

# Step 4 — Add Lambda Code (check below also)
Paste this code:

```python
import boto3
INSTANCE_ID = "YOUR_INSTANCE_ID"
def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    ec2.stop_instances(
        InstanceIds=[INSTANCE_ID]
    )
    print("EC2 stop command sent")
```
Replace:

```
YOUR_INSTANCE_ID
```
Deploy.

---

# Step 5 — Test Lambda
Click:

```
Test
```
Expected result:

```
EC2 instance → stopping → stopped
```
If this works, Lambda is correct.

---

# Step 6 — Create CloudWatch Alarm
Go to:

```
CloudWatch → Alarms → Create alarm
```
Metric:

```
EC2 → Per Instance Metrics → CPUUtilization
```
Select your instance.

Condition:

```
CPUUtilization ≥ 80
```
Period:

```
1 minute
```
Alarm name:

```
ec2-autoheal-alarm
```
Create alarm.

---

# Step 7 — Create EventBridge Rule
Go to:

```
EventBridge → Rules → Create rule
```
Rule name:

```
ec2-autoheal-rule
```
Event pattern:

```json
{
  "source": ["aws.cloudwatch"],
  "detail-type": ["CloudWatch Alarm State Change"],
  "detail": {
    "alarmName": ["ec2-autoheal-alarm"],
    "state": {
      "value": ["ALARM"]
    }
  }
}
```
---

# Step 8 — Add Target
Target type:

```
Lambda function
```
Target:

```
ec2-autoheal
```
Input:

```
Matched event
```
Create rule.

---

# Step 9 — Test System
Increase CPU on EC2:

```
yes > /dev/null
```
Wait until:

```
CloudWatch Alarm → ALARM
```
Then:

```
EC2 → stopping → stoppeimport boto3
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
```






lambda/config/permi

**Execution role:**

[﻿AWSLambdaBasicExecutionRole-f0b38c70-0e75-4bdd-8c60-466802172ea0](https://us-east-1.console.aws.amazon.com/iam/home?region=us-east-1#/policies/details/arn%3Aaws%3Aiam%3A%3A362552858462%3Apolicy%2Fservice-role%2FAWSLambdaBasicExecutionRole-f0b38c70-0e75-4bdd-8c60-466802172ea0) 

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "logs:CreateLogGroup",
            "Resource": "arn:aws:logs:us-east-1:362552858462:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": [
                "arn:aws:logs:us-east-1:362552858462:log-group:/aws/lambda/rds-autoheal:*"
            ]
        }
    ]
}
```
[﻿rds-role-AH](https://us-east-1.console.aws.amazon.com/iam/home?region=us-east-1#/roles/details/rds-autoheal-role-i9snyupa/editPolicy/rds-role-AH?step=addPermissions) 

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "rds:AddTagsToResource",
                "iam:PassRole",
                "rds:ListTagsForResource",
                "rds:DescribeDBInstances",
                "rds:CreateDBInstanceReadReplica",
                "rds:DeleteDBInstance",
                "cloudwatch:GetMetricStatistics",
                "cloudwatch:ListMetrics"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "arn:aws:lambda:us-east-1:362552858462:function:rds-autoheal"
            ]
        }
    ]
}
```


### **Resource-based policy statements**
![image.png](https://eraser.imgix.net/workspaces/vreiCe9sB3JnOVNTjdgY/kLYgtkRdl2MQtyG05vVHxbkQ5ua2/image_Tp3PWmNFoazc6Gynly2zP.png?ixlib=js-3.8.0 "image.png")













Amazon EventBridge/Scheduled rule/ rds-autoheal-schedule

### **Event schedule**
Fixed rate of

1 minute



```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "arn:aws:lambda:us-east-1:362552858462:function:rds-autoheal"
            ]
        }
    ]
}
```
![image.png](https://eraser.imgix.net/workspaces/vreiCe9sB3JnOVNTjdgY/kLYgtkRdl2MQtyG05vVHxbkQ5ua2/image_YEqWgmRq7qEhyAXio1Tou.png?ixlib=js-3.8.0 "image.png")



Amazon EventBridge/Scheduled rule/ ec2-autoheal-schedule

![image.png](https://eraser.imgix.net/workspaces/vreiCe9sB3JnOVNTjdgY/kLYgtkRdl2MQtyG05vVHxbkQ5ua2/image_AzWXQsdlbMefxba7A-tlm.png?ixlib=js-3.8.0 "image.png")

there role code is (not sure but try)

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "arn:aws:lambda:us-east-1:362552858462:function:ec2-autoheal"
            ]
        }
    ]
}
```


