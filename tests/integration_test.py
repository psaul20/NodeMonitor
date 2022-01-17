import base64
import os
import subprocess
import uuid

import requests
from urllib3.util import Retry

def test_daily_node_monitor():
    time_trigger = 'daily_5pm'
    port = 8088  # Each running framework instance needs a unique port

    encoded_trigger = base64.b64encode(time_trigger.encode('utf-8')).decode('utf-8')
    pubsub_message = {
        'data': encoded_trigger
    }

    process = subprocess.Popen(
      [
        'functions-framework',
        '--target', 'node_monitor',
        '--signature-type', 'event',
        '--port', str(port)
      ],
      cwd=os.path.dirname(__file__),
      stdout=subprocess.PIPE
    )

    # Send HTTP request simulating Pub/Sub message
    # (GCF translates Pub/Sub messages to HTTP requests internally)
    url = f'http://localhost:{port}/'

    retry_policy = Retry(total=6, backoff_factor=1)
    retry_adapter = requests.adapters.HTTPAdapter(
      max_retries=retry_policy)

    session = requests.Session()
    session.mount(url, retry_adapter)

    response = session.post(url, json=pubsub_message)

    assert response.status_code == 200

    # Stop the functions framework process
    process.kill()
    process.wait()
    out, err = process.communicate()

    print(out, err, response.content)

    assert f'nodes_total'in str(out)