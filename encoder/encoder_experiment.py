import csv
import os
import time

import kubernetes
from kubernetes import client, config

import encoder_qos
import pod_function

# Create k8s API instance
config.load_kube_config()
configuration = kubernetes.client.Configuration()
configuration.api_key['authorization'] = 'eyJhbGciOiJSUzI1NiIsImtpZCI6IiJ9.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJkZWZhdWx0Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZWNyZXQubmFtZSI6InN5c2RpZy1hZ2VudC10b2tlbi1kcmxrOCIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50Lm5hbWUiOiJzeXNkaWctYWdlbnQiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC51aWQiOiI2YjgzMDI2Mi1kYWI3LTExZTgtYWNlMy0wMDBhZjc5YmZmOTAiLCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6ZGVmYXVsdDpzeXNkaWctYWdlbnQifQ.PEHSPHcYfuv_z0LCmiP500B12ezBGD4KXNjYk-Ij73c19x9kyumzSjPyn2KCTQD0mOlQT2Tx_x4gdN4p9PrYCtpeJwWXfnvFmvAUQNtHXWVcnkjabbUJfKoy1t6ITW3wYvqgA47OIpah-nJjE4C6OsEwC-cy6ZHf9E9KFVdojAqWBLCB949mlv-wrUhKWsrh9sSArB8XB90RwAcS35xzZwXkErfspkOHYf_G8Lvdrl7e9sETZ0KS2ghFJZJzTDiJBFukYkXSKX2yj8YCtGkwDNYXiCsEq0gqombflb0l3t7femQsRgVE9-Qm7Ad3Aj3AHZ5u9U55KDfox_gb1Ed8Jw'
configuration.api_key_prefix['authorization'] = 'Bearer'
api_instance = kubernetes.client.CoreV1Api(kubernetes.client.ApiClient(configuration))

namespace = "distributed-encoder"

qos_test_list = [600 + 40*i for i in range(31)]
success = 0
failure = 0
cpus_sum = 0
mem_sum = 0
for qos_time in qos_test_list:
    print("qos time: " + str(qos_time))
    # Set the number of workers to 1
    os.system("rm distributed-encoder.jinja")
    os.system("cp ../distributed-encoder.jinja ./")
    start_time = time.time()
    pod_resource_usage = encoder_qos.qos_guarantee(api_instance, qos_time)
    end_time = time.time()
    # Resource allocation
    pods_cpus_mem_used = pod_function.get_cpu_memory_allocation(api_instance, namespace)
    cpus_sum += ((end_time-start_time)/3600)*pods_cpus_mem_used[1]
    mem_sum += ((end_time-start_time)/3600)*pods_cpus_mem_used[2]
    # Delete job
    encoder_qos.delete_job()
    if end_time - start_time <= qos_time:
        print("success")
        success += 1
    else:
        print("failure")
        failure += 1
    with open("exp_result.csv", 'a', newline='') as csvfile:
        writer = csv.writer(csvfile, dialect='excel')
        writer.writerow([qos_time, end_time - start_time, pods_cpus_mem_used[0], pods_cpus_mem_used[1], pods_cpus_mem_used[2],
                        pod_resource_usage[0], pod_resource_usage[1], pod_resource_usage[2], pod_resource_usage[3]])
    time.sleep(30)
with open("exp_result.csv", 'a', newline='') as csvfile:
    writer = csv.writer(csvfile, dialect='excel')
    writer.writerow([cpus_sum, mem_sum, success/(success + failure)])