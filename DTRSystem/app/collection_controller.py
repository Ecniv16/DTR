import pymongo


client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["Monitoring"]


def print_collection():

    collection_list = []
    for collection in list(db.collection_names()):
        dict_list = {
            'collection': collection,
            'count': db[collection].count()
        }
        collection_list.append(dict_list)

    return(collection_list)


def drop_collections(collection):
    db[collection].drop()
