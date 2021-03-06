import os
import time
import math

import pod_function

# Global variables
total_steps = 10000 # the number of training steps
min_predict_step = 200 # predict after completing min_predict_step mini batches.
worker_number = 1
scale_time = 0
scale_delay = 10 # traning begins after 10s when submit job.
load_data_delay = 2 # take 2 seconds to load traning data to memory
max_worker_number = 32


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


def scale_ps_or_worker():
    """Judge scale ps or worker.

    :return: string
                 "ps"
                 "worker"
    """
    print ("worker")
    return "worker"
    # ps_cpu_mem_usage = pod_function.get_pod_cpu_memory_usage("lstm-ps-0")
    # ps_cpu_mem_limit = pod_function.get_pod_cpu_memory_limits("lstm-ps-0")
    # pod_resource_threshold = 0.95
    # if ps_cpu_mem_usage[0]/ps_cpu_mem_limit[0] > pod_resource_threshold or ps_cpu_mem_usage[1]/ps_cpu_mem_limit[1] > pod_resource_threshold:
    #     # Delete job
    #     delete_job()
    #     print ("ps")
    #     return "ps"
    # else:
    #     # Delete job
    #     delete_job()
    #     print ("worker")
    #     return "worker"


def scale_workerII(predict_training_time, job_submit_time, qos_time):
    """Scale workers smartly."""
    # Judge scale ps or worker.
    if scale_ps_or_worker() == "ps":
        delete_job()
        pass
    else:
        # Modify memory limit
        # worker_cpu_mem_usage = pod_function.get_pod_cpu_memory_usage("lstm-worker-0")
        # worker_cpu_mem_limit = pod_function.get_pod_cpu_memory_limits("lstm-worker-0")
        # if worker_cpu_mem_usage[1] + 100 < worker_cpu_mem_limit[1]:
        #     rm_mem_request = "sed -i '114d' distributed-lstm.jinja"
        #     os.system(rm_mem_request)
        #     modify_mem_request = """sed -i '113a \        memory: "{memory}Mi"' distributed-lstm.jinja""".format(memory=worker_cpu_mem_usage[1] + 100)
        #     os.system(modify_mem_request)
        #     rm_mem_limit = "sed -i '117d' distributed-lstm.jinja"
        #     os.system(rm_mem_limit)
        #     modify_mem_limit = """sed -i '116a \        memory: "{memory}Mi"' distributed-lstm.jinja""".format(memory=worker_cpu_mem_usage[1] + 100)
        #     os.system(modify_mem_limit)
        # Delete job
        delete_job()
        # Compute worker number
        global worker_number
        predict_scale_time = time.time()
        # 1.09 is set through many experiments
        scale_worker_number = math.ceil((1.09*worker_number*predict_training_time)/(job_submit_time+qos_time-predict_scale_time-scale_delay-load_data_delay))
        change_worker_cmd = "sed -i 's/{{%- set worker_replicas = {number1} -%}}/{{%- set worker_replicas = {number2} -%}}/g' distributed-lstm.jinja".format(
                            number1=worker_number, number2=scale_worker_number)
        worker_number = scale_worker_number
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
        if forecast_complete_time <= job_submit_time + qos_time or worker_number >= max_worker_number:
            forecast_reach_qos = True
        else:
            # Scale the workers
            scale_workerII((used_time/global_step/1.2)*total_steps, job_submit_time, qos_time)
    print("Scale Done! Wait Job Finish!")
    return pod_function.wait_job_finish(api_instance, namespace, pod_name, job_submit_time)