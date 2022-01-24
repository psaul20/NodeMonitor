import base64
import datetime as dt
import mock
import src.SmsManager.main as main
import json

mock_context = mock.Mock()
mock_context.event_id = '123456'
mock_context.timestamp = dt.datetime.now()
mock_context.resource = {
    'name': 'projects/my-project/topics/my-topic',
    'service': 'pubsub.googleapis.com',
    'type': 'type.googleapis.com/google.pubsub.v1.PubsubMessage',
}

def test_Sms_Manager():
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
        {
            "message": "This is a Test Message for Daniel on SMS",
            "comm_recipient": "Daniel",
            "comm_methods": ["gmail"]
        }
        ])
    
    messages = base64.b64encode(messages.encode('utf-8'))
    pubMessage = {
        "data": messages
    }
    
    main.sms_Manager(pubMessage, mock_context)
    
if __name__ == "__main__":
    test_Sms_Manager()
    