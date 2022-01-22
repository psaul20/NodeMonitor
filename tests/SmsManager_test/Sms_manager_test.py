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
    messages = str([{
            "message": "This is a Test Message for Patrick on Telegram & SMS",
            "recipient": "Patrick",
            "comm_methods": ["telegram", "gmail"]
        },
        {
            "message": "This is a Test Message for Patrick & Amanda on Telegram & SMS",
            "recipient": "Patrick",
            "comm_methods": ["telegram", "gmail"]
        },
        {
            "message": "This is a Test Message for Patrick on SMS",
            "recipient": "Patrick",
            "comm_methods": ["gmail"]
        }])
    
    messages = base64.b64encode(messages.encode('utf-8')).decode('utf-8')
    pubMessage = {
        "data": messages
    }
    
    main.sms_Manager(pubMessage, mock_context)
    
if __name__ == "__main__":
    test_Sms_Manager()
    