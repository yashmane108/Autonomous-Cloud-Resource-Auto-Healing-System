import boto3
from datetime import datetime, timedelta
import requests

ec2 = boto3.client('ec2')
cloudwatch = boto3.client('cloudwatch')

CPU_THRESHOLD = 80
MEMORY_THRESHOLD = 80
EVALUATION_MINUTES = 10   # sliding window
HEALTH_URL = "http://your-app-url/health"

def get_average_metric(instance_id, metric_name, namespace='AWS/EC2'):
    response = cloudwatch.get_metric_statistics(
        Namespace=namespace,
        MetricName=metric_name,
        Dimensions=[
            {'Name': 'InstanceId', 'Value': instance_id}
        ],
        StartTime=datetime.utcnow() - timedelta(minutes=EVALUATION_MINUTES),
        EndTime=datetime.utcnow(),
        Period=300,
        Statistics=['Average']
    )

    datapoints = response['Datapoints']

    if not datapoints:
        return None

    # sort datapoints by timestamp
    datapoints.sort(key=lambda x: x['Timestamp'])
    
    values = [point['Average'] for point in datapoints]
    avg_value = sum(values) / len(values)

    return avg_value


def is_app_healthy():
    try:
        response = requests.get(HEALTH_URL, timeout=3)
        return response.status_code == 200
    except:
        return False


def lambda_handler(event, context):

    print("===== AUTO-HEAL EXECUTION START =====")

    instances = ec2.describe_instances(
        Filters=[
            {'Name': 'tag:AutoHeal', 'Values': ['True']},
            {'Name': 'instance-state-name', 'Values': ['running']}
        ]
    )

    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:

            instance_id = instance['InstanceId']
            print(f"\nChecking Instance: {instance_id}")

            cpu_avg = get_average_metric(instance_id, 'CPUUtilization')
            memory_avg = get_average_metric(instance_id, 'MemoryUtilization', 'CWAgent')

            print(f"CPU Avg ({EVALUATION_MINUTES} min): {cpu_avg}")
            print(f"Memory Avg: {memory_avg}")

            app_healthy = is_app_healthy()
            print(f"App Health: {'Healthy' if app_healthy else 'Unhealthy'}")

            # ----------- DECISION LOGIC -----------

            # Case 1: App crash
            if not app_healthy:
                print("ACTION: App down → Restarting instance")
                ec2.reboot_instances(InstanceIds=[instance_id])
                continue

            # Case 2: Memory leak
            if memory_avg and memory_avg > MEMORY_THRESHOLD:
                print("ACTION: High memory → Restarting instance")
                ec2.reboot_instances(InstanceIds=[instance_id])
                continue

            # Case 3: Continuous high CPU
            if cpu_avg and cpu_avg > CPU_THRESHOLD:
                print("WARNING: Sustained high CPU detected")

                # First action: Restart
                print("ACTION: Restarting instance")
                ec2.reboot_instances(InstanceIds=[instance_id])

                # Optional: Next cycle if still high → Stop
                # (Handled in next Lambda execution)
                continue

            print("STATUS: Instance healthy")

    print("\n===== AUTO-HEAL EXECUTION END =====")
