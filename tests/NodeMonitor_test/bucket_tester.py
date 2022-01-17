import json
import datetime as dt
from json.tool import main
import os
from google.cloud import storage
import pytz
import time

def upload_test():
    fileName = "PRE_API_Response_Data.json"
    bucketName = os.getenv("STORAGE_BUCKET_NAME")

    with open('tests/NodeMonitor_test/apidata.json', 'r') as j:
        responseData = json.load(j)
        #  print(responseData)

    with open(f'tests/NodeMonitor_test/apidataSTGTEST.json', 'w') as j:
        json.dump(responseData, j)
        
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucketName)
    blob = bucket.blob(fileName)

    blob.upload_from_filename('tests/NodeMonitor_test/apidataSTGTEST.json')

    print(
        "File {} uploaded to {}.".format(
            'tests/NodeMonitor_test/apidataSTGTEST.json', fileName
        )
    )

def check_storage_test():
    fileName = "PRE_API_Response_Data.json"
    bucketName = os.getenv("STORAGE_BUCKET_NAME")
    getBlob = False

    #Check to see if file has been uploaded in the last hour
    storage_client = storage.Client()
    blobs = storage_client.list_blobs(bucketName)
    
    utcTz = pytz.timezone('UTC')
    now = dt.datetime.now().astimezone(utcTz)

    for blob in blobs:
        blobtime = blob.updated.astimezone(utcTz)
        if blob.name == fileName and blobtime < now and blobtime > (now - dt.timedelta(hours=1)):
            getBlob = True

    if getBlob == True:
        blob.download_to_filename(f"tests/NodeMonitor_test/{fileName}")
        with open(f'tests/NodeMonitor_test/{fileName}', 'r') as j:
            storedData = json.loads(j.read())
        
        return storedData
    else:
        return False

if __name__ == "__main__":
    upload_test()
    time.sleep(secs=10)
    returned = check_storage_test()

    assert returned != False, "Upload & Download failed to Google Cloud Storage"