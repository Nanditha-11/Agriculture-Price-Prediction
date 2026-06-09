import os
from pymongo import MongoClient
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

print(f"Testing connection to: {uri.split('@')[-1] if '@' in uri else uri}")

try:
    client = MongoClient(uri)
    # The ping command is cheap and does not require auth.
    client.admin.command('ping')
    print("✅ Successfully connected to MongoDB Atlas!")
    
    # Check database and collections
    db = client['agripredict_db']
    print(f"Database: {db.name}")
    print(f"Collections: {db.list_collection_names()}")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
