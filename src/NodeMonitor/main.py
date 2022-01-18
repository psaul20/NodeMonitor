import requests
import base64
import json
import requests
import datetime as dt
import os
import pytz
from pytz import timezone
from google.cloud import storage
from google.cloud import pubsub

apiDict = {
    ('PRE','Patrick'): os.getenv('PATRICK_PRE_API_KEY')
}

monitorDataStruct = {
    'nodes_total': None,
    'nodes_online' : None,
    'tokens_earned_last_day' : None,
    'node_requests_last_day' : None,
    'current_token_price_USD' : None,
    'tokens_earned_last_day_USD' : None,
    'timestamp_central_time': None
}

def node_monitor(event, context):
    # """Background Cloud Function to be triggered by Pub/Sub events.
    # Args:
    #      event (dict):  The dictionary with data specific to this type of
    #                     event. The `@type` field maps to
    #                      `type.googleapis.com/google.pubsub.v1.PubsubMessage`.
    #                     The `data` field maps to the PubsubMessage data
    #                     in a base64-encoded string. The `attributes` field maps
    #                     to the PubsubMessage attributes if any is present.
    #      context (google.cloud.functions.Context): Metadata of triggering event
    #                     including `event_id` which maps to the PubsubMessage
    #                     messageId, `timestamp` which maps to the PubsubMessage
    #                     publishTime, `event_type` which maps to
    #                     `google.pubsub.topic.publish`, and `resource` which is
    #                     a dictionary that describes the service API endpoint
    #                     pubsub.googleapis.com, the triggering topic's name, and
    #                     the triggering event type
    #                     `type.googleapis.com/google.pubsub.v1.PubsubMessage`.
    # Returns:
    #     None. The output is written to Cloud Logging.

    print("This Function was triggered by messageId {} published at {} to {}"
                .format(context.event_id, context.timestamp, context.resource["name"]))

    if 'data' in event:
        time_trigger = base64.b64decode(event['data']).decode('utf-8')
        if time_trigger == 'daily_5pm':
            # Iterate through desired APIs and call associated functions to retrieve data
            for apiLabels, apiKey in apiDict.items():
                apiDataName = f"{apiLabels[0]}_{apiLabels[1]}_API_Data.json"
                monitorData = funcDict[apiLabels[0]](apiKey, apiDataName)
                monitorData['timestamp_central_time'] = dt.datetime.now(tz= timezone('US/Central'))
                monitorData['current_token_price_USD'] = 0 # To be incorporated later
                monitorData['tokens_earned_last_day_USD'] = monitorData['current_token_price_USD'] * monitorData['tokens_earned_last_day']
                # Send data to message manager
                send_Sms(apiLabels, monitorData, time_trigger)
                # Save data into cloud storage
                monitorDataName = f"{apiLabels[0]}_{apiLabels[1]}_Monitor_Data.json"
                save_Data(monitorData, monitorDataName)

def get_PRE_Data(apiKey: str, apiDataName: str) -> dict:
    # First, check storage to see if API data has been gathered in the last hour (avoids API rate limits)
    storedData = check_Storage(apiDataName, 1)
    if storedData != False:
        responseData = storedData
    
    # Otherwise, call API
    else:
        responseData = call_PRE_API(apiKey)
        # Save raw API Data for retrieval later if needed
        save_Data(responseData, apiDataName)
    
    # Populate monitor data points
    returnData = monitorDataStruct.copy()
    returnData['nodes_total'] = responseData['nodes_returned']

    nodesOnlineCount = 0
    nodeRequestTotal = 0
    tokenEarnedTotal = 0.0

    # Count nodes online, sum node requests and tokens earned
    for node, data in responseData['nodes'].items():
        if data['status']['connected'] == True and data['status']['blocked'] == False:
            nodesOnlineCount += 1
        nodeRequestTotal += data['period']['total_requests']
        tokenEarnedTotal += data['period']['total_pre_earned']
    returnData['nodes_online'] = nodesOnlineCount
    returnData['node_requests_last_day'] = nodeRequestTotal
    returnData['tokens_earned_last_day'] = tokenEarnedTotal
    
    return returnData
    
def save_Data(data, fileName):
    bucketName = os.getenv("STORAGE_BUCKET_NAME")
    
    with open(f"/tmp/{fileName}", 'w') as j:
        json.dump(data, j, default=str)
        
    # """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucketName)
    blob = bucket.blob(fileName)

    blob.upload_from_filename(f"/tmp/{fileName}")

    print("File {} uploaded to {}.".format(
            f"/tmp/{fileName}", fileName
        )
    )

def call_PRE_API(apiKey: str):
    parameters = {
            'stats' : 'true'
        }

    print("Calling Presearch API")
    response = requests.get(f"https://nodes.presearch.org/api/nodes/status/{apiKey}",
            params = parameters)
    responseData = response.json()
    
    return responseData

def check_Storage(fileName: str, hrLimit: float):
    bucketName = os.getenv("STORAGE_BUCKET_NAME")
    getBlob = False

    #Check to see if file has been uploaded within the given time limit
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucketName)
    blobs = storage_client.list_blobs(bucketName)
    
    # Standardize to UTC for comparison
    utcTz = pytz.timezone('UTC')
    now = dt.datetime.now().astimezone(utcTz)

    for blob in blobs:
        blobtime = blob.updated.astimezone(utcTz)
        if blob.name == fileName and blobtime < now and blobtime > (now - dt.timedelta(hours=hrLimit)):
            getBlob = True
        

    # If uploaded within time limit, download to local in memory storage
    if getBlob == True:
        blob = bucket.blob(fileName)
        blob.download_to_filename(f"/tmp/{fileName}")
        with open(f'/tmp/{fileName}', 'r') as j:
            storedData = json.load(j)
        
        return storedData
    else:
        return False
    
def send_Sms(apiData : dict, data: dict, timeTrigger: str):
    project_id = os.getenv('GCP_PROJECT_ID')
    topic_id = "send-sms"

    publisher = pubsub.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)
    
    if timeTrigger == 'daily_5pm':        
        message = f"{apiData[1]}'s {apiData[0]} Daily Update:" + \
        f"\r\nNodes Online:    {str(data['nodes_online'])}/{str(data['nodes_total'])}" + \
        f"\r\nNode Requests: {str(data['node_requests_last_day'])}" + \
        "\r\n{} Earned:        {:.4f}".format(apiData[0], data['tokens_earned_last_day']) + \
        f"\r\n$ Earned:            TBD" + \
        f"\r\n\r\nGo {apiData[0]} go!!"
    
    # Data must be a bytestring
    message = message.encode('utf-8')

    publisher.publish(
        topic_path, message
    )
    
    print(f"Published message {message} to {topic_path}.")


funcDict = {
    'PRE': get_PRE_Data
}
        
        
    
    
    
    
    
    
    

    
        
    
    
    
    