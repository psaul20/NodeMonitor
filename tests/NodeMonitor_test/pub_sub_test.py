from google.cloud import pubsub_v1
import os
import base64

project_id = os.getenv('GCP_PROJECT_ID')
topic_id = "time-trigger"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_id)

data = 'daily_5pm'
# Data must be a bytestring
data = data.encode('utf-8')
data = base64.b64encode(data)
print(data)

publisher.publish(
    topic_path, data
)

print(f"Publised message {data} to {topic_path}.")