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

# Base class for Stable Diffusion Image Generation Nodes
class StableDiffusionImageGenerationNodeBase:
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


class Leon_StableDiffusion_35_API_Node(StableDiffusionImageGenerationNodeBase):
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "image_url", "seed")
    FUNCTION = "generate_sd35_image"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "A cute cat", "tooltip": "What you wish to see in the output image. Use (word:weight) format to control word weights (max 10,000 characters)"}),
                "model": (["sd3.5-large", "sd3.5-large-turbo", "sd3.5-medium"], {"default": "sd3.5-large", "tooltip": "Stable Diffusion 3.5 model to use for generation"}),
                "output_format": (["png", "jpeg", "webp"], {"default": "webp", "tooltip": "Format of the output image"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 4294967294, "tooltip": "Seed for deterministic generation (0-4294967294)"}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/images/generations", "tooltip": "API URL"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_API_KEY_HERE", "tooltip": "Your HyprLab API key"}),
                "response_format": (["url", "b64_json"], {"default": "url", "tooltip": "Format of the response data"}),
            },
            "optional": {
                "negative_prompt": ("STRING", {"multiline": True, "default": "", "tooltip": "What NOT to include in the output image (max 10,000 characters)"}),
                "aspect_ratio": (["16:9", "1:1", "21:9", "2:3", "3:2", "4:5", "5:4", "9:16", "9:21"], {"default": "1:1", "tooltip": "Aspect ratio of the generated image"}),
            }
        }

    def generate_sd35_image(
        self,
        prompt,
        model,
        output_format,
        seed,
        api_url,
        api_key,
        response_format,
        negative_prompt="",
        aspect_ratio="1:1"
    ):
        if len(prompt) > 10000:
            raise ValueError("Prompt must not exceed 10,000 characters")
        if not prompt.strip():
            raise ValueError("Prompt must be a non-empty string")
        
        if negative_prompt and len(negative_prompt) > 10000:
            raise ValueError("Negative prompt must not exceed 10,000 characters")

        if seed < 0 or seed > 4294967294:
            raise ValueError("Seed must be between 0 and 4294967294")

        payload = {
            "model": model,
            "prompt": prompt,
            "response_format": response_format,
            "output_format": output_format,
            "seed": seed
        }

        # Add optional parameters
        if negative_prompt.strip():
            payload["negative_prompt"] = negative_prompt
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
        
        return self._make_api_call(payload, api_url, api_key, response_format, output_format, seed)


class Leon_StableDiffusion_3_Ultra_API_Node(StableDiffusionImageGenerationNodeBase):
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "image_url", "seed")
    FUNCTION = "generate_sd3_ultra_image"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "A cute cat", "tooltip": "What you wish to see in the output image. Use (word:weight) format to control word weights (max 10,000 characters)"}),
                "model": (["sd3-ultra"], {"default": "sd3-ultra", "tooltip": "Stable Diffusion 3 Ultra model"}),
                "output_format": (["png", "jpeg", "webp"], {"default": "webp", "tooltip": "Format of the output image"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 4294967294, "tooltip": "Seed for deterministic generation (0-4294967294)"}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/images/generations", "tooltip": "API URL"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_API_KEY_HERE", "tooltip": "Your HyprLab API key"}),
                "response_format": (["url", "b64_json"], {"default": "url", "tooltip": "Format of the response data"}),
            },
            "optional": {
                "negative_prompt": ("STRING", {"multiline": True, "default": "", "tooltip": "What NOT to include in the output image (max 10,000 characters)"}),
                "aspect_ratio": (["16:9", "1:1", "21:9", "2:3", "3:2", "4:5", "5:4", "9:16", "9:21"], {"default": "1:1", "tooltip": "Aspect ratio of the generated image"}),
            }
        }

    def generate_sd3_ultra_image(
        self,
        prompt,
        model,
        output_format,
        seed,
        api_url,
        api_key,
        response_format,
        negative_prompt="",
        aspect_ratio="1:1"
    ):
        if len(prompt) > 10000:
            raise ValueError("Prompt must not exceed 10,000 characters")
        if not prompt.strip():
            raise ValueError("Prompt must be a non-empty string")
        
        if negative_prompt and len(negative_prompt) > 10000:
            raise ValueError("Negative prompt must not exceed 10,000 characters")

        if seed < 0 or seed > 4294967294:
            raise ValueError("Seed must be between 0 and 4294967294")

        payload = {
            "model": model,
            "prompt": prompt,
            "response_format": response_format,
            "output_format": output_format,
            "seed": seed
        }

        # Add optional parameters
        if negative_prompt.strip():
            payload["negative_prompt"] = negative_prompt
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
        
        return self._make_api_call(payload, api_url, api_key, response_format, output_format, seed)


class Leon_StableDiffusion_XL_API_Node(StableDiffusionImageGenerationNodeBase):
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "image_url", "seed")
    FUNCTION = "generate_sdxl_image"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "A cute cat", "tooltip": "Text prompt for image generation"}),
                "model": (["sdxl-1.0"], {"default": "sdxl-1.0", "tooltip": "Stable Diffusion XL 1.0 model"}),
                "output_format": (["png", "jpeg", "webp"], {"default": "webp", "tooltip": "Format of the output image"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 4294967295, "tooltip": "Seed for deterministic generation (0-4294967295)"}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/images/generations", "tooltip": "API URL"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_API_KEY_HERE", "tooltip": "Your HyprLab API key"}),
                "response_format": (["url", "b64_json"], {"default": "url", "tooltip": "Format of the response data"}),
            },
            "optional": {
                "height": ("INT", {"default": 1024, "min": 640, "max": 1536, "tooltip": "Height in pixels (must match allowed dimensions)"}),
                "width": ("INT", {"default": 1024, "min": 640, "max": 1536, "tooltip": "Width in pixels (must match allowed dimensions)"}),
                "cfg_scale": ("FLOAT", {"default": 5.0, "min": 0.0, "max": 35.0, "step": 0.1, "tooltip": "How strictly the model follows the prompt (0-35)"}),
                "sampler": ([
                    "DDIM", "DDPM", "K_DPMPP_2M", "K_DPMPP_2S_ANCESTRAL",
                    "K_DPM_2", "K_DPM_2_ANCESTRAL", "K_EULER", "K_EULER_ANCESTRAL",
                    "K_HEUN", "K_LMS"
                ], {"default": "K_DPM_2_ANCESTRAL", "tooltip": "Sampling algorithm"}),
                "steps": ("INT", {"default": 20, "min": 1, "max": 50, "tooltip": "Number of processing steps (1-50)"}),
                "style_preset": ([
                    "3d-model", "analog-film", "anime", "cinematic", "comic-book", "digital-art",
                    "enhance", "fantasy-art", "isometric", "line-art", "low-poly", "modeling-compound",
                    "neon-punk", "origami", "photographic", "pixel-art", "tile-texture"
                ], {"default": "photographic", "tooltip": "Preset style to apply to the generated image"}),
            }
        }

    def generate_sdxl_image(
        self,
        prompt,
        model,
        output_format,
        seed,
        api_url,
        api_key,
        response_format,
        height=1024,
        width=1024,
        cfg_scale=5.0,
        sampler="K_DPM_2_ANCESTRAL",
        steps=20,
        style_preset="photographic"
    ):
        if not prompt.strip():
            raise ValueError("Prompt must be a non-empty string")

        if seed < 0 or seed > 4294967295:
            raise ValueError("Seed must be between 0 and 4294967295")

        # Validate allowed dimensions
        allowed_dimensions = [
            (1024, 1024), (1152, 896), (1216, 832), (1344, 768), (1536, 640),
            (640, 1536), (768, 1344), (832, 1216), (896, 1152)
        ]
        
        if (width, height) not in allowed_dimensions and (height, width) not in allowed_dimensions:
            raise ValueError(f"Dimensions {width}x{height} not allowed. Must be one of: {allowed_dimensions}")

        payload = {
            "model": model,
            "prompt": prompt,
            "response_format": response_format,
            "output_format": output_format,
            "seed": seed,
            "height": height,
            "width": width,
            "cfg_scale": cfg_scale,
            "sampler": sampler,
            "steps": steps,
            "style_preset": style_preset
        }
        
        return self._make_api_call(payload, api_url, api_key, response_format, output_format, seed)


# Node mappings for ComfyUI
STABLE_DIFFUSION_NODE_CLASS_MAPPINGS = {
    "Leon_StableDiffusion_35_API_Node": Leon_StableDiffusion_35_API_Node,
    "Leon_StableDiffusion_3_Ultra_API_Node": Leon_StableDiffusion_3_Ultra_API_Node,
    "Leon_StableDiffusion_XL_API_Node": Leon_StableDiffusion_XL_API_Node,
}

STABLE_DIFFUSION_NODE_DISPLAY_NAME_MAPPINGS = {
    "Leon_StableDiffusion_35_API_Node": "🤖 Leon Stable Diffusion 3.5 API",
    "Leon_StableDiffusion_3_Ultra_API_Node": "🤖 Leon Stable Diffusion 3 Ultra API",
    "Leon_StableDiffusion_XL_API_Node": "🤖 Leon Stable Diffusion XL API",
}