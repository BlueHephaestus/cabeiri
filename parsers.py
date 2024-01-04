# Description: Contains helper functions for parsing data
from datetime import datetime

def items_recursive(dic):
    for key, val in dic.items():
        if type(val) is dict:
            for ikey, ival in items_recursive(val):
                yield ikey, ival
        else:
            yield key, val


def flatten_dict(dic):
    # return 1-d dict from multidimensional dict
    return {k: v for k, v in items_recursive(dic)}

to_human_timestamp = lambda timestamp: datetime.fromtimestamp(timestamp / 1000).strftime('%b %d, %I:%M%p')

class TripletStore:
    def __init__(self):
        self.map1 = {}
        self.map2 = {}
        self.map3 = {}

    def insert(self, item1, item2, item3):
        self.map1[item1] = (item2, item3)
        self.map2[item2] = (item1, item3)
        self.map3[item3] = (item1, item2)

    def get(self, item):
        if item in self.map1:
            return self.map1[item]
        if item in self.map2:
            return self.map2[item]
        if item in self.map3:
            return self.map3[item]
        return None