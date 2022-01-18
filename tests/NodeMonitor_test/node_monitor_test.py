import base64
import datetime as dt
import mock
import src.NodeMonitor.main as main

mock_context = mock.Mock()
mock_context.event_id = '123456'
mock_context.timestamp = dt.datetime.now()
mock_context.resource = {
    'name': 'projects/my-project/topics/my-topic',
    'service': 'pubsub.googleapis.com',
    'type': 'type.googleapis.com/google.pubsub.v1.PubsubMessage',
}

def test_node_monitor():
    time_trigger = 'daily_5pm'
    encoded_trigger = base64.b64encode(time_trigger.encode('utf-8')).decode('utf-8')
    pubsub_message = {
        'data': encoded_trigger
    }
    
    # Call tested function
    output = main.node_monitor(pubsub_message, mock_context)
    
    # main.node_monitor(pubsub_message, mock_context)
    # out, err = capsys.readouterr()
    # assert f'nodes_total' in out
    

if __name__ == "__main__":
    test_node_monitor()
    