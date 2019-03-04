import json, requests, os, glob, re, sqlite3, time
from enum import Enum

class Platform(Enum):
    XBOX = 1
    PSN = 2
    BLIZ = 4

class BungieApi:
    base_url = 'https://www.bungie.net'
    platform_url = base_url + '/platform'
    token_url = platform_url + '/app/oauth/token/'

    def __init__(self, client_id=None, client_secret=None, api_key=None, database=None):
        self.setClientId(client_id)
        self.setClientSecret(client_secret)
        self.setAPIKey(api_key)
        self.setupDatabase(database)

    def setClientId(self, client_id):
        if client_id is None:
            self.client_id = os.getenv('BUNGIE_CLIENT_ID')
        else:
            self.client_id = client_id

        if self.client_id is None:
            raise Exception('Client ID not set for this application')

    def setClientSecret(self, client_secret):
        if client_secret is None:
            self.client_secret = os.getenv('BUNGIE_CLIENT_SECRET')
        else:
            self.client_secret = client_secret

        if self.client_secret is None:
            raise Exception('Client secret not set for this application')

    def setAPIKey(self, api_key):
        if api_key is None:
            self.api_key = os.getenv('BUNGIE_API_KEY')
        else:
            self.api_key = api_key

        if self.api_key is None:
            raise Exception('API key not set for this application')

    def getDatabase(self, database=None):
        if database is None:
            database = os.path.join('assets', 'sweeperbot.db')
        return sqlite3.connect(database)

    def setupDatabase(self, database=None):
        with self.getDatabase() as conn:
            with open(os.path.join('app', 'createtables.sql'), 'rt') as fp:
                conn.cursor().executescript(fp.read())

    def getAccessToken(self, u_id):
        print("Getting access token for account {}".format(u_id))
        tokenq = "SELECT rowid, token, expiry \
                    FROM auths WHERE token_type = 'access' AND u_id = ? \
                    ORDER BY rowid DESC"

        token = None
        with self.getDatabase() as conn:
            cursor = conn.cursor()
            now = int(time.time())
            for row in cursor.execute(tokenq, (int(u_id),)):
                if row[2] > now:
                    token = row[1]
                    break

        if token is None:
            print("No valid access token, must refresh")
            refresh = self.getRefreshToken(u_id)
            auth = self.refresh(refresh)
            self.storeAuth(auth)
            token = auth['access_token']

        return token

    def getRefreshToken(self, u_id):
        print("Getting refresh token for account {}".format(u_id))
        tokenq = "SELECT rowid, token, expiry \
                    FROM auths WHERE token_type = 'refresh' AND u_id = ? \
                    ORDER BY rowid DESC"

        token = None
        with self.getDatabase() as conn:
            cursor = conn.cursor()
            now = int(time.time())
            for row in cursor.execute(tokenq, (int(u_id),)):
                if row[2] > now:
                    token = row[1]
                    break

        return token

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

    def storeAuth(self, auth):
        now = int(time.time())
        uid = int(auth['membership_id'])
        userq = "REPLACE INTO users(membership_id) VALUES(?)"
        tokenq = "INSERT INTO auths(token_type, token, expiry, u_id) VALUES(?,?,?,?)"

        print("Storing tokens for member {}".format(uid))

        tokens = [
            ('refresh', auth['refresh_token'], now + int(auth['refresh_expires_in']), uid),
            ('access', auth['access_token'], now + int(auth['expires_in']), uid)
        ]

        with self.getDatabase() as conn:
            conn.cursor().execute(userq, (uid,))
            conn.cursor().executemany(tokenq, tokens)

    ############################################################################
    # MANIFEST AND ASSET DATABASE STUFF
    ############################################################################
    def _getLatestManifestFilename(self):
        manifests = glob.glob(os.path.join('assets', 'manifest_*.json'))
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
            cachedManifestVersion = re.search(versionRe, latestManifest).group(1)
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
        with open(os.path.join("assets", filename), 'wb') as file:
            file.write(resp.content)

    ############################################################################
    # CHARACTER STUFF
    ############################################################################
    def getPlatformMembershipId(self, membership_id, platform):
        platform = Platform(int(platform))
        print("Getting {} membership id for account {}".format(platform.name, membership_id))
        userq = "SELECT xbox_membership_id, psn_membership_id, bliz_membership_id \
                 FROM users WHERE membership_id = ?"

        with self.getDatabase() as conn:
            curs = conn.cursor()
            curs.execute(userq, (int(membership_id),))
            row = curs.fetchone()

            if row is None:
                return None

            if platform == Platform.XBOX:
                return row[0]
            elif platform == Platform.PSN:
                return row[1]
            elif platform == Platform.BLIZ:
                return row[2]

    def getMemberships(self, membership_id):
        access_token = self.getAccessToken(membership_id)
        headers = {
            'Authorization' : 'Bearer ' + access_token,
            'X-API-Key' : self.api_key
        }

        print("Getting memberships with token {}".format(access_token))

        r = requests.get(
            self.platform_url+'/User/GetMembershipsForCurrentUser/',
            headers=headers
        )
        return r.json()

    def storeMemberships(self, members):
        members = members['Response']
        userq = "UPDATE users SET bungie_name = ?, psn_name = ?, \
                xbox_name = ?, bliz_name = ?, psn_membership_id = ?, \
                xbox_membership_id = ?, bliz_membership_id = ? \
                WHERE membership_id = ?"

        values = {
            'display_name' : members['bungieNetUser']['displayName'],
            'psn_name' : None,
            'xbox_name' : None,
            'bliz_name' : None,
            'psn_membership_id' : None,
            'xbox_membership_id' : None,
            'bliz_membership_id' : None,
            'membership_id' : int(members['bungieNetUser']['membershipId'])
        }

        for membership in members['destinyMemberships']:
            type = Platform(int(membership['membershipType']))
            if type == Platform.XBOX:
                values['xbox_name'] = members['bungieNetUser']['xboxDisplayName']
                values['xbox_membership_id'] = int(membership['membershipId'])
            elif type == Platform.PSN:
                values['psn_name'] = members['bungieNetUser']['psnDisplayName']
                values['psn_membership_id'] = int(membership['membershipId'])
            elif type == Platform.BLIZ:
                values['bliz_name'] = members['bungieNetUser']['blizzardDisplayName']
                values['bliz_membership_id'] = int(membership['membershipId'])

        with self.getDatabase() as conn:
            conn.execute(userq, (
                values['display_name'], values['psn_name'],
                values['xbox_name'], values['bliz_name'],
                values['psn_membership_id'], values['xbox_membership_id'],
                values['bliz_membership_id'], values['membership_id']
            ))

    def getCharacters(self, membership_id, platform):
        access_token = self.getAccessToken(membership_id)
        try:
            platform_id = self.getPlatformMembershipId(membership_id, platform)
        except ValueError as v:
            print("Could not get characters: {}".format(v))
            return {}

        headers = {
            'Authorization' : 'Bearer ' + access_token,
            'X-API-Key' : self.api_key
        }
        params = { 'components' : ['100', '200'] }

        print("Getting characters with token {}".format(access_token))

        r = requests.get(
            self.platform_url + '/Destiny2/' + platform +
                '/Profile/' + str(platform_id) + '/',
            params=params,
            headers=headers
        )

        return r.json()

    def getCharacterItems(self, membership_id, platform, character_id):
        access_token = self.getAccessToken(membership_id)
        try:
            platform_id = self.getPlatformMembershipId(membership_id, platform)
        except ValueError as v:
            print("Could not get characters items: {}".format(v))
            return {}

        headers = {
            'Authorization' : 'Bearer ' + access_token,
            'X-API-Key' : self.api_key
        }
        params = { 'components' : ['201', '205'] }

        print("Getting character items with token {}".format(access_token))

        r = requests.get(
            self.platform_url + '/Destiny2/' + platform + '/Profile/' +
                str(platform_id) + '/Character/' + character_id + '/',
            params=params,
            headers=headers
        )
        return r.json()
