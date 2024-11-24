from qdrant_client import QdrantClient, models
from qdrant_client.http.models import VectorParams, Distance, Filter, FieldCondition, Range, Match
from src import config
from src.model.products import ListProductPoint, ProductPoint


class QdrantAdapter:
    """
    Adapter class for managing and querying Qdrant collections.

    Attributes:
        client (QdrantClient): Qdrant client initialized with host and port settings.
    """
    def __init__(self):
        """
               Initializes the QdrantAdapter instance and connects to the Qdrant server using configuration settings.
        """
        self.client = QdrantClient(host=config.DATABASE_QDRANT_HOST, port=config.DATABASE_QDRANT_PORT)

    def create_collection_if_not_exists(self, name: str, vector_size: int):
        """
        Creates a Qdrant collection with the specified name and vector size if it does not exist.

        Args:
            name (str): Name of the collection to be created.
            vector_size (int): Size of the vectors to be stored in the collection.

        Prints:
            A message indicating whether the collection was created or already exists.
        """
        if not self.client.collection_exists(name):
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
            print(f"Collection '{name}' created.")
        else:
            print(f"Collection '{name}' already exists.")

    def batch_upsert(self, collection_name: str, product_points: list[ProductPoint]):
        """
        Inserts or updates a batch of product data points into the specified collection.

        Args:
            collection_name (str): Name of the collection where data points will be stored.
            product_points (list[ProductPoint]): A list of ProductPoint objects to be upserted.

        Notes:
            Each ProductPoint should include an ID, vector, and payload.
        """
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

    def find_similar(
            self,
            vector_query: list[float],
            filters: list[dict[str, any]] = None
    ) -> ListProductPoint:
        """
        Searches for vectors in the collection similar to a given query vector, with optional filtering.

        Args:
           vector_query (list[float]): The query vector to find similar vectors.
           filters (list[dict[str, any]], optional): A list of filter conditions to apply during the search.
               Each filter should include 'field', 'operation', and 'value'.

        Returns:
           ListProductPoint: A list of ProductPoint objects matching the query.
        """
        must_conditions = []
        price_range = {}
        # todo: add all categories size shirt felan ...
        if filters:
            for filter_item in filters:
                field = filter_item.get('field')
                operation = filter_item.get('operation')
                value = filter_item.get('value')

                if field and operation:
                    if field == 'current_price' and operation in ['gt', 'gte', 'lt', 'lte']:
                        price_range[operation] = value
                    if field == 'query':
                        pass
                    else:
                        must_conditions.append(self._create_field_condition(filter_item))

        if price_range:
            must_conditions.append(FieldCondition(key='current_price', range=Range(**price_range)))
            # todo: handle none vales
        filter_conditions = Filter(must=must_conditions) if must_conditions else None
        search_result = self.client.search(
            collection_name=config.DATABASE_QDRANT_COLLECTION_NAME,
            query_vector=vector_query,
            with_payload=True,
            limit=20,
            query_filter=filter_conditions
        )
        print("diiiir")

        results = [ProductPoint(id=result.id, vector=result.vector, payload=result.payload) for result in search_result]

        return ListProductPoint(points=results)


    def _create_field_condition(self, filter_item: dict[str, any]) -> FieldCondition:
        """
        Creates a FieldCondition for filtering based on a filter dictionary.

        Args:
            filter_item (dict[str, any]): A dictionary with 'field', 'operation', and 'value' keys.

        Returns:
            FieldCondition: The constructed Qdrant FieldCondition object.

        Raises:
            ValueError: If the operation is not supported.
        """
        field = filter_item.get('field')
        operation = filter_item.get('operation')
        value = filter_item.get('value')
        if operation in ['gt', 'gte', 'lt', 'lte']:
            return FieldCondition(key=field, range=Range(**{operation: value}))
        elif operation == 'eq':
            return FieldCondition(key=field, match={'value': value})
        else:
            raise ValueError(f"Unsupported operation: {operation}")