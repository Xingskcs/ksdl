import time
from sdcclient import SdcClient

from kubernetes.client.rest import ApiException


def read_global_step(api_instance, namespace, pod_name):
    """Read pod log depends on namespace and pod name. 

    :api_instance: k8s API instance.
    :param namespace: namespace of pod.
    :pod_name: the name of pod.
    :return: int
                 the training global step.
    """
    pretty = 'true'
    tail_lines = 1

    try: 
        api_response = api_instance.read_namespaced_pod_log(pod_name, namespace, pretty=pretty, tail_lines=tail_lines)
        # Return traning global step
        if api_response.find('Global step') == -1:
            return -1
        return int(api_response.split(",")[0].split(" ")[2][:-1])
    except:
        pass


def wait_job_finish(api_instance, namespace, pod_name, job_submit_time):
    """Wait pod finish and print total time. 

    :api_instance: k8s API instance.
    :param namespace: namespace of pod.
    :pod_name: the name of pod.
    :job_submit_time: the submit time of job.

    :return: (float, float, float, float)
                 the cores used max by ps.
                 the mem used max by ps, the unit is M.
                 the cores used max by worker.
                 the mem used max by worker, the unit is M.
    """
    ps_cpu_max = 0
    ps_mem_max = 0
    worker_cpu_max = 0
    worker_mem_max = 0
    finish = False
    while not finish:
        try: 
            ps_cpu_mem_usage = get_pod_cpu_memory_usage("lstm-ps-0")
            worker_cpu_mem_usage = get_pod_cpu_memory_usage("lstm-worker-0")
            if ps_cpu_mem_usage[0] > ps_cpu_max:
                ps_cpu_max = ps_cpu_mem_usage[0]
            if ps_cpu_mem_usage[1] > ps_mem_max:
                ps_mem_max = ps_cpu_mem_usage[1]
            if worker_cpu_mem_usage[0] > worker_cpu_max:
                worker_cpu_max = worker_cpu_mem_usage[0]
            if worker_cpu_mem_usage[1] > worker_mem_max:
                worker_mem_max = worker_cpu_mem_usage[1]
            for i in range(32):
                api_response = api_instance.read_namespaced_pod_status("lstm-worker-{index}".format(index=i), namespace)
                if api_response.status.phase == "Succeeded":
                    finish = True
                    break
                time.sleep(1)
        except:
            pass
    print("Job Completed. Total time(seconds): " + str(time.time() - job_submit_time))
    return (ps_cpu_max, ps_mem_max, worker_cpu_max, worker_mem_max)


def get_cpu_memory_allocation(api_instance, namespace):
    """Get cpus and memory allocated in a namespace. 

    :return: (int, float, float)
                 the pod number.
                 the cpus allocated, the unit is m.
                 the mem allocated, the unit is G.
    """
    name = namespace.split('-')[1]
    label_selector = 'name='+name
    try: 
        api_response = api_instance.list_pod_for_all_namespaces(label_selector=label_selector)
        pod_number = len(api_response.items)
        cpus_sum = 0
        mem_sum = 0
        for i in range(pod_number):
            cpus_sum += float(api_response.items[i].spec.containers[0].resources.limits['cpu'])
            mem_str = api_response.items[i].spec.containers[0].resources.limits['memory']
            if mem_str.find('G') == -1:
                mem_sum += float(mem_str[:mem_str.find('M')])/1024
            else:
                mem_sum += float(mem_str[:mem_str.find('G')])
        return (pod_number, cpus_sum, mem_sum)
    except ApiException as e:
        print("Exception when calling CoreV1Api->list_pod_for_all_namespaces: %s\n" % e)


def get_pod_cpu_memory_usage(pod_name):
    """Get cpus and memory usage in a pod. 

    :return: (float, float)
                 the cores used.
                 the mem used, the unit is M.
    """
    sdclient = SdcClient("2b9e3c0a-cee6-443a-90b5-7530682b4d71")
    pod_filter = "kubernetes.pod.name = '%s'" % pod_name
    start = -60
    end = 0
    sampling = 60
    cpus_metrics = [{ "id": "cpu.cores.used", "aggregations": { "time": "timeAvg", "group": "max" } }]
    cpus_metric_data = sdclient.get_data(cpus_metrics, start, end, sampling, filter=pod_filter)
    cpus = float(cpus_metric_data[1].get('data')[0].get('d')[0])
    mem_metrics = [{ "id": "memory.bytes.used", "aggregations": { "time": "timeAvg", "group": "max" } }]
    mem_metrics_data = sdclient.get_data(mem_metrics, start, end, sampling, filter=pod_filter)
    mem = float(mem_metrics_data[1].get('data')[0].get('d')[0])/1024/1024
    return (cpus, mem)


def get_pod_cpu_memory_limits(pod_name):
    """Get cpus and memory limits of a pod. 

    :return: (float, float)
                 the cores used.
                 the mem used, the unit is M.
    """
    sdclient = SdcClient("2b9e3c0a-cee6-443a-90b5-7530682b4d71")
    pod_filter = "kubernetes.pod.name = '%s'" % pod_name
    start = -60
    end = 0
    sampling = 60
    cpus_limit_metrics = [{"id": "kubernetes.pod.resourceLimits.cpuCores", "aggregations": { "time": "timeAvg", "group": "max" }}]
    cpus_limit_data = sdclient.get_data(cpus_limit_metrics, start, end, sampling, filter=pod_filter)
    cpus_limit = float(cpus_limit_data[1].get('data')[0].get('d')[0])
    mem_limit_metrics = [{"id": "kubernetes.pod.resourceLimits.memBytes", "aggregations": { "time": "timeAvg", "group": "max" }}]
    mem_limit_data = sdclient.get_data(mem_limit_metrics, start, end, sampling, filter=pod_filter)
    mem_limit = float(mem_limit_data[1].get('data')[0].get('d')[0])/1024/1024
    return (cpus_limit, mem_limit)