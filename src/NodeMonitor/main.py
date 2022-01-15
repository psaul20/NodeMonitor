import logging
import requests
import base64
import json
import requests
import datetime as dt
from google.cloud import storage

apiDict = {
    ('PRE','Patrick'): 'LAHNgTM8pJPW3fb8or1F6Kj15zKGc0'
}

apiDataStruct = {
    'NodesTotal': None,
    'NodesOnline' : None,
    'NodeRequests' : None,
    'Token Earned Total' : None
}

funcDict = {
    'PRE': get_PRE_Data
}

def node_monitor(event, context):
    """Background Cloud Function to be triggered by Pub/Sub events.
    Args:
         event (dict):  The dictionary with data specific to this type of
                        event. The `@type` field maps to
                         `type.googleapis.com/google.pubsub.v1.PubsubMessage`.
                        The `data` field maps to the PubsubMessage data
                        in a base64-encoded string. The `attributes` field maps
                        to the PubsubMessage attributes if any is present.
         context (google.cloud.functions.Context): Metadata of triggering event
                        including `event_id` which maps to the PubsubMessage
                        messageId, `timestamp` which maps to the PubsubMessage
                        publishTime, `event_type` which maps to
                        `google.pubsub.topic.publish`, and `resource` which is
                        a dictionary that describes the service API endpoint
                        pubsub.googleapis.com, the triggering topic's name, and
                        the triggering event type
                        `type.googleapis.com/google.pubsub.v1.PubsubMessage`.
    Returns:
        None. The output is written to Cloud Logging.
    """

    logging.log("""This Function was triggered by messageId {} published at {} to {}
    """.format(context.event_id, context.timestamp, context.resource["name"]))

    if 'data' in event:
        name = base64.b64decode(event['data']).decode('utf-8')
        if name == 'hourly':
            for apiLabels, apiKey in apiDict.items():
                msgData = funcDict[apiLabels[0]](api_key)
                check_Diff(msgData)
                
                
        
def get_PRE_Data(apiKey) -> dict:
    fileName = "PRE_API_Response_Data.json"
    bucketName = "node_monitor_bucket"
    getBlob = False

    #Check to see if file has been uploaded in the last hour
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucketName)
    blobs = storage_client.list_blobs(bucket_name)
    now = dt.datetime.now()
    for blob in blobs:
        if blob.name == fileName and blob.updated < dt.datetime.now() and blob.updated > dt.timedelta(hours=1):
            getBlob = True

    if getBlob == True:
        blob.download_to_filename(f"tmp/{fileName}")
        with open(f'tmp/{fileName}', 'r') as j:
            responseData = json.loads(j.read())
            print(responseData)
        returnData = json.loads()

    else:
        parameters = {
                'stats' : 'true'
            }

        response = requests.get(f"https://nodes.presearch.org/api/nodes/status/LAHNgTM8pJPW3fb8or1F6Kj15zKGc0",
                params = parameters)
        responseData = response.json()
        
        returnData = apiDataStruct.copy()
        returnData['NodesTotal'] = responseData['nodes_returned']
    
    nodesOnlineCount = 0
    nodeRequestTotal = 0
    tokenEarnedTotal = 0.0
    returnData['NodesOnline'] = nodesOnlineCount
    for node in responseData['nodes']:
        if node['meta']['status']['connected'] == "true" and node['meta']['status']['blocked'] == "false":
            nodesOnlineCount += 1
        nodeRequestTotal += node['meta']['period']['total_requests']
        tokenEarnedTotal += node['meta']['period']['total_pre_earned']
    
    return returnData

def save_Data(apiData):
    

def check_Diff(msgData):
    if
    
        
        
    
    
    
    
    
    
    

    
        
    
    
    
    