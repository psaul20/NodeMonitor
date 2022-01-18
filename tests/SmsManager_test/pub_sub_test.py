from google.cloud import pubsub
import os
import base64

project_id = os.getenv('GCP_PROJECT_ID')
topic_id = "send-sms"

publisher = pubsub.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_id)

data = 'This is a\r\nNew Line Test'
# Data must be a bytestring
data = data.encode('utf-8')
print(data)

publisher.publish(
    topic_path, data
)

print(f"Published message {data} to {topic_path}.")