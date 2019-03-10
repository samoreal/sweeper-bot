import csv, re, json, argparse
from inventoryitem import Inventory, InventoryItem
from bungieapi import BungieApi

if __name__ == '__main__':
    main()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('csv', help = 'the file exported from DIM containing your armor')
    args = parser.parse_args()
    do_cli_diff(args.csv)

def do_cli_diff(dim_file):
    perk_re = re.compile('perks\s+\d+', re.IGNORECASE)
    value_re = re.compile('(tier\s+\d+armor)|(mod)$', re.IGNORECASE)

    buckets = {}
    with open(dim_file) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            perks = []
            for k, v in row.items():
                if (perk_re.match(k) and not value_re.match(v)):
                    perks.append(v.replace("*", ""))

            newItem = InventoryItem("{} ({})".format(row['Name'], row['Id']),
                                    row['Equippable'], row['Type'], perks)
            try:
                charBuckets = buckets[newItem.char]
            except KeyError:
                print("Creating {} bucket".format(newItem.char))
                charBuckets = {}
                buckets[newItem.char] = charBuckets

            try:
                inventory = charBuckets[newItem.type]
            except KeyError:
                print("Creating {} sub-bucket".format(newItem.type))
                inventory = Inventory()
                charBuckets[newItem.type] = inventory

            inventory.addItem(newItem)


    for char in buckets.keys():
        for type in buckets[char].keys():
            print("----------")
            print("{} for {}".format(type, char))
            print("----------")
            dupelist = buckets[char][type].getDupes()
            uniquedict = buckets[char][type].getUniques()
            for equivalent in dupelist:
                print('Identical inventory items: ', end='')
                print(', '.join([item.name for item in equivalent]))
            for perk in uniquedict.keys():
                print("{} is the only such item with the {} perk.".format(uniquedict[perk].name, perk))

    #with open('./assets/dump.json', 'wt') as fp:
        #json.dump(buckets, fp, indent=2)

def old_main():
    bapi = BungieApi()
    manifest = bapi.getManifest()
    if (bapi.shouldUpdateAssetDatabase(manifest)):
        bapi.getAssetDatabase(manifest)
