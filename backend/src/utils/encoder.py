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
    """
    Text Encoder for generating vector embeddings from text using a CLIP model.

    Attributes:
       model_name (str): Name of the pre-trained CLIP model.
       device (str): Device to use for computation (e.g., "cuda" or "cpu").
       model (CLIPModel): Loaded CLIP model for text encoding.
       processor (CLIPProcessor): Preprocessor for the CLIP model.
    """
    def __init__(self, model_name: str, device: str) -> None:
        """
        Initializes the TextEncoder with a specified CLIP model and device.

        Args:
            model_name (str): Name of the pre-trained CLIP model.
            device (str): Device to use for computation (e.g., "cuda" or "cpu").
        """
        self.model_name: str = model_name
        self.device: str = device
        self.model: CLIPModel = CLIPModel.from_pretrained(self.model_name).to(self.device)
        self.processor: CLIPProcessor = CLIPProcessor.from_pretrained(self.model_name)

        if self.device == "cuda":
            self.model.half()

        self.model.eval()

    @lru_cache(maxsize=1000)
    def encode(self, text: str) -> np.ndarray:
        """
        Encodes text into a vector embedding using a cached method.

        Args:
            text (str): The text to encode.

        Returns:
            np.ndarray: Encoded vector representation of the text.
        """
        return self._encode_uncached(text)

    @torch.no_grad()
    def _encode_uncached(self, text: str) -> np.ndarray:
        """
        Encodes text into a vector embedding without caching.

        Args:
            text (str): The text to encode.

        Returns:
            np.ndarray: Encoded vector representation of the text.
        """
        inputs = self.processor(text=[text], return_tensors="pt", padding=True).to(self.device)
        text_features = self.model.get_text_features(**inputs)
        text_features /= text_features.norm(dim=-1, keepdim=True)
        return text_features.cpu().numpy()[0]


class ImageEncoder:
    """
    Image Encoder for generating vector embeddings from images using a CLIP model.

    Attributes:
        model_name (str): Name of the pre-trained CLIP model.
        device (str): Device to use for computation (e.g., "cuda" or "cpu").
        model (CLIPModel): Loaded CLIP model for image encoding.
        processor (CLIPProcessor): Preprocessor for the CLIP model.
    """
    def __init__(self, model_name: str, device: str) -> None:
        """
        Initializes the ImageEncoder with a specified CLIP model and device.

        Args:
            model_name (str): Name of the pre-trained CLIP model.
            device (str): Device to use for computation (e.g., "cuda" or "cpu").
        """
        self.model_name: str = model_name
        self.device: str = device
        self.model: CLIPModel = CLIPModel.from_pretrained(self.model_name).to(self.device)
        self.processor: CLIPProcessor = CLIPProcessor.from_pretrained(self.model_name)

    @staticmethod
    async def get_image_from_url(session: aiohttp.ClientSession, url: str) -> Image.Image:
        """
        Downloads an image from a URL and loads it into memory.

        Args:
            session (aiohttp.ClientSession): Async HTTP session.
            url (str): URL of the image.

        Returns:
            Image.Image: PIL image object.
        """
        async with session.get(url) as response:
            image_data = await response.read()
            return Image.open(io.BytesIO(image_data))

    def encode(self, images: list[Image.Image]) -> np.ndarray:
        """
        Encodes a list of images into vector embeddings.

        Args:
            images (list[Image.Image]): List of images to encode.

        Returns:
            np.ndarray: Encoded vector embeddings of the images.
        """
        with torch.no_grad():
            inputs = self.processor(images=images, return_tensors="pt", padding=True).to(self.device)
            image_features = self.model.get_image_features(**inputs)
        return image_features.cpu().numpy()

    def preprocess_image(self, image: Image.Image) -> dict[str, torch.Tensor]:
        return self.processor(images=image, return_tensors="pt", padding=True)

    async def encode_images(self, image_urls: list[str]) -> np.ndarray:
        """
        Downloads and encodes a list of images from URLs.

        Args:
            image_urls (list[str]): List of image URLs.

        Returns:
            np.ndarray: Encoded vector embeddings of the images.
        """
        async with aiohttp.ClientSession() as session:
            images = await asyncio.gather(*[self.get_image_from_url(session, url) for url in image_urls])
        return self.encode(images)


class ProductProcessor:
    """
    Processes product data and generates embeddings for product images.

    Attributes:
        input_file_path (str): Path to the input JSON file containing product data.
        output_file_path (str | None): Path to the output JSON file for saving processed data.
        encoder (ImageEncoder): ImageEncoder instance for encoding product images.
        json_processor (JsonProcessor): Utility for JSON file operations.
    """
    def __init__(self, input_file_path: str, encoder: ImageEncoder, output_file_path: str | None = None) -> None:
        """
        Initializes the ProductProcessor with input and output file paths and an encoder for processing product images.

        Args:
            input_file_path (str): Path to the input JSON file containing product data.
            encoder (ImageEncoder): An instance of ImageEncoder used to generate embeddings for product images.
            output_file_path (str | None): Optional; path to the output JSON file where processed data will be saved.
                Defaults to None if no output file is specified.
        """
        self.input_file_path: str = input_file_path
        self.output_file_path: str | None = output_file_path
        self.encoder: ImageEncoder = encoder
        self.json_processor: JsonProcessor = JsonProcessor()

    async def process_products(self, products: list[dict[str, any]]) -> list[dict[str, any]]:
        """
        Processes a list of products, generating image embeddings.

        Args:
            products (list[dict[str, any]]): List of product dictionaries.

        Returns:
            list[dict[str, any]]: Processed product data with image embeddings.
        """
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
    """
    Utility class for JSON file operations.

    Methods:
        read: Reads JSON data from a file.
        write: Writes JSON data to a file.
    """
    @staticmethod
    def read(file_path: str) -> list[dict[str, any]]:
        """
        Utility class for JSON file operations.

        Methods:
            read: Reads JSON data from a file.
            write: Writes JSON data to a file.
        """
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data

    @staticmethod
    def write(file_path: str, data: list[dict[str, any]]) -> None:
        """
        Writes JSON data to a file.

        Args:
            file_path (str): Path to the JSON file.
            data (list[dict[str, any]]): Data to write to the JSON file.
        """
        with open(file_path, 'w') as f:
            json.dump(data, f)