import requests
import datetime as dt
import os

parameters = {
        'stats' : 'true',
        'start_date' : dt.datetime(2022,1,13,15,8)
    }

response = requests.get(f"https://nodes.presearch.org/api/nodes/status/{os.getenv('PATRICK_PRE_API_KEY')}",
        params = parameters)
responseData = response.json()
print(responseData)