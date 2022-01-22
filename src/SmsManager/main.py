import smtplib
import os
import base64
import requests
import json

def sms_Manager(event, context):
    
    print("This Function was triggered by messageId {} published at {} to {}"
                .format(context.event_id, context.timestamp, context.resource["name"]))
    if 'data' in event:
        message = str(base64.b64decode(event['data']).decode('utf-8'))
        print(f"Data from message: {message}")

        # Send to gmail
        print("Sending via Gmail")
        send_Gmail(message)
        
        # Send to Telegram
        print("Sending via Telegram")
        send_Telegram(message)
            
    else:
        print("Data not found")

def send_Gmail(message: str):
    # Add extra lines to avoid CMAEK envelope
    message = "\r\n" + message
    # Authenticate gmail using app password
    auth = (os.getenv("PATRICK_GMAIL_USERNAME"), os.getenv("PATRICK_GMAIL_PASSWORD"))

    if os.getenv('EMAIL_PHONE_NUMBER_REGISTRY') is not None:
        emailPhoneList = list(os.getenv('EMAIL_PHONE_NUMBER_REGISTRY').split(','))

        # Establish a secure session with gmail's outgoing SMTP server using your gmail account
        server = smtplib.SMTP( "smtp.gmail.com", 587 )
        server.starttls()
        server.login(auth[0], auth[1])
        
        for phone in emailPhoneList:
            # Send text message through SMS gateway of destination number
            server.sendmail( auth[0], phone, message)
            print(f"Message Sent to {phone}")
    

def send_Telegram(message: str):
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    bot_chatIDs = list(os.getenv('TELEGRAM_CHAT_IDS').split(','))
    
    for id in bot_chatIDs:
        textUrl = f'https://api.telegram.org/bot{bot_token}' + \
            f'/sendMessage?chat_id={id}' + \
            f'&parse_mode=Markdown&text={message}'
        
        print(f"Sending Telegram message to chat ID: {id}")
        response = requests.get(textUrl)
        print(f"Telegram Status Code for chat ID {id}: {response.status_code}")