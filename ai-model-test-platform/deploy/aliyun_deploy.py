#!/usr/bin/env python3
"""
阿里云ECS云助手部署脚本
通过阿里云OpenAPI调用云助手在目标实例上执行命令
"""

import json
import sys
import time

try:
    from aliyunsdkcore.client import AcsClient
    from aliyunsdkecs.request.v20140526.DescribeInstancesRequest import DescribeInstancesRequest
    from aliyunsdkecs.request.v20140526.RunCommandRequest import RunCommandRequest
    from aliyunsdkecs.request.v20140526.DescribeInvocationResultsRequest import DescribeInvocationResultsRequest
except ImportError:
    print("请先安装阿里云SDK: pip install aliyun-python-sdk-core aliyun-python-sdk-ecs")
    sys.exit(1)


# 阿里云配置 - 需要用户提供AccessKey
ACCESS_KEY_ID = ""  # 需要填写
ACCESS_KEY_SECRET = ""  # 需要填写
REGION_ID = "cn-hangzhou"  # 根据实际情况修改区域
INSTANCE_IP = "47.112.170.125"


def get_instance_id(client, ip):
    """根据公网IP查询实例ID"""
    request = DescribeInstancesRequest()
    request.set_accept_format('json')
    request.set_PageSize(100)

    response = client.do_action_with_exception(request)
    data = json.loads(response)

    for instance in data.get('Instances', {}).get('Instance', []):
        public_ip = instance.get('PublicIpAddress', {}).get('IpAddress', [])
        eip = instance.get('EipAddress', {}).get('IpAddress', '')
        if ip in public_ip or ip == eip:
            return instance['InstanceId']
    return None


def run_command(client, instance_id, command, timeout=600):
    """通过云助手执行命令"""
    request = RunCommandRequest()
    request.set_accept_format('json')
    request.set_InstanceIds([instance_id])
    request.set_CommandContent(command)
    request.set_Type("RunShellScript")  # Linux脚本
    request.set_Timeout(str(timeout))
    request.set_WorkingDir("/root")

    response = client.do_action_with_exception(request)
    data = json.loads(response)
    return data.get('InvokeId')


def get_command_result(client, invoke_id, instance_id):
    """获取命令执行结果"""
    request = DescribeInvocationResultsRequest()
    request.set_accept_format('json')
    request.set_InstanceId(instance_id)
    request.set_InvokeId(invoke_id)

    # 轮询等待结果
    for _ in range(60):  # 最多等待5分钟
        response = client.do_action_with_exception(request)
        data = json.loads(response)

        results = data.get('Invocation', {}).get('InvocationResults', {}).get('InvocationResult', [])
        if results:
            result = results[0]
            output = result.get('Output', '')
            exit_code = result.get('ExitCode', -1)
            status = result.get('InvocationStatus', '')

            if status in ['Success', 'Failed', 'Stopped']:
                return {
                    'status': status,
                    'exit_code': exit_code,
                    'output': output
                }

        time.sleep(5)

    return {'status': 'Timeout', 'exit_code': -1, 'output': ''}


def main():
    if not ACCESS_KEY_ID or not ACCESS_KEY_SECRET:
        print("错误: 请先在脚本中填写阿里云AccessKey ID和Secret")
        print("获取方式: 阿里云控制台 -> 右上角头像 -> AccessKey管理")
        sys.exit(1)

    client = AcsClient(ACCESS_KEY_ID, ACCESS_KEY_SECRET, REGION_ID)

    print(f"正在查询实例ID (IP: {INSTANCE_IP})...")
    instance_id = get_instance_id(client, INSTANCE_IP)

    if not instance_id:
        print(f"错误: 未找到IP为 {INSTANCE_IP} 的ECS实例")
        sys.exit(1)

    print(f"找到实例ID: {instance_id}")

    # 部署命令
    deploy_command = """
set -e
echo "开始部署AI模型测试平台..."

# 安装Docker
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi

# 安装Docker Compose
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

echo "Docker和Docker Compose已安装"
docker --version
docker-compose --version

# 创建项目目录
mkdir -p /opt/ai-model-test-platform
echo "项目目录已创建"

echo "部署环境准备完成，请上传项目代码后执行 deploy.sh"
"""

    print("正在通过云助手执行部署命令...")
    invoke_id = run_command(client, instance_id, deploy_command)
    print(f"命令已发送，InvokeId: {invoke_id}")

    print("等待命令执行完成...")
    result = get_command_result(client, invoke_id, instance_id)

    print(f"\n执行状态: {result['status']}")
    print(f"退出码: {result['exit_code']}")
    print(f"输出:\n{result['output']}")


if __name__ == '__main__':
    main()
