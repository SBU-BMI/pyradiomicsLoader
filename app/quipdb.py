import random

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure


def connect(dbhost, dbport):
    dburi = "mongodb://" + dbhost + ":" + str(dbport) + "/"
    client = MongoClient(dburi)
    try:
        res = client.admin.command('ismaster')
    except ConnectionFailure:
        print("Server is not available.")
        return None
    return client


def getdb(client, dbname):
    db = client[dbname]
    return db
    
        
def getRecordCount(db,slide_id):
  slideid=str(slide_id);  
  count=db.analysis.find({"analysis.execution_id":"CNN_synthetic_n_real","image.slide":slideid}).count() ;
  if count==0:
    count=db.mark.find({"provenance.analysis.execution_id":"CNN_synthetic_n_real","provenance.image.slide":slideid}).count() ;
    
  return count; 
