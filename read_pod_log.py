from __future__ import print_function
import time
import kubernetes
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from pprint import pprint

config.load_kube_config()

# Configure API key authorization: BearerToken
configuration = kubernetes.client.Configuration()
configuration.api_key['authorization'] = 'eyJhbGciOiJSUzI1NiIsImtpZCI6IiJ9.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlLXN5c3RlbSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJhZG1pbi11c2VyLXRva2VuLWNydnM5Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQubmFtZSI6ImFkbWluLXVzZXIiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC51aWQiOiJhZDlhZjRmYy1kYjg2LTExZTgtYTYxYS0wMDBhZjc5YmZmOTAiLCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6a3ViZS1zeXN0ZW06YWRtaW4tdXNlciJ9.MJFsXqqXQqFvFBMYsoOv75CnbFDql4IA_trWPN87Qci9Kjv1Nksn6F1Upryp9jTd3NmUBWAewnCPxHt2mkahWsMdAlbn1_KxtPPng21SxP41DwSYN46J-zlU4CKtquDVjQ6EYVPqNc_mRSgAg6D63BXg6yB18MaM5zMI9DJHzngko0qJh3UIOmGy6MsEYTgO4eoHX1r_fI0CommWDCKfjITQEqWxjn1ezHgsqFn0NsN13s2Y3PR3PYn_-SMTVFy6C_ShONM3NEAysxVAc32Q8WTYektVe5Pq_le0utoBQkSzXfBrN7CjyHNShy1siqI6SyKuJVb6vouHVT8wbaBbQw'
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
configuration.api_key_prefix['authorization'] = 'Bearer'

# create an instance of the API class
api_instance = kubernetes.client.CoreV1Api(kubernetes.client.ApiClient(configuration))
name = 'gan-worker-0' # str | name of the Pod
namespace = 'distributed-gan' # str | object name and auth scope, such as for teams and projects
pretty = 'true' # str | If 'true', then the output is pretty printed. (optional)
tail_lines = 1 # int | If set, the number of lines from the end of the logs to show. If not specified, logs are shown from the creation of the container or sinceSeconds or sinceTime (optional)

try: 
    api_response = api_instance.read_namespaced_pod_log(name, namespace, pretty=pretty, tail_lines=tail_lines)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling CoreV1Api->read_namespaced_pod_log: %s\n" % e)