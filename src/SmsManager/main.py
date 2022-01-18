import smtplib
import os
import base64

def sms_Manager(event, context):
    
    print("This Function was triggered by messageId {} published at {} to {}"
                .format(context.event_id, context.timestamp, context.resource["name"]))
    print(f"Data from message: {str(event['data'])}")
    
    if 'data' in event:
        message = base64.b64decode(event['data']['message']).decode('utf-8')
    
        # Authenticate gmail using app password
        auth = (os.getenv("PATRICK_GMAIL_USERNAME"), os.getenv("PATRICK_GMAIL_PASSWORD"))

        phoneList = list(os.getenv('PHONE_NUMBER_REGISTRY').split(','))

        # Establish a secure session with gmail's outgoing SMTP server using your gmail account
        server = smtplib.SMTP( "smtp.gmail.com", 587 )
        server.starttls()
        server.login(auth[0], auth[1])
        
        for phone in phoneList:
                # Send text message through SMS gateway of destination number
            server.sendmail( auth[0], phone, message)
            print(f"Message Sent to {phone}")
    else:
        print("Data not found")