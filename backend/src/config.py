import os
from dotenv import load_dotenv

load_dotenv()

API_HOST = os.environ.get("API_HOST")
API_PORT = int(os.environ.get("API_PORT"))

DATABASE_QDRANT_HOST = os.getenv("DATABASE_QDRANT_HOST")
DATABASE_QDRANT_PORT = os.getenv("DATABASE_QDRANT_PORT")
DATABASE_QDRANT_COLLECTION_NAME = os.getenv("DATABASE_QDRANT_COLLECTION_NAME")

CLIP_MODEL_NAME = os.getenv("CLIP_MODEL_NAME")

DATASET_PATH = os.getenv("DATASET_PATH")
CHECKPOINT_PATH = os.getenv("CHECKPOINT_PATH")

OPEN_API_KEY = os.getenv("OPENAI_API_KEY")
