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

# Base class for HyprLab Image Generation Nodes
class HyprLabImageGenerationNodeBase:
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
        if not payload.get("prompt", "").strip() and not payload.get("image_reference_url", "") : # Luma might not need prompt if image ref is strong
            pass

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


class Leon_Google_Image_API_Node(HyprLabImageGenerationNodeBase):
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "image_url", "seed")
    FUNCTION = "generate_image"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "A beautiful landscape with mountains and a lake", "tooltip": "Main text input to guide the generation process (max 10,000 characters)"}),
                "model": (["imagen-4-ultra", "imagen-4", "imagen-4-fast", "imagen-3", "imagen-3-fast"], {"default": "imagen-4-ultra", "tooltip": "Google Imagen model to use for generation"}),
                "aspect_ratio": (["1:1", "3:4", "4:3", "9:16", "16:9"], {"default": "1:1", "tooltip": "Aspect ratio of the generated image"}),
                "output_format": (["png", "jpeg", "webp"], {"default": "png", "tooltip": "Format of the output image"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Random seed for reproducible results"}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/images/generations", "tooltip": "API URL"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_API_KEY_HERE", "tooltip": "Your HyprLab API key"}),
                "response_format": (["url", "b64_json"], {"default": "url", "tooltip": "How the response data should be formatted"}),
            }
        }

    def generate_image(
        self,
        prompt,
        model,
        aspect_ratio,
        output_format,
        seed,
        api_url,
        api_key,
        response_format
    ):
        if len(prompt) > 10000:
            raise ValueError("Prompt must not exceed 10,000 characters")
        if not prompt.strip():
            raise ValueError("Prompt must be a non-empty string")

        payload = {
            "model": model,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "response_format": response_format,
            "output_format": output_format
        }
        
        return self._make_api_call(payload, api_url, api_key, response_format, output_format, seed)


class Leon_Luma_AI_Image_API_Node(HyprLabImageGenerationNodeBase):
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "image_url", "seed")
    FUNCTION = "generate_luma_image"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "A stunning fantasy landscape", "tooltip": "Main text input to guide the generation process (max 10,000 characters)"}),
                "model": (["photon", "photon-flash"], {"default": "photon", "tooltip": "Luma AI model to use for generation"}),
                "output_format": (["png", "jpeg", "webp"], {"default": "png", "tooltip": "Format of the output image"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Random seed for reproducible results (may not be used by Luma API via HyprLab)"}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/images/generations", "tooltip": "API URL"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_API_KEY_HERE", "tooltip": "Your HyprLab API key"}),
                "response_format": (["url", "b64_json"], {"default": "url", "tooltip": "How the response data should be formatted"}),
            },
            "optional": {
                "aspect_ratio": (["1:1", "3:4", "4:3", "9:16", "16:9", "9:21", "21:9"], {"default": "1:1", "tooltip": "Aspect ratio of the output. If not specified, model default may be used."}),
                "input_image_ref_socket": ("IMAGE", { "tooltip": "Image for image reference."}),
                "image_reference_weight": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01, "tooltip": "Influence of the image reference (0 to 1)."}),
                "input_style_ref_socket": ("IMAGE", { "tooltip": "Image for style reference."}),
                "style_reference_weight": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01, "tooltip": "Influence of the style reference (0 to 1)."}),
                "input_char_ref_socket": ("IMAGE", { "tooltip": "Image for character reference."}),
            }
        }

    def generate_luma_image(
        self,
        prompt,
        model,
        output_format,
        seed,
        api_url,
        api_key,
        response_format,
        aspect_ratio="1:1",
        input_image_ref_socket=None,
        image_reference_weight=0.5,
        input_style_ref_socket=None,
        style_reference_weight=0.5,
        input_char_ref_socket=None
    ):
        if len(prompt) > 10000:
            raise ValueError("Prompt must not exceed 10,000 characters")
        
        actual_image_ref_url = ""
        if input_image_ref_socket is not None:
            actual_image_ref_url = self._tensor_to_base64_data_uri(input_image_ref_socket)

        actual_style_ref_url = ""
        if input_style_ref_socket is not None:
            actual_style_ref_url = self._tensor_to_base64_data_uri(input_style_ref_socket)

        actual_char_ref_url = ""
        if input_char_ref_socket is not None:
            actual_char_ref_url = self._tensor_to_base64_data_uri(input_char_ref_socket)

        if not prompt.strip() and not actual_image_ref_url and not actual_style_ref_url and not actual_char_ref_url:
             raise ValueError("Prompt is required for Luma AI, or at least one reference Image (Socket) must be provided.")

        payload = {
            "model": model,
            "prompt": prompt,
            "response_format": response_format,
            "output_format": output_format
        }

        if aspect_ratio:
             payload["aspect_ratio"] = aspect_ratio
        
        if actual_image_ref_url:
            payload["image_reference_url"] = actual_image_ref_url
            payload["image_reference_weight"] = image_reference_weight
        
        if actual_style_ref_url:
            payload["style_reference_url"] = actual_style_ref_url
            payload["style_reference_weight"] = style_reference_weight

        if actual_char_ref_url:
            payload["character_reference_url"] = actual_char_ref_url

        return self._make_api_call(payload, api_url, api_key, response_format, output_format, seed)


class Leon_Flux_Image_API_Node(HyprLabImageGenerationNodeBase):
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "image_url", "seed")
    FUNCTION = "generate_flux_image"

    MODEL_MAPPING = {
        "FLUX 1.1 Pro Ultra": "flux-1.1-pro-ultra",
        "FLUX 1.1 Pro": "flux-1.1-pro",
        "FLUX Pro Canny": "flux-pro-canny",
        "FLUX Dev": "flux-dev",
        "FLUX Schnell": "flux-schnell"
    }
    ASPECT_RATIOS_ULTRA = ["21:9", "16:9", "3:2", "4:3", "5:4", "1:1", "4:5", "3:4", "2:3", "9:16", "9:21"]

    def __init__(self):
        super().__init__()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_choice": (list(cls.MODEL_MAPPING.keys()), {"default": "FLUX 1.1 Pro"}),
                "prompt": ("STRING", {"multiline": True, "default": "A stunning artistic photo"}),
                "response_format": (["url", "b64_json"], {"default": "url"}),
                "output_format": (["png", "jpeg", "webp"], {"default": "png"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/images/generations"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_HYPRLAB_API_KEY"}),
            },
            "optional": {
                "input_image_prompt_socket": ("IMAGE", { "tooltip": "Image for image guidance. Must be at least 256x256 pixels (FLUX 1.1 Pro Ultra, FLUX 1.1 Pro, FLUX Pro Canny)."}),
                "image_prompt_strength": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01, "tooltip": "Strength of image_prompt (FLUX 1.1 Pro Ultra only)"}),
                "aspect_ratio": (cls.ASPECT_RATIOS_ULTRA, {"default": "1:1", "tooltip": "Aspect ratio (FLUX 1.1 Pro Ultra only)"}),
                "raw": ("BOOLEAN", {"default": False, "tooltip": "Return raw output (FLUX 1.1 Pro Ultra only)"}),
                "steps": ("INT", {"default": 30, "min": 1, "max": 50, "tooltip": "Number of steps (FLUX 1.1 Pro, FLUX Pro Canny, FLUX Dev, FLUX Schnell)"}),
                "height": ("INT", {"default": 1024, "min": 256, "max": 1440, "step": 32, "tooltip": "Image height, multiple of 32 (FLUX 1.1 Pro, FLUX Pro Canny, FLUX Dev, FLUX Schnell)"}),
                "width": ("INT", {"default": 1024, "min": 256, "max": 1440, "step": 32, "tooltip": "Image width, multiple of 32 (FLUX 1.1 Pro, FLUX Pro Canny, FLUX Dev, FLUX Schnell)"}),
            }
        }

    def generate_flux_image(self, model_choice, prompt, response_format, output_format, seed, api_url, api_key,
                              input_image_prompt_socket=None, image_prompt_strength=0.5, aspect_ratio="1:1", raw=False,
                              steps=30, height=1024, width=1024):

        actual_model_name = self.MODEL_MAPPING.get(model_choice)
        if not actual_model_name:
            raise ValueError(f"Invalid model choice: {model_choice}.")

        payload = {
            "model": actual_model_name, "prompt": prompt,
            "response_format": response_format, "output_format": output_format,
        }
        if not prompt.strip():
            raise ValueError("Prompt must be a non-empty string.")

        actual_image_prompt_payload = ""
        if input_image_prompt_socket is not None:
            actual_image_prompt_payload = self._tensor_to_base64_data_uri(input_image_prompt_socket)

        if model_choice == "FLUX 1.1 Pro Ultra":
            if actual_image_prompt_payload: 
                payload["image_prompt"] = actual_image_prompt_payload
            payload["image_prompt_strength"] = image_prompt_strength
            if aspect_ratio != self.INPUT_TYPES()["optional"]["aspect_ratio"][1]["default"]: 
                 payload["aspect_ratio"] = aspect_ratio
            payload["raw"] = raw
        elif model_choice in ["FLUX 1.1 Pro", "FLUX Pro Canny"]:
            if actual_image_prompt_payload: 
                payload["image_prompt"] = actual_image_prompt_payload
            payload["steps"] = steps
            payload["height"] = height
            payload["width"] = width
        elif model_choice in ["FLUX Dev", "FLUX Schnell"]:
            payload["steps"] = steps
            payload["height"] = height
            payload["width"] = width

        if model_choice in ["FLUX 1.1 Pro", "FLUX Pro Canny", "FLUX Dev", "FLUX Schnell"]:
            if height % 32 != 0: raise ValueError(f"Height must be a multiple of 32. Got {height}.")
            if width % 32 != 0: raise ValueError(f"Width must be a multiple of 32. Got {width}.")

        return self._make_api_call(payload, api_url, api_key, response_format, output_format, seed)

class Leon_Flux_Kontext_API_Node(HyprLabImageGenerationNodeBase):
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "image_url", "seed")
    FUNCTION = "generate_flux_kontext_image"

    MODEL_CHOICES = ["flux-kontext-max", "flux-kontext-pro"]
    ASPECT_RATIO_CHOICES = [
        "match_input_image", "1:1", "16:9", "9:16", "4:3", "3:4", 
        "3:2", "2:3", "4:5", "5:4", "21:9", "9:21", "2:1", "1:2"
    ]

    def __init__(self):
        super().__init__()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": (cls.MODEL_CHOICES, {"default": "flux-kontext-pro"}),
                "prompt": ("STRING", {"multiline": True, "default": "A detailed artistic scene"}),
                "response_format": (["url", "b64_json"], {"default": "url"}),
                "output_format": (["png", "jpeg", "webp"], {"default": "png"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/images/generations"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_HYPRLAB_API_KEY"}),
            },
            "optional": {
                "input_image": ("IMAGE",),
                "aspect_ratio": (cls.ASPECT_RATIO_CHOICES, {"default": "1:1"}),
            }
        }

    def generate_flux_kontext_image(self, model, prompt, response_format, output_format, seed, 
                                      api_url, api_key, input_image=None, aspect_ratio="1:1"):

        if not prompt.strip():
            raise ValueError("Prompt must be a non-empty string.")

        payload = {
            "model": model,
            "prompt": prompt,
            "response_format": response_format,
            "output_format": output_format,
        }

        if input_image is not None:
            base64_data_uri = self._tensor_to_base64_data_uri(input_image)
            if base64_data_uri:
                payload["input_image"] = base64_data_uri
        
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
            if input_image is None and aspect_ratio == "match_input_image":
                 pass

        return self._make_api_call(payload, api_url, api_key, response_format, output_format, seed)

API_NODE_CLASS_MAPPINGS = {
    "Leon_Google_Image_API_Node": Leon_Google_Image_API_Node,
    "Leon_Luma_AI_Image_API_Node": Leon_Luma_AI_Image_API_Node,
    # "Leon_Midjourney_Proxy_API_Node": Leon_Midjourney_Proxy_API_Node, # Removed
    "Leon_Flux_Image_API_Node": Leon_Flux_Image_API_Node,
    "Leon_Flux_Kontext_API_Node": Leon_Flux_Kontext_API_Node,
}

API_NODE_DISPLAY_NAME_MAPPINGS = {
    "Leon_Google_Image_API_Node": "🤖 Leon Google Image API",
    "Leon_Luma_AI_Image_API_Node": "🤖 Leon Luma AI Image API",
    # "Leon_Midjourney_Proxy_API_Node": "🤖 Leon Midjourney Proxy API", # Removed
    "Leon_Flux_Image_API_Node": "🤖 Leon FLUX Image API",
    "Leon_Flux_Kontext_API_Node": "🤖 Leon FLUX Kontext API",
} 