import json, requests, os, glob, re

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

    ############################################################################
    # LOGIN STUFF
    ############################################################################
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

    def refresh(self, refresh_token):
        params = {
            'grant_type' : 'refresh_token',
            'client_id' : self.client_id,
            'client_secret' : self.client_secret,
            'refresh_token' : refresh_token
        }

        print ("Refreshing using refresh: {}".format(refresh_token))

        resp = requests.post(self.token_url, data=params)
        return json.loads(resp.text)

    ############################################################################
    # MANIFEST AND ASSET DATABASE STUFF
    ############################################################################
    def _getLatestManifestFilename(self):
        manifests = glob.glob(os.path.join('.', 'assets', 'manifest_*.json'))
        if len(manifests) == 0:
            return None
        manifests.sort(key=os.path.getmtime, reverse=True)
        return manifests[0]

    def _collapseVersion(self, version):
        return re.sub('\D', "", version)

    def getManifest(self):
        resp = requests.get(
            self.platform_url + '/Destiny2/Manifest/',
            headers = { 'X-API-Key' : self.api_key }
        )
        return resp.json()

    def shouldUpdateAssetDatabase(self, manifest):
        currentVersion = self._collapseVersion(manifest['Response']['version'])
        latestManifest = self._getLatestManifestFilename()

        if latestManifest is None:
            return True

        try:
            versionRe = 'manifest_([^.]+)\.json$'
            cachedManifestVersion = re.search(versionRe, latestManifest]).group(1)
            return currentVersion > cachedManifestVersion
        except AttributeError:
            print("Malformed manifest file name: {}".format(latestManifest))
            return True

    def getAssetDatabase(self, manifest):
        resp = requests.get(
            self.base_url + manifest['Response']['jsonWorldContentPaths']['en'],
            headers={ 'X-API-Key' : self.api_key }
        )

        version = self._collapseVersion(manifest['Response']['version'])
        filename = "manifest_{}.json".format(version)
        with open(os.path.join(".", "assets", filename), 'wb') as file:
            file.write(resp.content)

    ############################################################################
    # CHARACTER STUFF
    ############################################################################
    def getMemberships(self, access_token):
        headers = {
            'Authorization' : 'Bearer ' + access_token,
            'X-API-Key' : self.api_key
        }

        r = requests.get(
            base+'/User/GetMembershipsForCurrentUser/',
            headers=headers
        )
        return json.loads(r.text)

    def getCharacters(self, access_token, membership_id):
        headers = {
            'Authorization' : 'Bearer ' + access_token,
            'X-API-Key' : self.api_key
        }
        params = { 'components' : ['100', '200'] }

        r = requests.get(
            base+'/Destiny2/2/Profile/'+membership_id+'/',
            params=params,
            headers=headers
        )
        return json.loads(r.text)

    def getCharacterItems(self, access_token, membership_id, character_id):
        headers = {
            'Authorization' : 'Bearer ' + access_token,
            'X-API-Key' : self.api_key
        }
        params = { 'components' : ['201', '205'] }

        r = requests.get(
            base+'/Destiny2/2/Profile/'+membership_id+'/Character/'+character_id+'/',
            params=params,
            headers=headers
        )
        return json.loads(r.text)
