import smtplib
import os
import base64
import requests
import json

def sms_Manager(event, context):
    print("This Function was triggered by messageId {} published at {} to {}"
                .format(context.event_id, context.timestamp, context.resource["name"]))
    if 'data' in event:
        data = base64.b64decode(event["data"])
        data = json.loads(data)
        print(f"Data from message: {data}")

        for message in data:
            for comm_method in message['comm_methods']:
                if comm_method == 'sms':
                    # Send to gmail
                    print("Sending via Gmail")
                    send_Gmail(data)
                
                if comm_method == 'telegram':
                    # Send to Telegram
                    print("Sending via Telegram")
                    send_Telegram(data)
        else:
            print("Comm Method not found")
            
    else:
        print("Data not found")

def send_Gmail(data :dict):

    # Authenticate gmail using app password
    username = messagerConfig[data['recipient']]['gmail']['username']
    password = messagerConfig[data['recipient']]['gmail']['password']
    auth = (username, password)
    
    # Add extra lines to avoid CMAEK envelope
    message = "\r\n" + data['message']

    if messagerConfig[data['recipient']['gmail']['sms_address']] != '':
        smsAddress = messagerConfig[data['recipient']['gmail']['sms_address']]

        # Establish a secure session with gmail's outgoing SMTP server using your gmail account
        server = smtplib.SMTP( "smtp.gmail.com", 587 )
        server.starttls()
        server.login(auth[0], auth[1])

        # Send text message through SMS gateway of destination number
        server.sendmail( auth[0], smsAddress, message)
        print(f"Message Sent to {smsAddress}")
    else:
        print("No sms addresses found for {}.".format(data['recipient']))
    

def send_Telegram(data :dict): 
    bot_token = messagerConfig[data['recipient']]['telegram']['bot_token']
    bot_chatID = messagerConfig[data['recipient']]['telegram']['chat_id']
    message = data['message']
    
    if bot_token != '':
        if bot_chatID != '':
            textUrl = f'https://api.telegram.org/bot{bot_token}' + \
                f'/sendMessage?chat_id={id}' + \
                f'&parse_mode=Markdown&text={message}'
            
            print(f"Sending Telegram message to chat ID: {id}")
            response = requests.get(textUrl)
            print(f"Telegram Status Code for chat ID {id}: {response.status_code}")
        else:
            print('No chat IDs found for {}'.format(data['recipient']))
    else:
        print('No bot token found for {}'.format(data['recipient']))

messagerConfig = {
    "Patrick": {
        "gmail": {
            "username": os.getenv('PATRICK_GMAIL_USERNAME'),
            "password": os.getenv('PATRICK_GMAIL_PASSWORD'),
            "sms_address": os.getenv('PATRICK_GMAIL_SMS_ADDRESS')
        },
        "telegram": {
            "bot_token": os.getenv('TELEGRAM_BOT_TOKEN'),
            "chat_id": os.getenv('PATRICK_TELEGRAM_CHAT_ID')
        }
    },
    "Patrick & Amanda": {
        "gmail": {
            "username": os.getenv('PATRICK_GMAIL_USERNAME'),
            "password": os.getenv('PATRICK_GMAIL_PASSWORD'),
            "sms_address": os.getenv('PATRICK_AMANDA_GMAIL_SMS_ADDRESS')
        },
        "telegram": {
            "bot_token": os.getenv('TELEGRAM_BOT_TOKEN'),
            "chat_id": os.getenv('LETTERS_FROM_ALGOS_CHAT_ID')
        }
    }
}