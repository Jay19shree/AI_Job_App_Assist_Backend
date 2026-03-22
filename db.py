import os
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

logger = logging.getLogger(__name__)

# Read directly from environment variable — no fallback to localhost
MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME = os.environ.get("MONGODB_DB_NAME", "ai_job_assistant")

if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI environment variable is not set!")

try:
    _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    _client.admin.command("ping")
    logger.info("✅ Connected to MongoDB successfully")
except ConnectionFailure as e:
    logger.error("❌ Could not connect to MongoDB: %s", e)
    raise

_db = _client[DB_NAME]

jobs_collection  = _db["jobs"]
users_collection = _db["users"]