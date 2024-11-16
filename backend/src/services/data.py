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
    def __init__(self, input_file: str, encoder: ImageEncoder, qdrant_adapter: QdrantAdapter) -> None:
        self.input_file = input_file
        self.processor = ProductProcessor(input_file_path=input_file, encoder=encoder)
        self.qdrant_adapter = qdrant_adapter
        self.product_repository = ProductRepository(qdrant_adapter)
        self.checkpoint_file = f'{CHECKPOINT_PATH}/checkpoint.txt'

    def load_checkpoint(self) -> int:
        """Load the last processed index from the checkpoint file."""
        if os.path.exists(self.checkpoint_file):
            with open(self.checkpoint_file, 'r') as f:
                return int(f.read().strip())
        return 0

    def save_checkpoint(self, index) -> None:
        """Save the current index to the checkpoint file."""
        with open(self.checkpoint_file, 'w') as f:
            f.write(str(index))

    async def run(self) -> None:
        print("inja")
        vector_size = 512  # Adjust based on your model's output size
        self.product_repository.create_collection_if_not_exists(
            name=DATABASE_QDRANT_COLLECTION_NAME,
            vector_size=vector_size
        )

        while True:
            print("in loop")
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


# todo: put in other dif and change name?
async def main():
    print('hey')
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_name = CLIP_MODEL_NAME
    encoder = ImageEncoder(model_name=model_name, device=device)
    qdrant_adapter = QdrantAdapter()
    print("good")

    pipeline = DataPipeline(
        input_file=DATASET_PATH,
        encoder=encoder,
        qdrant_adapter=qdrant_adapter
    )

    print("oof")
    await pipeline.run()


if __name__ == "__main__":
    asyncio.run(main())
