from cmath import e
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
import google.auth.transport.requests
import google.oauth2.id_token
import urllib3
import certifi

nodeMonitorList = [{
    'title': 'Patrick_PRE',
    'token': 'PRE',
    'owner': 'Patrick',
    'api_key': os.getenv('PATRICK_PRE_API_KEY'),
    'comm_recipient': 'Patrick and Amanda',
    'comm_methods': ['telegram'],
    'start_date': dt.datetime(2022, 1, 13, 15, 8)
},
    {
    'title': 'Daniel_PRE',
    'token': 'PRE',
    'owner': 'Daniel',
    'api_key': os.getenv('DANIEL_PRE_API_KEY'),
    'comm_recipient': 'Daniel',
    'comm_methods': ['telegram', 'gmail'],
    'start_date': dt.datetime(2022, 1, 1, 3, 51)
}]

monitorDataStruct = {
    'nodes_total': None,
    'nodes_online' : None,
    'tokens_earned_last_day' : None,
    'node_requests_last_day' : None,
    'current_token_price_USD' : None,
    'tokens_earned_last_day_USD' : None,
    'tokens_earned_this_month_USD' : None,
    'tokens_earned_total': None,
    'tokens_earned_total_USD': None,
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
        timeTrigger = base64.b64decode(event['data']).decode('utf-8')
        if timeTrigger == 'daily_5pm':
            # Iterate through desired APIs and call associated functions to retrieve data
            for nodeMonitor in nodeMonitorList:
                apiDataName = f"{nodeMonitor['title']}_API_Data.json"
                # Populate initial values from node API call
                monitorData = funcDict[nodeMonitor['token']](nodeMonitor['api_key'], apiDataName, nodeMonitor['start_date'])
                monitorData['timestamp_central_time'] = dt.datetime.now(tz= timezone('US/Central'))
                
                # Populate remaining values based on price information                
                tknPrice = get_Price(nodeMonitor['token'])
                monitorData['current_token_price_USD'] = tknPrice
                monitorData['tokens_earned_last_day_USD'] = tknPrice * monitorData['tokens_earned_last_day']
                monitorData['tokens_earned_this_month_USD'] = tknPrice * monitorData['tokens_earned_this_month']
                monitorData['tokens_earned_total_USD'] = tknPrice * monitorData['tokens_earned_total']
                
                # Send data to message manager
                send_Sms(nodeMonitor, monitorData, timeTrigger)
                # Save data into cloud storage
                monitorDataName = f"{nodeMonitor['title']}_Monitor_Data.json"
                save_Data(monitorData, monitorDataName)

def get_PRE_Node_Data(apiKey: str, apiDataName: str, startDate: dt.datetime) -> dict:
    # Next, check storage to see if API data has been gathered in the last hour (avoids API rate limits)
    dailyStoredData = check_Storage(apiDataName.replace(".json","_Daily.json"), 1)
    if dailyStoredData != False:
        dailyResponseData = dailyStoredData
    else:
        # Get daily data - default call
        dailyResponseData = call_PRE_API(apiKey)
        # Save raw API Data for retrieval later if needed
        save_Data(dailyResponseData, apiDataName.replace(".json","_Daily.json"))
    
    beginStoredData = check_Storage(apiDataName.replace(".json","_Begin.json"), 1)
    if beginStoredData != False:
        beginResponseData = beginStoredData 
    # Otherwise, call API
    else:
        # Get data from beginning - pass kwargs
        beginResponseData = call_PRE_API(apiKey, apiFlags={'start_date':startDate})
        save_Data(beginResponseData, apiDataName.replace(".json","_Begin.json"))
    
    monthStoredData = check_Storage(apiDataName.replace(".json","_Month.json"), 1)
    if monthStoredData != False:
        monthResponseData = monthStoredData 
    # Otherwise, call API
    else:
        # Get data from beginning of the month - pass kwargs
        firstDayOfMonth = given_date.replace(day=1)
        monthResponseData = call_PRE_API(apiKey, apiFlags={'start_date':firstDayOfMonth})
        save_Data(monthResponseData, apiDataName.replace(".json","_Month.json"))

    
    # Populate monitor data points
    returnData = monitorDataStruct.copy()
    returnData['nodes_total'] = dailyResponseData['nodes_returned']
    
    # Count nodes online, sum node requests and tokens earned - Daily
    nodesOnlineCount = 0
    nodeRequestDaily = 0
    tokenEarnedDaily = 0.0

    for node, data in dailyResponseData['nodes'].items():
        if data['status']['connected'] == True and data['status']['blocked'] == False:
            nodesOnlineCount += 1
        nodeRequestDaily += data['period']['total_requests']
        tokenEarnedDaily += data['period']['total_pre_earned']
    returnData['nodes_online'] = nodesOnlineCount
    returnData['node_requests_last_day'] = nodeRequestDaily
    returnData['tokens_earned_last_day'] = tokenEarnedDaily

    # Count tokens earned since beginning    
    tokenEarnedTotal = 0.0

    for node, data in beginResponseData['nodes'].items():
        tokenEarnedTotal += data['period']['total_pre_earned']
    returnData['tokens_earned_total'] = tokenEarnedTotal
    
     # Count tokens earned since beginning    
    tokenEarnedThisMonth = 0.0

    for node, data in monthResponseData['nodes'].items():
        tokenEarnedThisMonth += data['period']['total_pre_earned']
    returnData['tokens_earned_this_month'] = tokenEarnedThisMonth
    
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

def call_PRE_API(apiKey: str, **apiFlags):
    parameters = {
            'stats' : 'true'
        }
    if apiFlags:
        for key, value in apiFlags['apiFlags'].items():
            parameters[key] = value

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
    
def send_Sms(nodeMonitor : dict, data: dict, timeTrigger: str):
    project_id = os.getenv('GCP_PROJECT_ID')
    topic_id = "send-sms"

    publisher = pubsub.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)
    
    if timeTrigger == 'daily_5pm':        
        message = f"{nodeMonitor['owner']}'s {nodeMonitor['token']} Daily Update:" + \
        f"\r\nNodes Online:          {str(data['nodes_online'])}/{str(data['nodes_total'])}" + \
        f"\r\nNode Requests:       {str(data['node_requests_last_day'])}" + \
        "\r\nPRE Price Today:     ${:.2f}".format(data['current_token_price_USD']) + \
        "\r\n{} Earned Today:  {:.4f}".format(nodeMonitor['token'], data['tokens_earned_last_day']) + \
        "\r\n$ Earned Today:       ${:.2f}".format(data['tokens_earned_last_day_USD']) + \
        "\r\n$ Earned This Month:       ${:.2f}".format(data['tokens_earned_this_month_USD']) + \
        "\r\nTotal {} Earned:    {:.2f}".format(nodeMonitor['token'], data['tokens_earned_total']) + \
        "\r\nTotal $ Earned:         ${:.2f}".format(data['tokens_earned_total_USD']) + \
        f"\r\nGo {nodeMonitor['token']} go!!"
    
    # Data must be a bytestring
    messageData = json.dumps([{
        "message": message,
        "comm_recipient": nodeMonitor['comm_recipient'],
        "comm_methods": nodeMonitor['comm_methods']
    }])
    messageData = messageData.encode('utf-8')
    
    publisher.publish(topic_path, messageData)
    
    print(f"Published message {message} to {topic_path}.")

def get_Price(symbol):
    # For testing
    # url = 'http://10.0.0.102:8080/'
    url = os.getenv('PRICE_CHECKER_URL')
    data = json.dumps({'symbol': symbol})    
    auth_req = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(auth_req, url)
    http = urllib3.PoolManager(ca_certs=certifi.where())
    
    headers = {
        "Authorization": f"Bearer {id_token}",
        'Content-Type': "application/json"
    }
        
    print("Sending price request to {}.".format(url))
    response = http.request('POST', url, headers=headers, body=data)  
    responseData = response.data.decode('utf-8')
    print("Content returned: {}".format(responseData))
    
    if response.status == 200:
        try:
            return float(responseData)
        except:
            print("Error Message: {}".format(e))
            return 0.0
    else:
        print("Response Status {} Message: {}".format(response.status, response.read()))
        return 0.0

funcDict = {
    'PRE': get_PRE_Node_Data
}
        
        
    
    
    
    
    
    
    

    
        
    
    
    
    
