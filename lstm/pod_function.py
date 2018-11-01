import time

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
    """
    finish = False
    while True:
        if finish:
            break
        try: 
            for i in range(32):
                api_response = api_instance.read_namespaced_pod_status("lstm-worker-{index}".format(index=i), namespace)
                if api_response.status.phase == "Succeeded":
                    finish = True
                    break
                time.sleep(1)
        except:
            pass
    print("Job Completed. Total time(seconds): " + str(time.time() - job_submit_time))


def get_cpu_memory_usage(api_instance, namespace):
    """Get cpus and memory used in a namespace. 

    :return: (int, float, float)
                 the pod number.
                 the cpus used, the unit is m.
                 the mem used, the unit is G.
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
            mem_sum += float(mem_str[:mem_str.find('G')])
        return (pod_number, cpus_sum, mem_sum)
    except ApiException as e:
        print("Exception when calling CoreV1Api->list_pod_for_all_namespaces: %s\n" % e)
