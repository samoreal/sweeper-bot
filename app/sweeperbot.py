import json, requests, zipfile, io, sqlite3
from inventoryitem import Inventory, InventoryItem
from bungieapi import BungieApi

if __name__ == '__main__':
    main()

def main():
    bapi = BungieApi()
    manifest = bapi.getManifest()
    if (bapi.shouldUpdateAssetDatabase(manifest)):
        bapi.getAssetDatabase(manifest)


def old_main():
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
