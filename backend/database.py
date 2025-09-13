import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("Missing MONGO_URI environment variable")

# MongoDB setup
client = MongoClient(MONGO_URI)
db = client.jabba_trader

# Collections
users_collection = db.users
option_chain_collection = db.option_chain
metrics_collection = db.metrics
