import torch

from src import config
from src.adapter.qdrant import QdrantAdapter
from src.repository.product import ProductRepository
from src.utils.encoder import TextEncoder

from src.model.products import ListProductPoint


class Search:
    """
    Provides search functionality for finding products similar to a query text.

    This class initializes the required adapters and repositories and provides a
    method to search for products by encoding a text query into a vector and applying
    optional filters.

    Attributes:
        qdrant_adapter (QdrantAdapter): Adapter for interacting with the Qdrant vector database.
        product_repository (ProductRepository): Repository for managing product-related operations.
    """
    def __init__(self) -> None:
        """
        Initializes the Search service.

        Sets up the Qdrant adapter and product repository required for executing similarity searches.
        """
        self.qdrant_adapter: QdrantAdapter = QdrantAdapter()
        self.product_repository: ProductRepository = ProductRepository(self.qdrant_adapter)

    def find_similar(self, text: str, filters: list[dict[str, any]] = None) -> ListProductPoint:
        """
        Finds products similar to the given query text using vector similarity.

        This method encodes the input text into a vector representation using a pre-trained
        text encoder (e.g., CLIP) and performs a similarity search in the Qdrant database.
        Optional filters can be applied to narrow down the results.

        Args:
            text (str): The query text for which similar products need to be searched.
            filters (list[dict[str, any]], optional): A list of filter dictionaries defining
                conditions to apply to the search results. Defaults to None.

        Returns:
            ListProductPoint: A Pydantic model containing a list of product points matching
                              the query and filters.

        Raises:
            Exception: If an error occurs during text encoding or the search process.

        Example:
            search_service = Search()
            filters = [{"field": "price", "operation": "gte", "value": 50.0}]
            results = search_service.find_similar("Men's black sneakers", filters=filters)
        """
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
        model_name: str = config.CLIP_MODEL_NAME
        text_encoder: TextEncoder = TextEncoder(model_name=model_name, device=device)
        encoded_text: torch.Tensor = text_encoder.encode(text)
        result = self.product_repository.find_similar(encoded_text, filters)
        return result