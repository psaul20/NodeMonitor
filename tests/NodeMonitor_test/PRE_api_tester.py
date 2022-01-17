import requests

def call_PRE_API(apiKey: str, time):
    parameters = {
            'stats' : 'true',
            ''
        }

    response = requests.get(f"https://nodes.presearch.org/api/nodes/status/{apiKey}",
            params = parameters)
    responseData = response.json()
    
    return responseData