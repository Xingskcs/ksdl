import os
import time
import math

import pod_function

# Global variables
total_steps = 100000
min_predict_step = 500
worker_number = 1
scale_time = 0
scale_delay = 8 # training begins after 8s when submit job.
load_data_delay = 1.6 # take 1.6s to load training data to memory
max_worker_number = 32
ps_cpu = 2000
ps_number = 1


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


def scale_ps_horizontally():
    global ps_number
    change_ps_cmd = "sed -i 's/{{%- set ps_replicas = {number1} -%}}/{{%- set ps_replicas = {number2} -%}}/g' distributed-gan.jinja".format(
        number1=ps_number, number2=ps_number*2)
    ps_number = ps_number*2
    os.system(change_ps_cmd)


def scale_ps_vertically(new_ps_cpu):
    """Scale ps."""
    global ps_cpu
    if new_ps_cpu != ps_cpu:
        print("Change ps cpus to: " + str(new_ps_cpu))
        ps_cpu = new_ps_cpu
        # Change ps cpus
        rm_cpu_request = "sed -i '63d' distributed-gan.jinja"
        os.system(rm_cpu_request)
        modify_cpu_request = """sed -i '62a \        cpu: "{cpu}m"' distributed-gan.jinja""".format(cpu=ps_cpu)
        os.system(modify_cpu_request)
        rm_cpu_limit = "sed -i '66d' distributed-gan.jinja"
        os.system(rm_cpu_limit)
        modify_cpu_limit = """sed -i '65a \        cpu: "{cpu}m"' distributed-gan.jinja""".format(cpu=ps_cpu)
        os.system(modify_cpu_limit)
          

def scale_ps_workerII(job_submit_time, qos_time):
    """Scale ps or worker smartly."""
    delete_job()
    global worker_number
    predict_scale_time = time.time()
    # Reduce threshold
    # reduce_threshold = 1
    # scale_worker_number = math.ceil((reduce_threshold*worker_number*predict_training_time)/(job_submit_time+qos_time-predict_scale_time-scale_delay-load_data_delay))
    scale_worker_number = math.ceil((5000)/(job_submit_time+qos_time-predict_scale_time))
    change_worker_cmd = "sed -i 's/{{%- set worker_replicas = {number1} -%}}/{{%- set worker_replicas = {number2} -%}}/g' distributed-gan.jinja".format(
                        number1=worker_number, number2=scale_worker_number)
    worker_number = scale_worker_number
    os.system(change_worker_cmd)
    # Change ps resources
    # if worker_number > 4 and worker_number <= 8:
    #     scale_ps_vertically(4000)
    # elif worker_number > 8 and worker_number <= 14:
    #     scale_ps_vertically(6000)
    # elif worker_number > 14:
    #     scale_ps_vertically(8000)
    if worker_number > 4 and worker_number <= 7:
        scale_ps_vertically(4000)
    elif worker_number > 7 and worker_number <= 10:
        scale_ps_vertically(6000)
    elif worker_number > 10:
        scale_ps_vertically(8000)
    submit_job()



def qos_guarantee(api_instance, qos_time):
    """According to the log of the pod, predict the completion time of
    the job, compare it with qos, and scale the number of pods horizontally."""
    global worker_number
    worker_number = 1
    global ps_cpu
    ps_cpu = 2000
    namespace = "distributed-gan"
    pod_name = "gan-worker-0"
    forecast_reach_qos = False
    # Submit a gan job
    submit_job()
    # Record the submit time
    job_submit_time = time.time()
    while not forecast_reach_qos:
        # Predict job completion time.
        forecast_complete_time = scale_time + 5000/worker_number
        print("Prediction completion time: " + str(forecast_complete_time))
        print("QoS time: " + str(job_submit_time + qos_time))
        print("Difference between prediction and qos: " + str(forecast_complete_time - job_submit_time - qos_time))
        if forecast_complete_time <= job_submit_time + qos_time or worker_number >= max_worker_number:
            forecast_reach_qos = True
        else:
            # Scale the workers
            scale_ps_workerII(job_submit_time, qos_time)
    print("Scale Done! Wait Job Finish!")
    return pod_function.wait_job_finish(api_instance, namespace, pod_name, job_submit_time)