from pymongo import MongoClient
from app.config import MONGO_URI, MONGO_DB

def get_mongo_db():
    client = MongoClient(MONGO_URI)
    return client[MONGO_DB]