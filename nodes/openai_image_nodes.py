import tenacity
import random
import base64
from PIL import Image
import os
import io
import torch
import numpy as np
import requests
import json
import time

# Base class for OpenAI Image Generation Nodes
class OpenAIImageGenerationNodeBase:
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "image_url", "seed")

    @tenacity.retry(
        wait=tenacity.wait_exponential(multiplier=1.25, min=5, max=30),
        stop=tenacity.stop_after_attempt(5)
    )
    def _make_api_call(
        self,
        payload,
        api_url,
        api_key,
        response_format, # "url" or "b64_json"
        output_format,   # "png", "jpeg", "webp"
        seed
    ):
        if not payload.get("prompt", "").strip():
            raise ValueError("Prompt must be a non-empty string")

        random.seed(seed)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        try:
            response = requests.post(api_url.rstrip('/'), json=payload, headers=headers)
            
            print(f"API Request URL: {api_url.rstrip('/')}")
            print(f"API Request Payload: {json.dumps(payload)}")
            print(f"HTTP status: {response.status_code}")
            response_text_to_print = response.text
            if "b64_json" in response_text_to_print and len(response_text_to_print) > 1000:
                response_text_to_print = response_text_to_print[:500] + "... (response truncated)"
            print(f"Response: {response_text_to_print}")
            
            response.raise_for_status()
            response_json = response.json()

            pil_img = None
            actual_image_url = ""

            if response_format == "b64_json":
                b64_data = response_json["data"][0]["b64_json"]
                img_data = base64.b64decode(b64_data)
                pil_img = Image.open(io.BytesIO(img_data))
                actual_image_url = f"data:image/{output_format};base64,{b64_data}"
            else:
                actual_image_url = response_json["data"][0]["url"]
                if not actual_image_url:
                    raise Exception(f"Image URL not found in response: {response_json}")
                
                img_response = requests.get(actual_image_url)
                if img_response.status_code != 200:
                    raise Exception(f"Failed to download the image from {actual_image_url}, status: {img_response.status_code}")
                pil_img = Image.open(io.BytesIO(img_response.content))

            if pil_img is None:
                raise Exception("Failed to load image from API response")

            pil_img = pil_img.convert("RGBA")
            img_array = np.array(pil_img).astype(np.float32) / 255.0

            if img_array.ndim == 3 and img_array.shape[-1] == 3:
                alpha_channel = np.ones_like(img_array[..., :1])
                img_array = np.concatenate((img_array, alpha_channel), axis=-1)
            
            img_tensor = torch.from_numpy(img_array).unsqueeze(0)
            
            return (img_tensor, actual_image_url, seed)

        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
        except KeyError as e:
            print(f"Full error response for KeyError: {response.text if 'response' in locals() else 'Response object not available'}")
            raise Exception(f"Unexpected response format (KeyError): {str(e)}. Check API documentation and response structure.")
        except Exception as e:
            print(f"Full error response for other Exception: {response.text if 'response' in locals() else 'Response object not available'}")
            raise Exception(f"Image generation failed: {str(e)}")

    def _tensor_to_base64_data_uri(self, tensor_image):
        if tensor_image is None:
            return None
        
        if tensor_image.ndim == 4:
            tensor_image = tensor_image[0]
        
        np_image = (tensor_image.cpu().numpy() * 255).astype(np.uint8)
        pil_image = Image.fromarray(np_image, 'RGBA' if np_image.shape[-1] == 4 else 'RGB')
        
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        base64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{base64_str}"


class Leon_DALLE_Image_API_Node(OpenAIImageGenerationNodeBase):
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "image_url", "seed")
    FUNCTION = "generate_dalle_image"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "A cute baby sea otter", "tooltip": "Text description of the image to generate"}),
                "model": (["dall-e-3", "dall-e-2", "azure/dall-e-3"], {"default": "dall-e-3", "tooltip": "DALL-E model to use for generation"}),
                "quality": (["standard", "hd"], {"default": "standard", "tooltip": "Image quality (DALL-E 3 only)"}),
                "response_format": (["url", "b64_json"], {"default": "url", "tooltip": "Format of the response"}),
                "size": (["1024x1024", "1024x1792", "1792x1024", "512x512", "256x256"], {"default": "1024x1024", "tooltip": "Size of the generated image"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Random seed for reproducible results"}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/images/generations", "tooltip": "API URL"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_HYPRLAB_API_KEY", "tooltip": "Your HyprLab API key"}),
            },
            "optional": {
                "style": (["None", "vivid", "natural"], {"default": "None", "tooltip": "Style of the generated image (DALL-E 3 only, None to omit)"}),
            }
        }

    def generate_dalle_image(
        self,
        prompt,
        model,
        quality,
        response_format,
        size,
        seed,
        api_url,
        api_key,
        style="None"
    ):
        if not prompt.strip():
            raise ValueError("Prompt must be a non-empty string")

        # Validate size based on model
        if model in ["dall-e-3", "azure/dall-e-3"]:
            valid_sizes = ["1024x1024", "1024x1792", "1792x1024"]
            if size not in valid_sizes:
                raise ValueError(f"For DALL-E 3, size must be one of: {valid_sizes}")
        elif model == "dall-e-2":
            valid_sizes = ["1024x1024", "512x512", "256x256"]
            if size not in valid_sizes:
                raise ValueError(f"For DALL-E 2, size must be one of: {valid_sizes}")

        payload = {
            "model": model,
            "prompt": prompt,
            "n": 1,
            "response_format": response_format,
            "size": size
        }

        # Add DALL-E 3 specific parameters
        if model in ["dall-e-3", "azure/dall-e-3"]:
            payload["quality"] = quality
            if style != "None":
                payload["style"] = style

        return self._make_api_call(payload, api_url, api_key, response_format, "png", seed)


class Leon_GPT_Image_API_Node(OpenAIImageGenerationNodeBase):
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "image_url", "seed")
    FUNCTION = "generate_gpt_image"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "A cute cat.", "tooltip": "Text description of the image to generate"}),
                "model": (["gpt-image-1"], {"default": "gpt-image-1", "tooltip": "GPT Image model to use"}),
                "background": (["auto"], {"default": "auto", "tooltip": "Background setting"}),
                "moderation": (["auto"], {"default": "auto", "tooltip": "Content moderation setting"}),
                "output_compression": ("INT", {"default": 100, "min": 1, "max": 100, "tooltip": "Output compression quality (1-100)"}),
                "output_format": (["png", "jpeg", "webp"], {"default": "png", "tooltip": "Output image format"}),
                "quality": (["low", "medium", "high"], {"default": "high", "tooltip": "Image generation quality"}),
                "response_format": (["url", "b64_json"], {"default": "url", "tooltip": "Format of the response"}),
                "size": (["1024x1024", "1024x1536", "1536x1024"], {"default": "1024x1024", "tooltip": "Size of the generated image"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Random seed for reproducible results"}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/images/generations", "tooltip": "API URL"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_HYPRLAB_API_KEY", "tooltip": "Your HyprLab API key"}),
            },
            "optional": {
                "input_image": ("IMAGE", {"tooltip": "Optional input image for image-to-image generation"}),
                "input_images": ("IMAGE", {"tooltip": "Optional multiple input images (will be converted to array)"}),
                "mask_image": ("IMAGE", {"tooltip": "Optional mask image for inpainting"}),
            }
        }

    def generate_gpt_image(
        self,
        prompt,
        model,
        background,
        moderation,
        output_compression,
        output_format,
        quality,
        response_format,
        size,
        seed,
        api_url,
        api_key,
        input_image=None,
        input_images=None,
        mask_image=None
    ):
        if not prompt.strip():
            raise ValueError("Prompt must be a non-empty string")

        payload = {
            "model": model,
            "prompt": prompt,
            "background": background,
            "moderation": moderation,
            "output_compression": output_compression,
            "output_format": output_format,
            "quality": quality,
            "response_format": response_format,
            "size": size
        }

        # Handle single image input
        if input_image is not None:
            image_data_uri = self._tensor_to_base64_data_uri(input_image)
            if image_data_uri:
                payload["image"] = image_data_uri

        # Handle multiple image inputs
        if input_images is not None:
            # For multiple images, we'll treat it as an array
            image_data_uri = self._tensor_to_base64_data_uri(input_images)
            if image_data_uri:
                payload["image"] = [image_data_uri]  # Convert to array format

        # Handle mask image
        if mask_image is not None:
            mask_data_uri = self._tensor_to_base64_data_uri(mask_image)
            if mask_data_uri:
                payload["mask"] = mask_data_uri

        return self._make_api_call(payload, api_url, api_key, response_format, output_format, seed)


# Node mappings for ComfyUI
OPENAI_IMAGE_NODE_CLASS_MAPPINGS = {
    "Leon_DALLE_Image_API_Node": Leon_DALLE_Image_API_Node,
    "Leon_GPT_Image_API_Node": Leon_GPT_Image_API_Node,
}

OPENAI_IMAGE_NODE_DISPLAY_NAME_MAPPINGS = {
    "Leon_DALLE_Image_API_Node": "🤖 Leon DALL-E Image API",
    "Leon_GPT_Image_API_Node": "🤖 Leon GPT-Image API",
}