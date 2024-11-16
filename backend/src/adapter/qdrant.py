from qdrant_client import QdrantClient, models
from qdrant_client.http.models import VectorParams, Distance
from src import config
from src.model.products import ListProductPoint, ProductPoint


class QdrantAdapter:
    def __init__(self):
        self.client = QdrantClient(host=config.DATABASE_QDRANT_HOST, port=config.DATABASE_QDRANT_PORT)

    def create_collection_if_not_exists(self, name: str, vector_size: int):
        if not self.client.collection_exists(name):
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
            print(f"Collection '{name}' created.")
        else:
            print(f"Collection '{name}' already exists.")

    def batch_upsert(self, collection_name: str, product_points: list[ProductPoint]):
        points = [
            models.PointStruct(
                id=point.id,
                vector=point.vector,
                payload=point.payload.model_dump()
            )
            for point in product_points
        ]
        self.client.upsert(
            collection_name=collection_name,
            points=points
        )
    def find_similar(self, collection_name: str, vector_query: list[float]) -> ListProductPoint:
        search_result = self.client.search(
            collection_name=collection_name,
            query_vector=vector_query,
            with_payload=True,
            limit=20
        )

        results = []
        for result in search_result:
            output_model = ProductPoint(id=result.id, vector=result.vector, payload=result.payload)
            results.append(output_model)
        return ListProductPoint(points=results)
