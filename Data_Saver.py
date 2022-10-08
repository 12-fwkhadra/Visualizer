from pymongo import MongoClient
import pymongo
import json
import pandas as pd
from Data_Collector import path_finder


def connecting_to_mongo():
    # connecting python to mongodb
    CONNECTION_STRING = "mongodb+srv://fk1:mongodb22@cluster0.7mt03q2.mongodb.net/?retryWrites=true&w=majority"

    # set a client for the connection
    client = MongoClient(CONNECTION_STRING)

    # Create the database, tester is a sample name
    return client['tester']


# access the database
dbname = connecting_to_mongo()


def save_to_mongo():
    csv_path = path_finder()
    topics = pd.read_csv(fr'%s' % csv_path, names=['Topic'])
    for topic in topics['Topic']:
        collection = dbname[topic]
        requesting = []
        with open(r'%s.json' % topic) as file:
            for jsonobj in file:
                myDict = json.loads(jsonobj)
                requesting.append(pymongo.InsertOne(myDict))
        result = collection.bulk_write(requesting)

connecting_to_mongo()
save_to_mongo()
