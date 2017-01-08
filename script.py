import pymongo
from pprint import pprint

db = pymongo.MongoClient().sentences
col = db.string
for c in col.find():
    tag = c['Tag']
    if type(tag) == type(""):
        splitedList = tag.split(',')
        col.update_many({'_id':c['_id']},{'$set': {'Tag':splitedList}})

for c in col.find():
    pprint(c)
