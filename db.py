"""
db.py
-----
MongoDB connection. Fails fast with a clear message if MongoDB is not running.
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import logging

logger = logging.getLogger(__name__)

MONGODB_URI = "mongodb://localhost:27017"
DB_NAME = "ai_job_assistant"

try:
    _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=3000)
    # Force a connection check immediately
    _client.admin.command("ping")
    logger.info("✅ Connected to MongoDB successfully")
except ConnectionFailure:
    logger.error("❌ Could not connect to MongoDB. Is it running on port 27017?")
    raise

_db = _client[DB_NAME]

jobs_collection  = _db["jobs"]
users_collection = _db["users"]
