from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import os
import base64
import datetime as dt
from flask_api import status
from flask import request
from dotenv import load_dotenv

# TODO: Figure out how to make it an HTTP request function
def crypto_Price_Checker(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
    # Only needed for testing
    load_dotenv()
    
    request_json = request.get_json(silent=True)
    request_args = request.args
    print("Request JSON: {}".format(request_json))

    if request_json and 'symbol' in request_json:
        symbol = request_json['symbol']
        print("Received symbol {} at {}".format(symbol, dt.datetime.now()))
        if 'api_key' in request_json:
            return get_Price(symbol, request_json['api_key'])
        else:
            return get_Price(symbol)
        
    if request_args and 'symbol' in request_args:
        symbol = request_args['symbol']
        print("Received symbol {} at {}".format(symbol, dt.datetime.now()))
        if 'api_key' in request_args:
            return get_Price(symbol, request_args['api_key'])
        else:
            return get_Price(symbol)
        
    else:
        print("Symbol not found.")
        return status.HTTP_400_BAD_REQUEST, "Symbol not found."

def get_Price(symbol :str, apiKey=os.getenv('COINMARKETCAP_API_KEY')):
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    parameters = {
    'symbol': symbol,
    }

    headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': apiKey
    }
    
    session = Session()
    session.headers.update(headers)

    try:
        print("Calling Coin Market Cap API")
        response = session.get(url, params=parameters)
        statusString = "API call status: {} - {}".format(response.status_code,response.reason)
        # Error handling
        if response.status_code == 400:
            return status.HTTP_400_BAD_REQUEST, statusString
        data = json.loads(response.text)
        print(data)
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)
    
    print("Price data: {}".format(data['data'][symbol]['quote']['USD']['price']))
    
    return str(data['data'][symbol]['quote']['USD']['price'])
    
