import json
import requests
import datetime as dt
from google.cloud import storage

apiDataStruct = {
    'nodes_total': None,
    'nodes_online' : None,
    'node_requests' : None,
    'tokens_earned_total' : None
}

# fileName = "PRE_API_Response_Data.json"
# bucketName = "node_monitor_bucket"
# getBlob = False

# storage_client = storage.Client()
# bucket = storage_client.bucket(bucketName)
# blobs = storage_client.list_blobs(bucket_name)
# for blob in blobs:
#     if blob.name == fileName and blob.updated < dt.datetime.now():
#         getBlob = True

# if getBlob == True:
#     blob.download_to_filename(f"tmp/{fileName})

# else:
#     parameters = {
#             'stats' : 'true'
#         }

#     response = requests.get(f"https://nodes.presearch.org/api/nodes/status/LAHNgTM8pJPW3fb8or1F6Kj15zKGc0",
#             params = parameters)
#     responseData = response.json()

with open('/Users/patricksaul/Documents/Projects/Python Projects/NodeMonitor/tests/NodeMonitor_test/apidata.json', 'r') as j:
     responseData = json.load(j)
    #  print(responseData)
     
returnData = apiDataStruct.copy()
returnData['nodes_total'] = responseData['nodes_returned']

#stuck on nested dictionary extraction

nodesOnlineCount = 0
nodeRequestTotal = 0
tokenEarnedTotal = 0.0

for node, data in responseData['nodes'].items():
    print(data)
    if data['status']['connected'] == True and data['status']['blocked'] == False:
        nodesOnlineCount += 1
    nodeRequestTotal += data['period']['total_requests']
    tokenEarnedTotal += data['period']['total_pre_earned']

returnData['nodes_online'] = nodesOnlineCount
returnData['node_requests'] = nodeRequestTotal
returnData['tokens_earned_total'] = tokenEarnedTotal
    
print(returnData)

assert responseData["success"] == True