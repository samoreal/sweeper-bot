import json, requests, zipfile, io, sqlite3
from inventoryitem import Inventory, InventoryItem

code = ''
access_token = ''
refresh_token = ''

bungie_id = '10253057'
ps_membership_id = '4611686018448173014'
bliz_membership_id = '4611686018468068743'
titan_char_id = '2305843009261191525'

headers = {
    'Authorization' : 'Bearer ' + access_token,
    'X-API-Key' : api_key
}

def refresh():
    params = {
        'grant_type' : 'refresh_token',
        'client_id' : client_id,
        'client_secret' : client_secret,
        'refresh_token' : refresh_token
    }

    r = requests.post(token_endpoint, data=params)
    print (json.dumps(json.loads(r.text), indent=2))

def getManifest():
    r = requests.get(base+'/Destiny2/Manifest/', headers={'X-API-Key' : api_key})
    if r.ok:
        manifest = r.json()
        version = manifest['Response']['version']
        assets = manifest['Response']['mobileWorldContentPaths']['en']

        r = requests.get('https://www.bungie.net'+assets, headers={'X-API-Key' : api_key})
        if r.ok:
            zip = zipfile.ZipFile(io.BytesIO(r.content))
            zip.extractall('./assets/manifest.db')
        else:
            print(r.request.headers)
            print(r.request.url)
    else:
        print (r.text)

def getMemberships():
    r = requests.get(base+'/User/GetMembershipsForCurrentUser/', headers=headers)
    print (json.dumps(json.loads(r.text), indent=2))

def getCharacters():
    params = { 'components' : ['100', '200'] }
    r = requests.get(base+'/Destiny2/2/Profile/'+ps_membership_id+'/', params=params, headers=headers)
    print (json.dumps(json.loads(r.text), indent=2))

def getCharacterItems():
    params = { 'components' : ['201', '205'] }
    r = requests.get(base+'/Destiny2/2/Profile/'+ps_membership_id+'/Character/'+titan_char_id+'/',
        params=params, headers=headers)
    print (json.dumps(json.loads(r.text), indent=2))

def main():
    manifest = None

    with open('helmet2.json') as f:
        manifest = json.load(f)

    perklist = manifest['perks']
    allitems = manifest['items']

    inventory = Inventory()
    for itemdata in allitems:
        perks = [ perklist[perkid] for perkid in itemdata['perks'] ]
        item = InventoryItem(itemdata['name'], *perks)
        inventory.addItem(item)

    print("")
    print("----------")
    print("Duplicate Items")
    print("----------")
    dupelist = inventory.getDupes()
    for equivalent in dupelist:
        print('Identical inventory items: ', end='')
        print(', '.join([item.name for item in equivalent]))

    print("")
    print("----------")
    print("Unique Items")
    print("----------")
    uniquedict = inventory.getUniques()
    for perk in uniquedict.keys():
        print(uniquedict[perk].name + ' is the only item with the ' + perk + ' perk.')

    print("")
    print("----------")
    print("Missing Perks")
    print("----------")
    for perk in perklist.values():
        if perk not in inventory.perkmap:
            print(perk + " not on any inventory item!")

if __name__ == '__main__':
    getManifest()
