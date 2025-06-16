import os


class OpenAIConfig:
    def __init__(self) -> None:
        """
        Contains:
            1. Credentials needed to estabalish connection with OpenAI API
        """
        ### Openai
        self.OPENAI_API_VERSION = "2025-03-01-preview"
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT")

        self.CHATCOMPLETION_MODEL = "gpt-4o-mini"
        self.EMBEDDING_MODEL = "text-embedding-ada-002"
        self.MAX_RETRIES = 5

        self.TEMPERATURE = 0.1


class SqlConfig:
    def __init__(self) -> None:
        """
        Contains all the configurations related to the SQLite server
        """
        # Credentials
        self.DB_PATH = "data/cyfuture.db"
        self.CONVERSATION_ANALYTICS_TABLE = "cyfuture_conversation_analytics"
        self.COMPLAINTS_TABLE = "cyfuture_complaints"
        self.USER_DETAILS_TABLE = "cyfuture_user_details"


class MilvusConfig:
    def __init__(self) -> None:
        """
        Contains all the configurations related to the Milvus server
        """
        # Credentials
        self.MILVUS_HOST = os.getenv("MILVUS_HOST")
        self.MILVUS_PORT = os.getenv("MILVUS_PORT")

        self.MILVUS_COLLECTION_NAME = "CyfutureRag"
        self.MILVUS_DB_NAME = "CyfutureRag"
        self.MILVUS_TIMEOUT = 2
        # Index parameters
        self.MILVUS_VECTOR_DIM = 1536
        self.MILVUS_INDEX_TYPE = "HNSW"
        self.MILVUS_INDEX_PARAMS = {
            "M": 16,
            "EFConstruction": 128,
        }
        self.MILVUS_DISTANCE_METRIC = "COSINE"
        self.ENGLISH_MILVUS_KNN = 5

        self.MILVUS_INDEX_NAME = "CyfutureRag_index"

        self.MILVUS_RETURN_FIELDS = ["content"]
