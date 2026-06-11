#!/usr/bin/env python3
import json
import sys
from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526.DescribeInstancesRequest import DescribeInstancesRequest

ACCESS_KEY_ID = "ALIBABA_CLOUD_ACCESS_KEY_ID"
ACCESS_KEY_SECRET = "ALIBABA_CLOUD_ACCESS_KEY_SECRET"
INSTANCE_IP = "47.112.170.125"

regions = [
    "cn-hangzhou", "cn-beijing", "cn-shanghai", "cn-shenzhen",
    "cn-qingdao", "cn-zhangjiakou", "cn-huhehaote", "cn-wulanchabu",
    "cn-chengdu", "cn-hongkong", "ap-southeast-1", "ap-southeast-2",
    "ap-northeast-1", "us-west-1", "us-east-1", "eu-central-1"
]

for region in regions:
    try:
        client = AcsClient(ACCESS_KEY_ID, ACCESS_KEY_SECRET, region)
        request = DescribeInstancesRequest()
        request.set_accept_format('json')
        request.set_PageSize(100)
        response = client.do_action_with_exception(request)
        data = json.loads(response)
        for instance in data.get('Instances', {}).get('Instance', []):
            public_ip = instance.get('PublicIpAddress', {}).get('IpAddress', [])
            eip = instance.get('EipAddress', {}).get('IpAddress', '')
            if INSTANCE_IP in public_ip or INSTANCE_IP == eip:
                print(f"找到实例！区域: {region}, 实例ID: {instance['InstanceId']}")
                sys.exit(0)
    except Exception as e:
        pass

print("未找到实例，请确认IP地址正确")
