import hashlib

class Inventory:
    def __init__(self):
        self.perkmap = {}
        self.itemhashes = {}

    def addItem(self, item):
        if item.hash in self.itemhashes:
            self.itemhashes[item.hash].append(item)
            return
        else:
            self.itemhashes[item.hash] = [ item ]

        for perk in item.getPerks():
            if (perk not in self.perkmap):
                self.perkmap[perk] = []
            self.perkmap[perk].append(item)

    def getDupes(self):
        dupes = []
        for items in self.itemhashes.values():
            if len(items) > 1:
                dupes.append(items)
        return dupes

    def getUniques(self):
        uniques = {}
        for perk in self.perkmap.keys():
            if len(self.perkmap[perk]) == 1:
                uniques[perk] = self.perkmap[perk][0]
        return uniques

class InventoryItem:
    def __init__(self, name, char, type, perklist):
        self.name = name
        self.char = char
        self.type = type
        self.perks = {}
        for perk in perklist:
            self.perks[perk] = True
        self.computeHash()

    def getPerks(self):
        return self.perks.keys()

    def addPerk(self, perk):
        self.perks[perk] = True
        self.computeHash()

    def removePerk(self, perk):
        if perk in self.perks:
            del(perks[perk])
            self.computeHash()

    def computeHash(self):
        sortedPerks = sorted(self.perks.keys())
        md5 = hashlib.md5()
        for perk in sortedPerks:
            md5.update(perk.encode('utf8'))
        self.hash = md5.hexdigest()
