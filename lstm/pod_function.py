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
    timestamps = True

    try: 
        api_response = api_instance.read_namespaced_pod_log(pod_name, namespace, pretty=pretty, tail_lines=tail_lines, timestamps = timestamps)
        # Return traning global step
        if api_response.find('Global step') == -1:
            return -1
        return int(api_response[api_response.find('Global step')+12:api_response.find('Local step')-1])
    except ApiException as e:
        print("Exception when calling CoreV1Api->read_namespaced_pod_log: %s\n" % e)


def wait_job_finish(api_instance, namespace, pod_name, job_submit_time):
    """Wait pod finish and print total time. 

    :api_instance: k8s API instance.
    :param namespace: namespace of pod.
    :pod_name: the name of pod.
    :job_submit_time: the submit time of job.
    """
    try:
        while True: 
            api_response = api_instance.read_namespaced_pod_status(pod_name, namespace)
            if api_response.status.phase == "Succeeded":
                break
        print("Job Completed. Total time(seconds): " + str(time.time() - job_submit_time))
    except ApiException as e:
        print("Exception when calling CoreV1Api->read_namespaced_pod_status: %s\n" % e)
