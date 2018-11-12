import os
import time
import math

import pod_function

# Global variables
total_steps = 30000 # the number of training steps
min_predict_step = 300 # predict after completing min_predict_step mini batches.
worker_number = 1
scale_time = 0
scale_delay = 10 # traning begins after 10s when submit job.
load_data_delay = 2 # take 2 seconds to load traning data to memory
max_worker_number = 32
ps_cpu = 2000


def submit_job():
    """Submit job."""
    os.system("python render_template.py distributed-encoder.jinja | kubectl create -f - -n distributed-encoder")
    global scale_time
    scale_time = time.time()


def delete_job():
    """Delete job."""
    os.system("python render_template.py distributed-encoder.jinja | kubectl delete -f - -n distributed-encoder --grace-period=0 --force")


def scale_ps_vertically(new_ps_cpu):
    """Scale ps."""
    global ps_cpu
    if new_ps_cpu != ps_cpu:
        print("Change ps cpus to: " + str(new_ps_cpu))
        ps_cpu = new_ps_cpu
        # Change ps cpus
        rm_cpu_request = "sed -i '63d' distributed-encoder.jinja"
        os.system(rm_cpu_request)
        modify_cpu_request = """sed -i '62a \        cpu: "{cpu}m"' distributed-encoder.jinja""".format(cpu=ps_cpu)
        os.system(modify_cpu_request)
        rm_cpu_limit = "sed -i '66d' distributed-encoder.jinja"
        os.system(rm_cpu_limit)
        modify_cpu_limit = """sed -i '65a \        cpu: "{cpu}m"' distributed-encoder.jinja""".format(cpu=ps_cpu)
        os.system(modify_cpu_limit)


def scale_worker():
    """Scale workers."""
    global worker_number
    change_worker_cmd = "sed -i 's/{{%- set worker_replicas = {number1} -%}}/{{%- set worker_replicas = {number2} -%}}/g' distributed-encoder.jinja".format(
                        number1=worker_number, number2=worker_number*2)
    worker_number = worker_number*2
    os.system(change_worker_cmd)
    submit_job()


def scale_workerII(predict_training_time, job_submit_time, qos_time):
    """Scale workers smartly."""
    global worker_number
    predict_scale_time = time.time()
    scale_worker_number = math.ceil((worker_number*predict_training_time)/(job_submit_time+qos_time-predict_scale_time-scale_delay-load_data_delay))
    change_worker_cmd = "sed -i 's/{{%- set worker_replicas = {number1} -%}}/{{%- set worker_replicas = {number2} -%}}/g' distributed-encoder.jinja".format(
                        number1=worker_number, number2=scale_worker_number)
    worker_number = scale_worker_number
    os.system(change_worker_cmd)
    # Change ps resources
    if worker_number > 7:
        scale_ps_vertically(4000)
    submit_job()


def qos_guarantee(api_instance, qos_time):
    """According to the log of the pod, predict the completion time of 
    the job, compare it with qos, and scale the number of pods horizontally."""
    global worker_number
    worker_number = 1
    global ps_cpu
    ps_cpu = 2000
    namespace = "distributed-encoder"
    pod_name = "encoder-worker-0"
    forecast_reach_qos = False
    # Submit a lstm job
    submit_job()
    # Record the submit time
    job_submit_time = time.time()
    threshold = 1.1
    if qos_time < 1120:
        threshold = 1.1
    else:
        threshold = 1.8
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
        forecast_complete_time = scale_time + scale_delay + load_data_delay + (used_time/global_step/threshold)*total_steps
        print("Prediction completion time: " + str(forecast_complete_time))
        print("QoS time: " + str(job_submit_time + qos_time))
        print("Difference between prediction and qos: " + str(forecast_complete_time - job_submit_time - qos_time))
        if forecast_complete_time <= job_submit_time + qos_time or worker_number >= max_worker_number:
            forecast_reach_qos = True
        else:
            # Delete job
            delete_job()
            # Scale the workers
            scale_workerII((used_time/global_step/threshold)*total_steps, job_submit_time, qos_time)
    print("Scale Done! Wait Job Finish!")
    return pod_function.wait_job_finish(api_instance, namespace, pod_name, job_submit_time)