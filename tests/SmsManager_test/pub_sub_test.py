from google.cloud import pubsub_v1
import os
import base64

project_id = os.getenv('GCP_PROJECT_ID')
topic_id = "send-sms"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_id)

data = {
    'message': 'This is a Test'
}
# Data must be a bytestring
data = base64.b64encode(data['message'].encode("utf-8"))

future = publisher.publish(
    topic_path, data
)

print(f"Published messages with custom attributes to {topic_path}.")