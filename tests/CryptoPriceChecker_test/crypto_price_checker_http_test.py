import datetime as dt
import requests
from flask import request

def test_Crypto_Price_Checker():

    url = 'http://localhost:8080'
    data = {'symbol': 'PRE'}
    
    print("Sending request to {}.".format(url))
    response = requests.post(url, json= data)
    data = response.content
    print("Content returned: {}".format(data))
    
    return float(data)
    
if __name__ == "__main__":
    price = test_Crypto_Price_Checker()
    assert price > 0 and price < 10000
