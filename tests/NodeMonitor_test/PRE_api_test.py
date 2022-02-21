import requests
import datetime as dt
import os

parameters = {
        'stats' : 'true',
        'start_date' : dt.datetime(2022,1,1,3,51)
    }

response = requests.get(f"https://nodes.presearch.org/api/nodes/status/{os.getenv('DANIEL_PRE_API_KEY')}",
        params = parameters)
responseData = response.json()
print(responseData)