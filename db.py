import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

logger = logging.getLogger(__name__)

# Import settings which properly reads from .env file
from config import get_settings
settings = get_settings()

MONGODB_URI = settings.mongodb_uri
DB_NAME = settings.mongodb_db_name

if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI is not set in .env file!")

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