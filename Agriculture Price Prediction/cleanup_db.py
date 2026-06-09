import pymongo

# Configure MongoDB connection
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client['agripredict_db']
predictions_collection = db['predictions']

# Remove 'Season' field from all documents
result = predictions_collection.update_many(
    { "Season": { "$exists": True } },
    { "$unset": { "Season": "" } }
)

print(f"Cleanup complete! Removed 'Season' from {result.modified_count} records.")
