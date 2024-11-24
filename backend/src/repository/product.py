from src import config
from src.adapter.qdrant import QdrantAdapter
from src.model.products import ListProductPoint, ProductPoint


class ProductRepository:
    def __init__(self, qdrant_adapter: QdrantAdapter) -> None:
        """
        Initializes the ProductRepository with a QdrantAdapter instance.

        Args:
            qdrant_adapter (QdrantAdapter): An adapter for interacting with the Qdrant vector database.
        """
        self.config = config
        self.qdrant_adapter = qdrant_adapter

    def create_collection_if_not_exists(self, name: str, vector_size: int) -> None:
        """
        Creates a Qdrant collection if it does not already exist.

        Args:
            name (str): The name of the collection to create.
            vector_size (int): The size of the vectors to be stored in the collection.
        """
        self.qdrant_adapter.create_collection_if_not_exists(name, vector_size)

    def batch_insert(self, collection_name: str, data: list[ProductPoint]) -> None:
        """
              Inserts or updates a batch of product data points into the specified Qdrant collection.

              Args:
                  collection_name (str): The name of the collection where data points will be inserted.
                  data (list[ProductPoint]): A list of ProductPoint objects to be upserted.
        """
        self.qdrant_adapter.batch_upsert(collection_name, data)

    def find_similar(self, text: list[float], filters: list[dict[str, any]] = None) -> ListProductPoint:
        """
        Searches for similar products in the Qdrant collection based on a query vector and optional filters.

        Args:
                   text (list[float]): The query vector used for similarity search.
                   filters (list[dict[str, any]], optional): A list of filter conditions to refine the search results.
                       Each filter should include 'field', 'operation', and 'value'.

        Returns:
                   ListProductPoint: A list of ProductPoint objects representing the search results.
        """
        return self.qdrant_adapter.find_similar(text, filters)