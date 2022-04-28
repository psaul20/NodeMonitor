from cmath import e
import requests
import base64
import json
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
    'nodes_online': None,
    'tokens_earned_last_day': None,
    'node_requests_last_day': None,
    'current_token_price_USD': None,
    'tokens_earned_last_day_USD': None,
    'tokens_earned_this_month_USD': None,
    'tokens_earned_total': None,
    'tokens_earned_total_USD': None,
    'timestamp_central_time': None
}


def node_monitor(event, context):
    print("This Function was triggered by messageId {} published at {} to {}"
          .format(context.event_id, context.timestamp, context.resource["name"]))

    if 'data' in event:
        timeTrigger = base64.b64decode(event['data']).decode('utf-8')
        if timeTrigger == 'daily_5pm':
            # Iterate through desired APIs and call associated functions to retrieve data
            for nodeMonitor in nodeMonitorList:
                apiDataName = f"{nodeMonitor['title']}_API_Data.json"
                monitorDataName = f"{nodeMonitor['title']}_Monitor_Data.json"
                # Populate initial values from node API call
                monitorData = funcDict[nodeMonitor['token']](
                    nodeMonitor['api_key'], apiDataName, monitorDataName, nodeMonitor['start_date'])
                monitorData['timestamp_central_time'] = dt.datetime.now(
                    tz=timezone('US/Central'))

                # Populate remaining values based on price information
                tknPrice = get_Price(nodeMonitor['token'])
                monitorData['current_token_price_USD'] = tknPrice
                monitorData['tokens_earned_last_day_USD'] = tknPrice * \
                    monitorData['tokens_earned_last_day']
                monitorData['tokens_earned_this_month_USD'] = tknPrice * \
                    monitorData['tokens_earned_this_month']
                monitorData['tokens_earned_total_USD'] = tknPrice * \
                    monitorData['tokens_earned_total']

                # Send data to message manager
                send_Sms(nodeMonitor, monitorData, timeTrigger)
                # Save data into cloud storage
                save_Data(monitorData, monitorDataName)


def get_PRE_Node_Data(apiKey: str, apiDataName: str, monitorDataName: str, startDate: dt.datetime) -> dict:
    # Get data from beginning, incremented from last data pull - pass kwargs
    lastDataStruct = check_Storage(monitorDataName)
    
    # Check storage to see if API data has been gathered in the last hour (avoids API rate limits)
    dailyStoredData = check_Storage(
        apiDataName.replace(".json", "_Daily.json"), 1)
    if dailyStoredData is not False:
        dailyResponseData = dailyStoredData
    else:
        # Get daily data - default call
        dailyResponseData = call_PRE_API(apiKey)
        # Save raw API Data for retrieval later if needed
        save_Data(dailyResponseData, apiDataName.replace(
            ".json", "_Daily.json"))

    # Get data from beginning - incremented from last pull
    # First, check if incremental data pulled in last hour
    beginStoredDataIncr = check_Storage(
        apiDataName.replace(".json", "_Begin_Incr.json"), 1)
    if beginStoredDataIncr is not False:
        beginResponseData = beginStoredDataIncr
    # Otherwise, call API
    else:
        if lastDataStruct is not False:
            beginResponseData = call_PRE_API(
                apiKey, apiFlags={'start_date': lastDataStruct['timestamp_central_time']})
        else:
            beginResponseData = call_PRE_API(
                apiKey, apiFlags={'start_date': startDate})
        save_Data(beginResponseData, apiDataName.replace(
            ".json", "_Begin_Incr.json"))

    monthStoredData = check_Storage(
        apiDataName.replace(".json", "_Month.json"), 1)
    if monthStoredData is not False:
        monthResponseData = monthStoredData
    # Otherwise, call API
    else:
        # Get data from beginning of the month - pass kwargs
        firstDayOfMonth = dt.datetime.today().replace(day=1)
        monthResponseData = call_PRE_API(
            apiKey, apiFlags={'start_date': firstDayOfMonth})
        save_Data(monthResponseData, apiDataName.replace(
            ".json", "_Month.json"))

    # Populate monitor data points
    returnData = monitorDataStruct.copy()
    returnData['nodes_total'] = dailyResponseData['nodes_returned']

    # Count nodes online, sum node requests and tokens earned - Daily
    nodesOnlineCount = 0
    nodeRequestDaily = 0
    tokenEarnedDaily = 0.0

    for node, data in dailyResponseData['nodes'].items():
        if data['status']['connected'] is True and data['status']['blocked'] is False:
            nodesOnlineCount += 1
        nodeRequestDaily += data['period']['total_requests']
        tokenEarnedDaily += data['period']['total_pre_earned']
    returnData['nodes_online'] = nodesOnlineCount
    returnData['node_requests_last_day'] = nodeRequestDaily
    returnData['tokens_earned_last_day'] = tokenEarnedDaily

    # Increment tokens earned since beginning
    if lastDataStruct is not False:
        tokenEarnedTotal = lastDataStruct['tokens_earned_total']
    else:
        tokenEarnedTotal = 0.0

    for node, data in beginResponseData['nodes'].items():
        tokenEarnedTotal += data['period']['total_pre_earned']
    returnData['tokens_earned_total'] = tokenEarnedTotal

    # Count tokens earned since beginning of month
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

    print("File {} uploaded to {}.".format(f"/tmp/{fileName}", fileName))


def call_PRE_API(apiKey: str, **apiFlags):
    parameters = {
        'stats': 'true'
    }
    if apiFlags:
        for key, value in apiFlags['apiFlags'].items():
            parameters[key] = value

    print("Calling Presearch API")
    response = requests.get(f"https://nodes.presearch.org/api/nodes/status/{apiKey}",
                            params=parameters)
    responseData = response.json()

    return responseData


def check_Storage(fileName: str, hrLimit: float = 0.0):
    bucketName = os.getenv("STORAGE_BUCKET_NAME")
    getBlob = False

    # Check to see if file has been uploaded within the given time limit
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucketName)
    blobs = storage_client.list_blobs(bucketName)

    # Standardize to UTC for comparison
    utcTz = pytz.timezone('UTC')
    now = dt.datetime.now().astimezone(utcTz)

    for blob in blobs:
        if hrLimit == 0.0:
            if blob.name == fileName:
                getBlob = True
        else:
            blobtime = blob.updated.astimezone(utcTz)
            if blob.name == fileName and blobtime < now and blobtime > (now - dt.timedelta(hours=hrLimit)):
                getBlob = True

    # If uploaded within time limit, download to local in memory storage
    if getBlob is True:
        blob = bucket.blob(fileName)
        blob.download_to_filename(f"/tmp/{fileName}")
        with open(f'/tmp/{fileName}', 'r') as j:
            storedData = json.load(j)

        return storedData
    else:
        return False


def send_Sms(nodeMonitor: dict, data: dict, timeTrigger: str):
    project_id = os.getenv('GCP_PROJECT_ID')
    topic_id = "send-sms"

    publisher = pubsub.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)

    if timeTrigger == 'daily_5pm':
        message = f"{nodeMonitor['owner']}'s {nodeMonitor['token']} Daily Update:" + \
            f"\r\nNodes Online:             {str(data['nodes_online'])}/{str(data['nodes_total'])}" + \
            f"\r\nNode Requests:          {str(data['node_requests_last_day'])}" + \
            "\r\nPRE Price Today:        ${:.2f}".format(data['current_token_price_USD']) + \
            "\r\n{} Earned Today:     {:.4f}".format(nodeMonitor['token'], data['tokens_earned_last_day']) + \
            "\r\n$ Earned Today:         ${:.2f}".format(data['tokens_earned_last_day_USD']) + \
            "\r\n{} Earned This Month:  {:.4f}".format(nodeMonitor['token'], data['tokens_earned_this_month']) + \
            "\r\n$ Earned This Month:    ${:.2f}".format(data['tokens_earned_this_month_USD']) + \
            "\r\nTotal {} Earned:       {:.2f}".format(nodeMonitor['token'], data['tokens_earned_total']) + \
            "\r\nTotal $ Earned:            ${:.2f}".format(data['tokens_earned_total_USD']) + \
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
        except e:
            print("Error Message: {}".format(e))
            return 0.0
    else:
        print("Response Status {} Message: {}".format(
            response.status, response.read()))
        return 0.0


funcDict = {
    'PRE': get_PRE_Node_Data
}
