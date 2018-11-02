import os
import time

import pod_function

# Global variables
total_steps = 10000 # the number of training steps
min_predict_step = 200 # predict after completing min_predict_step mini batches.
worker_number = 1
scale_time = 0
scale_delay = 10 # traning begins after 10s when submit job.
load_data_delay = 2 # take 2 seconds to load traning data to memory


def submit_job():
    """Submit job."""
    os.system("python render_template.py distributed-lstm.jinja | kubectl create -f - -n distributed-lstm")
    global scale_time
    scale_time = time.time()


def delete_job():
    """Delete job."""
    os.system("python render_template.py distributed-lstm.jinja | kubectl delete -f - -n distributed-lstm --grace-period=0 --force")


def scale_worker():
    """Scale workers."""
    global worker_number
    change_worker_cmd = "sed -i 's/{{%- set worker_replicas = {number1} -%}}/{{%- set worker_replicas = {number2} -%}}/g' distributed-lstm.jinja".format(
        number1=worker_number, number2=worker_number*2)
    worker_number = worker_number*2
    os.system(change_worker_cmd)
    submit_job()


def qos_guarantee(api_instance, qos_time):
    """According to the log of the pod, predict the completion time of 
    the job, compare it with qos, and scale the number of pods horizontally."""
    global worker_number
    worker_number = 1
    namespace = "distributed-lstm"
    pod_name = "lstm-worker-0"
    forecast_reach_qos = False
    # Submit a lstm job
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
                if global_step != -1 and global_step >= min_predict_step:
                    used_time = time.time() - scale_time - scale_delay - load_data_delay
                    break
            except:
                # Cannot read global step when init.
                pass
            time.sleep(0.5)
        # Predict job completion time.
        forecast_complete_time = scale_time + scale_delay + load_data_delay + (used_time/global_step/1.2)*total_steps
        print("Prediction completion time: " + str(forecast_complete_time))
        print("QoS time: " + str(job_submit_time + qos_time))
        print("Difference between prediction and qos: " + str(forecast_complete_time - job_submit_time - qos_time))
        if forecast_complete_time <= job_submit_time + qos_time:
            forecast_reach_qos = True
        else:
            # Delete previous job
            delete_job()
            # Scale the workers
            scale_worker()
    print("Scale Done! Wait Job Finish!")
    return pod_function.wait_job_finish(api_instance, namespace, pod_name, job_submit_time)
