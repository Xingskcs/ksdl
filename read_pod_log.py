import kubernetes
from kubernetes import client, config
from kubernetes.client.rest import ApiException


def read_pod_log(namespace, pod_name):
    """Read pod log depends on namespace and pod name. 

    :param namespace: namespace of pod.
    :pod_name: the name of pod.
    :return: int
                 the training global step.
    """
    config.load_kube_config()
    configuration = kubernetes.client.Configuration()
    configuration.api_key['authorization'] = 'eyJhbGciOiJSUzI1NiIsImtpZCI6IiJ9.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlLXN5c3RlbSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJhZG1pbi11c2VyLXRva2VuLWNydnM5Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQubmFtZSI6ImFkbWluLXVzZXIiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC51aWQiOiJhZDlhZjRmYy1kYjg2LTExZTgtYTYxYS0wMDBhZjc5YmZmOTAiLCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6a3ViZS1zeXN0ZW06YWRtaW4tdXNlciJ9.MJFsXqqXQqFvFBMYsoOv75CnbFDql4IA_trWPN87Qci9Kjv1Nksn6F1Upryp9jTd3NmUBWAewnCPxHt2mkahWsMdAlbn1_KxtPPng21SxP41DwSYN46J-zlU4CKtquDVjQ6EYVPqNc_mRSgAg6D63BXg6yB18MaM5zMI9DJHzngko0qJh3UIOmGy6MsEYTgO4eoHX1r_fI0CommWDCKfjITQEqWxjn1ezHgsqFn0NsN13s2Y3PR3PYn_-SMTVFy6C_ShONM3NEAysxVAc32Q8WTYektVe5Pq_le0utoBQkSzXfBrN7CjyHNShy1siqI6SyKuJVb6vouHVT8wbaBbQw'
    configuration.api_key_prefix['authorization'] = 'Bearer'

    api_instance = kubernetes.client.CoreV1Api(kubernetes.client.ApiClient(configuration))
    name = pod_name 
    namespace = namespace
    pretty = 'true'
    tail_lines = 1
    timestamps = True

    try: 
        api_response = api_instance.read_namespaced_pod_log(name, namespace, pretty=pretty, tail_lines=tail_lines, timestamps = timestamps)
        # Return traning global step
        if api_response.find('Global step') == -1:
            return -1
        return int(api_response[api_response.find('Global step')+12:api_response.find('Local step')-1])
    except ApiException as e:
        print("Exception when calling CoreV1Api->read_namespaced_pod_log: %s\n" % e)