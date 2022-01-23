from google.cloud import pubsub
import os
import base64
import json

project_id = os.getenv('GCP_PROJECT_ID')
topic_id = "send-sms"

publisher = pubsub.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_id)

messages = json.dumps([
    {
        "message": "This is a Test Message for Patrick on Telegram and SMS",
        "comm_recipient": "Patrick",
        "comm_methods": ["telegram", "gmail"]
    },
    # {
    #     "message": "This is a Test Message for Patrick and Amanda on Telegram and SMS",
    #     "comm_recipient": "Patrick and Amanda",
    #     "comm_methods": ["telegram", "gmail"]
    # },
    # {
    #     "message": "This is a Test Message for Patrick on SMS",
    #     "comm_recipient": "Patrick",
    #     "comm_methods": ["gmail"]
    # }
    ])
    
messages = messages.encode('utf-8')

publisher.publish(
    topic_path, messages
)

print(f"Published message data {messages} to {topic_path}.")