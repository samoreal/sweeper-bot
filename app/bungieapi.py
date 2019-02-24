import json, requests, zipfile, io, sqlite3, os

class BungieApi:
    base_url = 'https://www.bungie.net'
    platform_url = base_url + '/platform'
    token_url = platform_url + '/app/oauth/token/'

    def __init__(self, client_id=None, client_secret=None, api_key=None):
        self.setClientId(client_id)
        self.setClientSecret(client_secret)
        self.setAPIKey(api_key)

    def setClientId(self, client_id=None):
        if client_id is None:
            self.client_id = os.getenv('BUNGIE_CLIENT_ID')
        else:
            self.client_id = client_id

        if self.client_id is None:
            raise Exception('Client ID not set for this application')

    def setClientSecret(self, client_secret=None):
        if client_secret is None:
            self.client_secret = os.getenv('BUNGIE_CLIENT_SECRET')
        else:
            self.client_secret = client_secret

        if self.client_secret is None:
            raise Exception('Client secret not set for this application')

    def setAPIKey(self, api_key=None):
        if api_key is None:
            self.api_key = os.getenv('BUNGIE_API_KEY')
        else:
            self.api_key = api_key

        if self.api_key is None:
            raise Exception('API key not set for this application')

    def authorize(self, code):
        params = {
            'grant_type' : 'authorization_code',
            'code' : code,
            'client_id' : self.client_id,
            'client_secret' : self.client_secret,
        }

        print("Authorizing using code: {}".format(code))

        resp = requests.post(self.token_url, data=params)
        return json.loads(resp.text)
