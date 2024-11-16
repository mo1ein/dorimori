import json
from functools import lru_cache
import torch
from transformers import CLIPProcessor, CLIPModel
import aiohttp
import asyncio
from PIL import Image
import io
import numpy as np


class TextEncoder:
    def __init__(self, model_name: str, device: str) -> None:
        self.model_name: str = model_name
        self.device: str = device
        self.model: CLIPModel = CLIPModel.from_pretrained(self.model_name).to(self.device)
        self.processor: CLIPProcessor = CLIPProcessor.from_pretrained(self.model_name)

        if self.device == "cuda":
            self.model.half()

        self.model.eval()

    @lru_cache(maxsize=1000)
    def encode(self, text: str) -> np.ndarray:
        return self._encode_uncached(text)

    @torch.no_grad()
    def _encode_uncached(self, text: str) -> np.ndarray:
        inputs = self.processor(text=[text], return_tensors="pt", padding=True).to(self.device)
        text_features = self.model.get_text_features(**inputs)
        text_features /= text_features.norm(dim=-1, keepdim=True)
        return text_features.cpu().numpy()[0]


class ImageEncoder:
    def __init__(self, model_name: str, device: str) -> None:
        self.model_name: str = model_name
        self.device: str = device
        self.model: CLIPModel = CLIPModel.from_pretrained(self.model_name).to(self.device)
        self.processor: CLIPProcessor = CLIPProcessor.from_pretrained(self.model_name)

    @staticmethod
    async def get_image_from_url(session: aiohttp.ClientSession, url: str) -> Image.Image:
        async with session.get(url) as response:
            image_data = await response.read()
            return Image.open(io.BytesIO(image_data))

    def encode(self, images: list[Image.Image]) -> np.ndarray:
        with torch.no_grad():
            inputs = self.processor(images=images, return_tensors="pt", padding=True).to(self.device)
            image_features = self.model.get_image_features(**inputs)
        return image_features.cpu().numpy()

    def preprocess_image(self, image: Image.Image) -> dict[str, torch.Tensor]:
        return self.processor(images=image, return_tensors="pt", padding=True)

    async def encode_images(self, image_urls: list[str]) -> np.ndarray:
        async with aiohttp.ClientSession() as session:
            images = await asyncio.gather(*[self.get_image_from_url(session, url) for url in image_urls])
        return self.encode(images)


class ProductProcessor:
    def __init__(self, input_file_path: str, encoder: ImageEncoder, output_file_path: str | None = None) -> None:
        self.input_file_path: str = input_file_path
        self.output_file_path: str | None = output_file_path
        self.encoder: ImageEncoder = encoder
        self.json_processor: JsonProcessor = JsonProcessor()

    async def process_products(self, products: list[dict[str, any]]) -> list[dict[str, any]]:
        all_images = []
        image_indices = []

        for i, product in enumerate(products):
            for url in product['images']:
                all_images.append(url)
                image_indices.append(i)

        embeddings = await self.encoder.encode_images(all_images)

        for j, embedding in enumerate(embeddings):
            product_index = image_indices[j]
            if 'image_embeddings' not in products[product_index]:
                products[product_index]['image_embeddings'] = []
            products[product_index]['image_embeddings'].append(embedding.tolist())

        return products

    async def run(self) -> None:
        products = self.json_processor.read(self.input_file_path)
        await self.process_products(products)
        self.json_processor.write(self.output_file_path, products)


class JsonProcessor:
    @staticmethod
    def read(file_path: str) -> list[dict[str, any]]:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data

    @staticmethod
    def write(file_path: str, data: list[dict[str, any]]) -> None:
        with open(file_path, 'w') as f:
            json.dump(data, f)