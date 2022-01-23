import smtplib
import os
import base64
import requests
import json

def sms_Manager(event, context):
    print("This Function was triggered by messageId {} published at {} to {}"
                .format(context.event_id, context.timestamp, context.resource["name"]))
    if 'data' in event:
        data = str(base64.b64decode(event["data"]).decode('utf-8'))
        print(f"Data from message: {data}")
        data = json.loads(data)

        for messageData in data:
            for comm_method in messageData['comm_methods']:
                if comm_method == 'gmail':
                    # Send to gmail
                    print("Sending SMS via Gmail")
                    send_Gmail(messageData)
                
                elif comm_method == 'telegram':
                    # Send to Telegram
                    print("Sending message via Telegram")
                    send_Telegram(messageData)
                else:
                    print("Comm Method not found")
            
    else:
        print("Data not found")

def send_Gmail(messageData :dict):

    # Authenticate gmail using app password
    username = messagerConfig[messageData['comm_recipient']]['gmail']['username']
    password = messagerConfig[messageData['comm_recipient']]['gmail']['password']
    auth = (username, password)
    
    # Add extra lines to avoid CMAEK envelope
    message = "\r\n" + messageData['message']

    if messagerConfig[messageData['comm_recipient']]['gmail']['sms_address'] != '':
        smsAddress = messagerConfig[messageData['comm_recipient']]['gmail']['sms_address']

        # Establish a secure session with gmail's outgoing SMTP server using your gmail account
        server = smtplib.SMTP( "smtp.gmail.com", 587 )
        server.starttls()
        server.login(auth[0], auth[1])

        # Send text message through SMS gateway of destination number
        server.sendmail( auth[0], smsAddress, message)
        print(f"Message Sent to {smsAddress}")
    else:
        print("No sms addresses found for {}.".format(messageData['comm_recipient']))
    

def send_Telegram(messageData :dict): 
    bot_token = messagerConfig[messageData['comm_recipient']]['telegram']['bot_token']
    bot_chatID = messagerConfig[messageData['comm_recipient']]['telegram']['chat_id']
    message = messageData['message']
    
    if bot_token != '':
        if bot_chatID != '':
            textUrl = f'https://api.telegram.org/bot{bot_token}' + \
                f'/sendMessage?chat_id={bot_chatID}' + \
                f'&parse_mode=Markdown&text={message}'
            
            print(f"Sending Telegram message to chat ID: {bot_chatID}")
            response = requests.get(textUrl)
            print(f"Telegram Status Code for chat ID {bot_chatID}: {response.status_code}")
        else:
            print('No chat IDs found for {}'.format(messageData['comm_recipient']))
    else:
        print('No bot token found for {}'.format(messageData['comm_recipient']))

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
    "Patrick and Amanda": {
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