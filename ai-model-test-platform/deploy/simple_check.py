#!/usr/bin/env python3
import json
from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526.RunCommandRequest import RunCommandRequest
from aliyunsdkecs.request.v20140526.DescribeInvocationResultsRequest import DescribeInvocationResultsRequest

client = AcsClient("ALIBABA_CLOUD_ACCESS_KEY_ID", "ALIBABA_CLOUD_ACCESS_KEY_SECRET", "cn-shenzhen")

request = RunCommandRequest()
request.set_accept_format('json')
request.set_InstanceIds(["i-wz9egw4g1k2w0ml1hoy0"])
request.set_CommandContent("echo 'Hello from ECS'; docker --version; ls /opt/ai-model-test-platform/ 2>/dev/null || echo 'No project dir'")
request.set_Type("RunShellScript")
request.set_Timeout("60")

response = client.do_action_with_exception(request)
data = json.loads(response)
invoke_id = data.get('InvokeId')
print(f"InvokeId: {invoke_id}")

import time
for _ in range(20):
    req = DescribeInvocationResultsRequest()
    req.set_accept_format('json')
    req.set_InstanceId("i-wz9egw4g1k2w0ml1hoy0")
    req.set_InvokeId(invoke_id)
    resp = client.do_action_with_exception(req)
    d = json.loads(resp)
    results = d.get('Invocation', {}).get('InvocationResults', {}).get('InvocationResult', [])
    if results:
        r = results[0]
        if r.get('InvocationStatus') in ['Success', 'Failed']:
            print(f"Status: {r['InvocationStatus']}")
            print(f"Output: {r.get('Output', '')}")
            break
    time.sleep(3)
