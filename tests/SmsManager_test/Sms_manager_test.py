import base64
import datetime as dt
import mock
import src.SmsManager.main as main

mock_context = mock.Mock()
mock_context.event_id = '123456'
mock_context.timestamp = dt.datetime.now()
mock_context.resource = {
    'name': 'projects/my-project/topics/my-topic',
    'service': 'pubsub.googleapis.com',
    'type': 'type.googleapis.com/google.pubsub.v1.PubsubMessage',
}

def test_Sms_Manager():
    message = 'This is a Test Message'
    message = base64.b64encode(message.encode('utf-8')).decode('utf-8')
    pubMessage = {
        'topic' : 'fake_topic',
        'data':{ 
            'message': message
            }
    }
    
    main.sms_Manager(pubMessage, mock_context)
    
if __name__ == "__main__":
    test_Sms_Manager()
    