import pymongo
from pprint import pprint

db = pymongo.MongoClient().sentences
col = db.MXXXXX
'''
All update tag
for c in col.find():
    tag = c['Tag']
    if type(tag) == type(""):
        splitedList = tag.split(',')
        col.update_many({'_id':c['_id']},{'$set': {'Tag':splitedList}})
'''
'''
All update layer
col.update_many({},{'$set': {'layer':'rock'}})
for c in col.find():
    pprint(c)
'''
a = list(col.aggregate([{'$match': {'layer': 'rock'}}, {'$sample': {'size': 1}}]))[0]['Contents']

pprint(a)


