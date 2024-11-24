import asyncio
import os
import time

import torch
from tqdm import tqdm

from src.config import DATASET_PATH, CLIP_MODEL_NAME, CHECKPOINT_PATH, DATABASE_QDRANT_COLLECTION_NAME, \
    DATABASE_QDRANT_COLLECTION_NAME
from src.adapter.qdrant import QdrantAdapter
from src.model.products import ProductPayload, ProductPoint
from src.repository.product import ProductRepository
from src.utils.encoder import ImageEncoder, ProductProcessor, JsonProcessor


class DataPipeline:
    """
    Handles processing, encoding, and insertion of product data into Qdrant.

    This class processes input product data, generates image embeddings using a specified
    encoder, and inserts the processed data into a Qdrant vector database. The pipeline
    uses checkpoints to ensure data processing can resume from the last successful batch
    in case of interruptions.

    Attributes:
        input_file (str): Path to the input JSON file containing product data.
        processor (ProductProcessor): Processor for product data, including image encoding.
        qdrant_adapter (QdrantAdapter): Adapter for interacting with Qdrant.
        product_repository (ProductRepository): Repository for managing product data operations.
        checkpoint_file (str): Path to the checkpoint file for saving and loading progress.
    """
    def __init__(self, input_file: str, encoder: ImageEncoder, qdrant_adapter: QdrantAdapter) -> None:
        """
        Initializes the DataPipeline with input data, an image encoder, and a Qdrant adapter.

        Args:
            input_file (str): Path to the JSON file containing product data.
            encoder (ImageEncoder): Encoder for generating image embeddings.
            qdrant_adapter (QdrantAdapter): Adapter for interacting with the Qdrant vector database.
        """
        self.input_file = input_file
        self.processor = ProductProcessor(input_file_path=input_file, encoder=encoder)
        self.qdrant_adapter = qdrant_adapter
        self.product_repository = ProductRepository(qdrant_adapter)
        self.checkpoint_file = f'{CHECKPOINT_PATH}/checkpoint.txt'

    def load_checkpoint(self) -> int:
        """
        Load the last processed index from the checkpoint file.

        Returns:
            int: The last processed index. Defaults to 0 if no checkpoint exists.
        """
        if os.path.exists(self.checkpoint_file):
            with open(self.checkpoint_file, 'r') as f:
                return int(f.read().strip())
        return 0

    def save_checkpoint(self, index) -> None:
        """
        Save the current index to the checkpoint file.

        Args:
            index (int): The index to save for resuming processing later.
        """
        with open(self.checkpoint_file, 'w') as f:
            f.write(str(index))

    async def run(self) -> None:
        """
        Runs the data pipeline to process, encode, and insert product data.

        This method processes the product data in batches, generates embeddings for each product,
        and inserts the data into the Qdrant vector database. The process is checkpointed to
        resume processing in case of interruptions.

        Steps:
        - Read product data from the input file.
        - Load the last processed checkpoint.
        - Process and encode product data in batches.
        - Insert processed data into Qdrant.
        - Save progress after each batch.

        Periodically checks for new data to process.

        Raises:
            Exception: If an error occurs during batch processing.
        """
        vector_size = 512  # Adjust based on your model's output size
        self.product_repository.create_collection_if_not_exists(
            name=DATABASE_QDRANT_COLLECTION_NAME,
            vector_size=vector_size
        )

        while True:
            data = JsonProcessor.read(self.input_file)
            start_index = self.load_checkpoint()
            total_batches = (len(data) + 10 - 1) // 10

            with tqdm(
                    total=total_batches,
                    desc="Processing and inserting batches",
                    initial=start_index // 10
            ) as pbar:
                for i in range(start_index, len(data), 10):
                    batch = data[i:i + 10]
                    try:
                        processed_batch = await self.processor.process_products(batch)

                        product_points = []
                        for item in processed_batch:
                            payload = ProductPayload.model_validate(item)
                            product_point = ProductPoint(
                                id=item['id'],
                                vector=item['image_embeddings'][0],
                                payload=payload,
                            )
                            product_points.append(product_point)

                        self.product_repository.batch_insert(
                            DATABASE_QDRANT_COLLECTION_NAME,
                            product_points
                        )

                        self.save_checkpoint(i + 10)
                        pbar.update(1)
                    except Exception as e:
                        print(f"Error processing batch {i}: {str(e)}")
                        # Optionally log the error or implement retry logic

            # Wait before checking for new data again (e.g., every minute)
            print("Waiting for new data...")
            time.sleep(60)  # Adjust the sleep duration as needed


# todo: i think put in other dir and change name
async def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_name = CLIP_MODEL_NAME
    encoder = ImageEncoder(model_name=model_name, device=device)
    qdrant_adapter = QdrantAdapter()

    pipeline = DataPipeline(
        input_file=DATASET_PATH,
        encoder=encoder,
        qdrant_adapter=qdrant_adapter
    )

    await pipeline.run()


if __name__ == "__main__":
    asyncio.run(main())
