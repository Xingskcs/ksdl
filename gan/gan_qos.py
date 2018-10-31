import os
import time

import kubernetes
from kubernetes import client, config
from kubernetes.client.rest import ApiException

import pod_function

# Global variables
total_steps = 500000
qos_time = 8000
min_predict_step = 200
worker_number = 1
scale_time = 0

# Create k8s API instance
config.load_kube_config()
configuration = kubernetes.client.Configuration()
configuration.api_key['authorization'] = 'eyJhbGciOiJSUzI1NiIsImtpZCI6IiJ9.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlLXN5c3RlbSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJhZG1pbi11c2VyLXRva2VuLWNydnM5Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQubmFtZSI6ImFkbWluLXVzZXIiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC51aWQiOiJhZDlhZjRmYy1kYjg2LTExZTgtYTYxYS0wMDBhZjc5YmZmOTAiLCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6a3ViZS1zeXN0ZW06YWRtaW4tdXNlciJ9.MJFsXqqXQqFvFBMYsoOv75CnbFDql4IA_trWPN87Qci9Kjv1Nksn6F1Upryp9jTd3NmUBWAewnCPxHt2mkahWsMdAlbn1_KxtPPng21SxP41DwSYN46J-zlU4CKtquDVjQ6EYVPqNc_mRSgAg6D63BXg6yB18MaM5zMI9DJHzngko0qJh3UIOmGy6MsEYTgO4eoHX1r_fI0CommWDCKfjITQEqWxjn1ezHgsqFn0NsN13s2Y3PR3PYn_-SMTVFy6C_ShONM3NEAysxVAc32Q8WTYektVe5Pq_le0utoBQkSzXfBrN7CjyHNShy1siqI6SyKuJVb6vouHVT8wbaBbQw'
configuration.api_key_prefix['authorization'] = 'Bearer'
api_instance = kubernetes.client.CoreV1Api(kubernetes.client.ApiClient(configuration))


def submit_job():
    """Submit job."""
    os.system("python render_template.py distributed-gan.jinja | kubectl create -f - -n distributed-gan")
    global scale_time
    scale_time = time.time()


def delete_job():
    """Delete job."""
    os.system("python render_template.py distributed-gan.jinja | kubectl delete -f - -n distributed-gan --grace-period=0 --force")


def scale_worker():
    """Scale workers"""
    global worker_number
    change_worker_cmd = "sed -i 's/{{%- set worker_replicas = {number1} -%}}/{{%- set worker_replicas = {number2} -%}}/g' distributed-gan.jinja".format(
        number1=worker_number, number2=worker_number*2)
    worker_number = worker_number*2
    os.system(change_worker_cmd)
    submit_job()


def main():
    """According to the log of the pod, predict the completion time of
    the job, compare it with qos, and scale the number of pods horizontally."""
    namespace = "distributed-gan"
    pod_name = "gan-worker-0"
    forecast_reach_qos = False
    # Submit a gan job
    submit_job()
    # Record the submit time
    job_submit_time = time.time()
    while not forecast_reach_qos:
        # Read global step
        global_step = 0
        used_time = 0
        while True:
            try:
                global_step = pod_function.read_global_step(api_instance, namespace, pod_name)
                print(global_step)
                if global_step != -1 and global_step >= min_predict_step:
                    used_time = time.time() - scale_time
                    break
            except:
                # Cannot read global step when init.
                pass
            time.sleep(1)
        # Predict job completion time.
        forecast_complete_time = scale_time + (used_time/global_step)*total_steps
        print("Prediction completion time: " + str(forecast_complete_time))
        print("QoS time: " + str(job_submit_time + qos_time))
        if forecast_complete_time <= job_submit_time + qos_time:
            forecast_reach_qos = True
        else:
            # Delete previous job
            delete_job()
            # Scale the workers
            scale_worker()
    pod_function.wait_job_finish(api_instance, namespace, pod_name, job_submit_time)


if __name__ == "__main__":
    main()