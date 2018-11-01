import csv
import os
import time

import kubernetes
from kubernetes import client, config

import lstm_qos
import pod_function

# Create k8s API instance
config.load_kube_config()
configuration = kubernetes.client.Configuration()
configuration.api_key['authorization'] = 'eyJhbGciOiJSUzI1NiIsImtpZCI6IiJ9.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlLXN5c3RlbSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJhZG1pbi11c2VyLXRva2VuLWNydnM5Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQubmFtZSI6ImFkbWluLXVzZXIiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC51aWQiOiJhZDlhZjRmYy1kYjg2LTExZTgtYTYxYS0wMDBhZjc5YmZmOTAiLCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6a3ViZS1zeXN0ZW06YWRtaW4tdXNlciJ9.MJFsXqqXQqFvFBMYsoOv75CnbFDql4IA_trWPN87Qci9Kjv1Nksn6F1Upryp9jTd3NmUBWAewnCPxHt2mkahWsMdAlbn1_KxtPPng21SxP41DwSYN46J-zlU4CKtquDVjQ6EYVPqNc_mRSgAg6D63BXg6yB18MaM5zMI9DJHzngko0qJh3UIOmGy6MsEYTgO4eoHX1r_fI0CommWDCKfjITQEqWxjn1ezHgsqFn0NsN13s2Y3PR3PYn_-SMTVFy6C_ShONM3NEAysxVAc32Q8WTYektVe5Pq_le0utoBQkSzXfBrN7CjyHNShy1siqI6SyKuJVb6vouHVT8wbaBbQw'
configuration.api_key_prefix['authorization'] = 'Bearer'
api_instance = kubernetes.client.CoreV1Api(kubernetes.client.ApiClient(configuration))

namespace = "distributed-lstm"

qos_test_list = [600 + 10*i for i in range(121)]
success = 0
failure = 0
cpus_sum = 0
mem_sum = 0
for qos_time in qos_test_list:
    print("qos time: " + str(qos_time))
    # Set the number of workers to 1
    os.system("rm distributed-lstm.jinja")
    os.system("cp ../distributed-lstm.jinja ./")
    start_time = time.time()
    lstm_qos.qos_guarantee(api_instance, qos_time)
    end_time = time.time()
    # Resource utilization
    pods_cpus_mem_used = pod_function.get_cpu_memory_usage(api_instance, namespace)
    cpus_sum += ((end_time-start_time)/3600)*pods_cpus_mem_used[1]
    mem_sum += ((end_time-start_time)/3600)*pods_cpus_mem_used[2]
    # Delete job
    lstm_qos.delete_job()
    if end_time - start_time <= qos_time:
        print("success")
        success += 1
    else:
        print("failure")
        failure += 1
    with open("exp_result.csv", 'a', newline='') as csvfile:
        writer = csv.writer(csvfile, dialect='excel')
        writer.writerow([qos_time, end_time - start_time, pods_cpus_mem_used[0], pods_cpus_mem_used[1], pods_cpus_mem_used[2]])
    time.sleep(30)
with open("exp_result.csv", 'a', newline='') as csvfile:
    writer = csv.writer(csvfile, dialect='excel')
    writer.writerow([cpus_sum, mem_sum, success/(success + failure)])
