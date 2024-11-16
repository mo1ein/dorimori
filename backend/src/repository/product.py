from src import config
from src.adapter.qdrant import QdrantAdapter
from src.model.products import ListProductPoint, ProductPoint


class ProductRepository:
    def __init__(self, qdrant_adapter: QdrantAdapter) -> None:
        self.config = config
        self.qdrant_adapter = qdrant_adapter

    def create_collection_if_not_exists(self, name: str, vector_size: int) -> None:
        self.qdrant_adapter.create_collection_if_not_exists(name, vector_size)

    def batch_insert(self, collection_name: str, data: list[ProductPoint]) -> None:
        self.qdrant_adapter.batch_upsert(collection_name, data)

    def find_similar(self, collection_name:str, text: list[float]) -> ListProductPoint:
        return self.qdrant_adapter.find_similar(collection_name, text)