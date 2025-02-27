# WARNING: Do not hardcode AWS credentials in your local files or repositories.
# Use AWS CLI or environment variables to securely manage credentials.

import os
import boto3
import pandas as pd
import glob
import logging
import datetime
from datetime import datetime

# 로그 설정
logging.basicConfig(level=logging.INFO)

### Account ID 및 Region 정보를 Dict 형태로 기입

account_region_map = {
    #"000011112222": ["ap-northeast-2"],       #예시 정보
}

CREDENTIALS_DIR = "{path_to_your_key_dir}"
all_ec2_info = []

#CSV 파일로 저장된 access key, secret key 파일들을 모두 읽음
csv_files = glob.glob(f"{CREDENTIALS_DIR}/*.csv")

if not csv_files:
    logging.error("No credential files found in the 'credential' folder.")
    exit()

for csv_file in csv_files:
    logging.info(f"Processing credential file: {csv_file}")
    
    # 자격증명 읽기
    try:
        credentials = pd.read_csv(csv_file)
        access_key = credentials['Access key ID'][0]
        secret_key = credentials['Secret access key'][0]
        logging.info(f"Successfully read credentials from {csv_file}")
    except Exception as e:
        logging.error(f"Error reading credential file {csv_file}: {e}")
        continue

    # 세션 생성
    try:
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        sts_client = session.client('sts')
        account_id = sts_client.get_caller_identity()["Account"]
        logging.info(f"Account ID: {account_id} from {csv_file}")
    except Exception as e:
        logging.error(f"Error retrieving account ID with credentials from {csv_file}: {e}")
        continue

    # 계정 ID로 리전 목록 가져오기
    regions = account_region_map.get(account_id)
    if not regions:
        logging.warning(f"No region mapping found for account ID {account_id}. Skipping this account.")
        continue
    logging.info(f"Regions for account ID {account_id}: {regions}")

    # 각 리전에 대해 EC2 정보 수집
    for region in regions:
        try:
            ec2_client = session.client('ec2', region_name=region)
            asg_client = session.client('autoscaling', region_name=region)
            instances = ec2_client.describe_instances()
            logging.info(f"Retrieved EC2 instances for account ID {account_id} in region {region}")
            
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    instance_info = {
                        "Region": region,
                        "AccountID": account_id,
                        "Name": None,
                        "InstanceId": instance.get('InstanceId'),
                        "InstanceType": instance.get('InstanceType'),
                        "State": instance.get('State', {}).get('Name'),
                        "PublicIpAddress": instance.get('PublicIpAddress'),
                        "PrivateIpAddress": instance.get('PrivateIpAddress'),
                        "AutoScalingGroupName": None,
                        "LaunchTemplateName": None
                    }

                    if 'Tags' in instance:
                        for tag in instance['Tags']:
                            if tag['Key'] == 'aws:autoscaling:groupName':
                                asg_name = tag['Value']
                                instance_info["AutoScalingGroupName"] = asg_name
                                
                                # Launch Template 정보 가져오기
                                asg_response = asg_client.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])
                                if asg_response['AutoScalingGroups']:
                                    asg = asg_response['AutoScalingGroups'][0]
                                    if 'LaunchTemplate' in asg:
                                        instance_info["LaunchTemplateName"] = asg['LaunchTemplate']['LaunchTemplateName']
                            if tag['Key'] == 'Name':
                                instance_info["Name"] = tag['Value']
                    # ASG 및 Launch Template 정보 수집
                    if 'Tags' in instance:
                        for tag in instance['Tags']:
                            if tag['Key'] == 'aws:autoscaling:groupName':
                                asg_name = tag['Value']
                                instance_info["AutoScalingGroupName"] = asg_name
                                
                                # Launch Template 정보 가져오기
                                asg_response = asg_client.describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])
                                if asg_response['AutoScalingGroups']:
                                    asg = asg_response['AutoScalingGroups'][0]
                                    if 'LaunchTemplate' in asg:
                                        instance_info["LaunchTemplateName"] = asg['LaunchTemplate']['LaunchTemplateName']                  
                    all_ec2_info.append(instance_info)
        
        except Exception as e:
            logging.error(f"Error retrieving EC2 instances in region {region} for account ID {account_id}: {e}")
            continue

# 결과를 Excel 파일로 저장
output_file = f'hosts_ec2_{datetime.now().strftime("%Y-%m-%d-%H-%M")}.csv'
df = pd.DataFrame(all_ec2_info)
df.to_excel(output_file, index=False, engine='openpyxl')
logging.info(f"{'Output file created' if not df.empty else 'Empty output file created'}: {output_file}")
