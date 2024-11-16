import torch

from src import config
from src.adapter.qdrant import QdrantAdapter
from src.repository.product import ProductRepository
from src.utils.encoder import TextEncoder

from src.model.products import ListProductPoint


class Search:
    def __init__(self) -> None:
        self.qdrant_adapter: QdrantAdapter = QdrantAdapter()
        self.product_repository: ProductRepository = ProductRepository(self.qdrant_adapter)

    def find_similar(self, text: str) -> ListProductPoint:
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
        model_name: str = config.CLIP_MODEL_NAME
        text_encoder: TextEncoder = TextEncoder(model_name=model_name, device=device)
        encoded_text: torch.Tensor = text_encoder.encode(text)
        result = self.product_repository.find_similar(config.DATABASE_QDRANT_COLLECTION_NAME, encoded_text)
        return result


if __name__ == "__main__":
    search = Search()
    a = search.find_similar("red tie")
    print(a)
