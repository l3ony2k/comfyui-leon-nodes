import tenacity
from openai import OpenAI
import random
import base64
from PIL import Image
import os
import io
import torch
import numpy as np
import tempfile
import requests
import json
import time


def validate_and_cast_response(response):
    """Validate raw JSON response and convert to tensor format"""
    data = response.data
    if not data or len(data) == 0:
        raise Exception("No images returned from API endpoint")

    # Initialize list to store image tensors
    image_tensors = []

    # Process each image in the data array
    for image_data in data:
        image_url = image_data.url
        b64_data = image_data.b64_json

        if not image_url and not b64_data:
            raise Exception("No image was generated in the response")

        if b64_data:
            img_data = base64.b64decode(b64_data)
            img = Image.open(io.BytesIO(img_data))

        elif image_url:
            img_response = requests.get(image_url)
            if img_response.status_code != 200:
                raise Exception("Failed to download the image")
            img = Image.open(io.BytesIO(img_response.content))

        img = img.convert("RGBA")

        # Convert to numpy array, normalize to float32 between 0 and 1
        img_array = np.array(img).astype(np.float32) / 255.0
        img_tensor = torch.from_numpy(img_array)

        # Add to list of tensors
        image_tensors.append(img_tensor)

    return torch.stack(image_tensors, dim=0)


# Base class for HyprLab Image Generation Nodes
class HyprLabImageGenerationNodeBase:
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "image_url", "seed")

    # Common API call and response processing logic
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
            # For Luma, prompt is required according to docs, but let's be a bit flexible if other params are present
            # For Google Imagen, prompt is strictly required. This check should ideally be in the specific node's method.
            # For now, we'll assume prompt is generally needed or other refs exist.
            pass

        random.seed(seed)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        try:
            response = requests.post(api_url.rstrip('/'), json=payload, headers=headers) # api_url is already full path
            
            print(f"API Request URL: {api_url.rstrip('/')}")
            print(f"API Request Payload: {json.dumps(payload)}")
            print(f"HTTP status: {response.status_code}")
            # Limit printing large base64 responses
            response_text_to_print = response.text
            if "b64_json" in response_text_to_print and len(response_text_to_print) > 1000:
                response_text_to_print = response_text_to_print[:500] + "... (response truncated)"
            print(f"Response: {response_text_to_print}")
            
            response.raise_for_status()
            response_json = response.json()

            pil_img = None
            actual_image_url = "" # To store URL from API or data URI

            if response_format == "b64_json":
                b64_data = response_json["data"][0]["b64_json"]
                img_data = base64.b64decode(b64_data)
                pil_img = Image.open(io.BytesIO(img_data))
                actual_image_url = f"data:image/{output_format};base64,{b64_data}"
            else:  # "url" format
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


class Leon_Google_Image_API_Node(HyprLabImageGenerationNodeBase):
    """
    A ComfyUI node for generating images using Google's Imagen models via HyprLab API.
    Supports imagen-4, imagen-3, and imagen-3-fast models.
    """

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
                "model": (["imagen-4", "imagen-3", "imagen-3-fast"], {"default": "imagen-4", "tooltip": "Google Imagen model to use for generation"}),
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
            # Google Imagen API doesn't use seed in payload directly via HyprLab in this way
        }
        
        return self._make_api_call(payload, api_url, api_key, response_format, output_format, seed)


class Leon_Luma_AI_Image_API_Node(HyprLabImageGenerationNodeBase):
    """
    A ComfyUI node for generating images using Luma AI models (photon, photon-flash) via HyprLab API.
    """
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
                "image_reference_url": ("STRING", {"multiline": False, "default": "", "tooltip": "URL, Data URI, or base64 string for an image to be used as a reference."}),
                "image_reference_weight": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01, "tooltip": "Influence of the image_reference_url (0 to 1)."}),
                "style_reference_url": ("STRING", {"multiline": False, "default": "", "tooltip": "URL, Data URI, or base64 string for an image whose style will be referenced."}),
                "style_reference_weight": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01, "tooltip": "Influence of the style_reference_url (0 to 1)."}),
                "character_reference_url": ("STRING", {"multiline": False, "default": "", "tooltip": "URL, Data URI, or base64 string for an image whose character features will be referenced."}),
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
        image_reference_url="",
        image_reference_weight=0.5,
        style_reference_url="",
        style_reference_weight=0.5,
        character_reference_url=""
    ):
        if len(prompt) > 10000:
            raise ValueError("Prompt must not exceed 10,000 characters")
        if not prompt.strip() and not image_reference_url.strip() and not style_reference_url.strip() and not character_reference_url.strip():
             raise ValueError("Prompt is required for Luma AI, or at least one reference URL must be provided.")

        payload = {
            "model": model,
            "prompt": prompt,
            "response_format": response_format,
            "output_format": output_format
        }

        # Always add aspect_ratio as it's a selection with a default value in the UI.
        if aspect_ratio: # This will always be true since aspect_ratio is a dropdown choice
             payload["aspect_ratio"] = aspect_ratio
        
        if image_reference_url.strip():
            payload["image_reference_url"] = image_reference_url.strip()
            payload["image_reference_weight"] = image_reference_weight
        
        if style_reference_url.strip():
            payload["style_reference_url"] = style_reference_url.strip()
            payload["style_reference_weight"] = style_reference_weight

        if character_reference_url.strip():
            payload["character_reference_url"] = character_reference_url.strip()
            # No corresponding weight for character_reference_url in HyprLab's Luma docs example

        return self._make_api_call(payload, api_url, api_key, response_format, output_format, seed)


class Leon_Midjourney_Proxy_API_Node:
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("image", "image_url", "task_id", "final_prompt_from_api", "message_hash")

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mj_proxy_endpoint": ("STRING", {
                    "multiline": False,
                    "default": "http://localhost:8080", # Your example endpoint
                    "tooltip": "Base URL of your Midjourney Proxy (e.g., http://localhost:8080)"
                }),
                "mj_api_secret": ("STRING", {
                    "multiline": False,
                    "default": "sk-midjourney", 
                    "tooltip": "Your mj-api-secret for the proxy"
                }),
                "x_api_key": ("STRING", {
                    "multiline": False,
                    "default": "sk-midjourneyke", 
                    "tooltip": "Your X-Api-Key for the proxy (if different from mj-api-secret)"
                }),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "dog playing ball --v 7 --ar 1:1"
                }),
                "bot_type": (["MID_JOURNEY", "NIJI_JOURNEY"], { # Ensure casing matches API
                    "default": "MID_JOURNEY"
                }),
                "polling_interval_seconds": ("INT", {
                    "default": 5, "min": 1, "max": 60,
                    "tooltip": "How often to check task status (seconds)"
                }),
                "max_polling_attempts": ("INT", {
                    "default": 30, "min": 1, "max": 120, # Increased default for potentially longer MJ tasks
                    "tooltip": "Max attempts to poll for result before timeout"
                }),
            },
            "optional": {
                "account_filter_remark": ("STRING", {
                    "multiline": False,
                    "default": "", # e.g., "lzn" from your example
                    "tooltip": "Optional: Remark for account filtering (e.g., lzn)"
                }),
                "base64_array_json": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "tooltip": "Optional: JSON string for base64Array, e.g., [\"data:image/png;base64,YOUR_BASE64\"]"
                }),
                "notify_hook": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "tooltip": "Optional: Webhook URL for notifications from the MJ proxy"
                })
            }
        }

    FUNCTION = "generate_mj_image"

    def _pil_to_rgba_tensor(self, pil_img):
        pil_img = pil_img.convert("RGBA")
        img_array = np.array(pil_img).astype(np.float32) / 255.0
        if img_array.ndim == 3 and img_array.shape[-1] == 3:
            alpha_channel = np.ones_like(img_array[..., :1])
            img_array = np.concatenate((img_array, alpha_channel), axis=-1)
        return torch.from_numpy(img_array).unsqueeze(0)

    def generate_mj_image(self, mj_proxy_endpoint, mj_api_secret, x_api_key, prompt, bot_type, 
                          polling_interval_seconds, max_polling_attempts, 
                          account_filter_remark="", base64_array_json="", notify_hook=""):
        
        submit_url = f"{mj_proxy_endpoint.rstrip('/')}/mj/submit/imagine"
        
        headers = {
            'Content-Type': 'application/json',
            'mj-api-secret': mj_api_secret,
            'X-Api-Key': x_api_key
        }
        
        payload = {
            "prompt": prompt,
            "botType": bot_type # Ensure this casing matches what your API expects (e.g. MID_JOURNEY)
        }

        if account_filter_remark.strip():
            payload["accountFilter"] = {"remark": account_filter_remark.strip()}
        
        if base64_array_json.strip():
            try:
                payload["base64Array"] = json.loads(base64_array_json)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in base64_array_json: {str(e)}. Expected format e.g., [\"data:image/png;base64,YOUR_BASE64\"]")
        
        if notify_hook.strip():
            payload["notifyHook"] = notify_hook.strip()

        print(f"MJ Proxy: Submitting to {submit_url}")
        print(f"MJ Proxy: Headers: {json.dumps({k: (v if k != 'mj-api-secret' and k != 'X-Api-Key' else '***') for k, v in headers.items()})}") # Avoid logging secrets
        print(f"MJ Proxy: Payload: {json.dumps(payload)}")

        try:
            response = requests.post(submit_url, json=payload, headers=headers)
            response.raise_for_status()
            submit_response_json = response.json()
            print(f"MJ Proxy: Submit Response: {json.dumps(submit_response_json)}")
        except requests.exceptions.RequestException as e:
            response_text = e.response.text if e.response else "No response text"
            raise Exception(f"Midjourney task submission failed (RequestException): {str(e)}, Response: {response_text}")
        except Exception as e:
            raise Exception(f"Midjourney task submission failed (Other Exception): {str(e)}, Response: {response.text if 'response' in locals() else 'No response object'}")

        if submit_response_json.get("code") != 1:
            raise Exception(f"Midjourney task submission error: {submit_response_json.get('description', 'Unknown error from proxy')}, Code: {submit_response_json.get('code')}")
        
        task_id = submit_response_json.get("result")
        if not task_id:
            raise Exception("Midjourney task submission response did not include a task ID (result field).")
        
        print(f"MJ Proxy: Task {task_id} submitted. Polling for result...")

        fetch_url = f"{mj_proxy_endpoint.rstrip('/')}/mj/task/{task_id}/fetch"
        
        for attempt in range(max_polling_attempts):
            print(f"MJ Proxy: Polling attempt {attempt + 1}/{max_polling_attempts} for task {task_id} at {fetch_url}")
            try:
                fetch_response = requests.get(fetch_url, headers=headers) # Use same headers for fetch
                fetch_response.raise_for_status()
                task_data = fetch_response.json()
            except requests.exceptions.RequestException as e:
                response_text = e.response.text if e.response else "No response text"
                print(f"MJ Proxy: Polling attempt failed (RequestException): {str(e)}, Response: {response_text}. Retrying in {polling_interval_seconds}s...")
                time.sleep(polling_interval_seconds)
                continue
            except Exception as e:
                print(f"MJ Proxy: Polling attempt failed (Other Exception): {str(e)}. Retrying in {polling_interval_seconds}s...")
                time.sleep(polling_interval_seconds)
                continue

            status = task_data.get("status")
            image_url = task_data.get("imageUrl")
            progress = task_data.get("progress", "N/A")
            fail_reason = task_data.get("failReason")
            final_prompt_from_api = task_data.get("finalPrompt", task_data.get("promptEn", prompt)) # Get final prompt, fallback to original
            message_hash = task_data.get("properties", {}).get("messageHash", task_data.get("messageHash", ""))

            print(f"MJ Proxy: Task {task_id} status: {status}, Progress: {progress}, Final Prompt: {final_prompt_from_api}, Hash: {message_hash}")

            if status == "SUCCESS":
                if not image_url:
                    raise Exception(f"Midjourney task {task_id} Succeeded but no imageUrl found in response: {json.dumps(task_data)}")
                
                print(f"MJ Proxy: Task {task_id} successful. Image URL: {image_url}")
                try:
                    img_download_response = requests.get(image_url) # No special headers needed for discord cdn typically
                    img_download_response.raise_for_status()
                    pil_img = Image.open(io.BytesIO(img_download_response.content))
                    img_tensor = self._pil_to_rgba_tensor(pil_img)
                    return (img_tensor, image_url, task_id, final_prompt_from_api, message_hash)
                except Exception as e:
                    raise Exception(f"Failed to download or process image from {image_url}: {str(e)}")

            elif status == "FAILURE":
                raise Exception(f"Midjourney task {task_id} failed: {fail_reason or 'Unknown reason'}. Full task data: {json.dumps(task_data)}")
            elif status == "MODAL":
                 raise Exception(f"Midjourney task {task_id} is in MODAL state. This node does not support modal interactions. Full task data: {json.dumps(task_data)}")

            if attempt < max_polling_attempts - 1:
                time.sleep(polling_interval_seconds)
            else:
                raise Exception(f"Midjourney task {task_id} timed out after {max_polling_attempts * polling_interval_seconds} seconds. Last status: {status}, Progress: {progress}. Full task data: {json.dumps(task_data)}")
        
        raise Exception("Midjourney polling finished unexpectedly (should have returned or raised an error within the loop).")


class Leon_Image_Split_4Grid_Node:
    CATEGORY = "Leon_Utils" # Changed category
    RETURN_TYPES = ("IMAGE", "IMAGE", "IMAGE", "IMAGE")
    RETURN_NAMES = ("image_TL", "image_TR", "image_BL", "image_BR")
    FUNCTION = "split_image_grid"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",), # Input image
            }
        }

    def _tensor_to_pil(self, tensor_image):
        # Assuming tensor_image is (B, H, W, C) and we take the first image if batched
        if tensor_image.ndim == 4:
            tensor_image = tensor_image[0]
        # Convert CHW to HWC if needed (though ComfyUI IMAGE is usually HWC)
        # tensor_image = tensor_image.permute(1, 2, 0) # If CHW
        np_image = (tensor_image.cpu().numpy() * 255).astype(np.uint8)
        pil_image = Image.fromarray(np_image, 'RGBA' if np_image.shape[-1] == 4 else 'RGB')
        return pil_image

    def _pil_to_rgba_tensor(self, pil_img):
        pil_img = pil_img.convert("RGBA")
        img_array = np.array(pil_img).astype(np.float32) / 255.0
        if img_array.ndim == 3 and img_array.shape[-1] == 3:
            alpha_channel = np.ones_like(img_array[..., :1])
            img_array = np.concatenate((img_array, alpha_channel), axis=-1)
        return torch.from_numpy(img_array).unsqueeze(0)

    def split_image_grid(self, image):
        if image is None:
            raise ValueError("Input image cannot be None for splitting.")
        
        pil_image = self._tensor_to_pil(image)
        pil_image = pil_image.convert("RGBA") # Ensure it's RGBA before processing

        width, height = pil_image.size
        mid_w, mid_h = width // 2, height // 2

        # Define crop boxes (left, upper, right, lower)
        box_tl = (0, 0, mid_w, mid_h)
        box_tr = (mid_w, 0, width, mid_h)
        box_bl = (0, mid_h, mid_w, height)
        box_br = (mid_w, mid_h, width, height)

        img_tl = pil_image.crop(box_tl)
        img_tr = pil_image.crop(box_tr)
        img_bl = pil_image.crop(box_bl)
        img_br = pil_image.crop(box_br)

        tensor_tl = self._pil_to_rgba_tensor(img_tl)
        tensor_tr = self._pil_to_rgba_tensor(img_tr)
        tensor_bl = self._pil_to_rgba_tensor(img_bl)
        tensor_br = self._pil_to_rgba_tensor(img_br)

        return (tensor_tl, tensor_tr, tensor_bl, tensor_br)


class Leon_String_Combine_Node:
    CATEGORY = "Leon_Utils" # Changed category
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("combined_string",)
    FUNCTION = "combine_strings"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "string_1": ("STRING", {"multiline": False, "default": ""}),
                "string_2": ("STRING", {"multiline": False, "default": ""}),
                "linking_element": ("STRING", {"multiline": False, "default": ""})
            }
        }

    def combine_strings(self, string_1, string_2, linking_element):
        return (f"{string_1}{linking_element}{string_2}",)


class Leon_ImgBB_Upload_Node:
    CATEGORY = "Leon_Utils"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("image_url",)
    FUNCTION = "upload_to_imgbb"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "api_key": ("STRING", {"default": "", "multiline": False, "tooltip": "Your ImgBB API key"}),
            },
            "optional": {
                "expire": ("BOOLEAN", {"default": False, "tooltip": "Set to True to make the image expire"}),
                "expiration_time_seconds": (
                    "INT",
                    {"default": 3600, "min": 60, "max": 15552000, "step": 1, "tooltip": "Expiration time in seconds (e.g., 3600 for 1 hour). Only used if expire is True."},
                ),
            }
        }

    def _tensor_to_pil(self, tensor_image):
        # Assuming tensor_image is (B, H, W, C) and we take the first image if batched
        if tensor_image.ndim == 4:
            tensor_image = tensor_image[0]
        np_image = (tensor_image.cpu().numpy() * 255).astype(np.uint8)
        # Ensure image is RGB for PNG saving if it's RGBA (ImgBB might handle alpha, but being explicit is safer for general uploads)
        # However, saving as PNG with alpha is fine.
        pil_image = Image.fromarray(np_image, 'RGBA' if np_image.shape[-1] == 4 else 'RGB')
        return pil_image

    def upload_to_imgbb(self, image, api_key, expire=False, expiration_time_seconds=3600):
        """
        Upload an image to ImgBB and return the URL.
        """
        if not api_key or not api_key.strip():
            raise ValueError("ImgBB API Key is required and cannot be empty.")

        pil_image = self._tensor_to_pil(image)

        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG") # Save as PNG
        buffer.seek(0)

        base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

        url = f"https://api.imgbb.com/1/upload?key={api_key}"
        if expire:
            # ImgBB API expects expiration in seconds, min 60, max 15552000 (6 months)
            # The input field already has these constraints.
            url += f"&expiration={expiration_time_seconds}"

        payload = {
            "image": base64_image,
        }

        print(f"ImgBB Upload: Posting to {url.split('?key=')[0]}?key=YOUR_API_KEY...") # Don't log key in URL
        # print(f"ImgBB Upload: Payload keys: {payload.keys()}") # image key is present

        try:
            response = requests.post(url, data=payload)
            response.raise_for_status() # Will raise HTTPError for bad responses (4xx or 5xx)
            result = response.json()

            # Debugging the response structure
            # print(f"ImgBB Raw Response: {result}")

            if result.get("success") and result.get("data") and result["data"].get("url"):
                return (result["data"]["url"],)
            else:
                error_message = "Unknown error"
                if result.get("error"):
                    if isinstance(result["error"], dict):
                        error_message = result["error"].get("message", "Unknown error from API dictionary")
                    else: # Sometimes error might be a string
                        error_message = str(result["error"])
                elif result.get("status_txt"):
                     error_message = result.get("status_txt")
                
                status_code = result.get("status_code", response.status_code)
                raise ValueError(f"ImgBB API Error (Code: {status_code}): {error_message}. Full response: {json.dumps(result)}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"ImgBB upload request failed: {str(e)}")
        except Exception as e:
            # Catch any other exception, including JSONDecodeError if response is not JSON
            raise ValueError(f"ImgBB upload error: {str(e)}. Response text (if available): {response.text if 'response' in locals() else 'N/A'}")


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
        pass

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
                "image_prompt": ("STRING", {"multiline": False, "default": "", "tooltip": "URL for image guidance (FLUX 1.1 Pro Ultra, FLUX 1.1 Pro, FLUX Pro Canny)"}),
                "image_prompt_strength": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01, "tooltip": "Strength of image_prompt (FLUX 1.1 Pro Ultra only)"}),
                "aspect_ratio": (cls.ASPECT_RATIOS_ULTRA, {"default": "1:1", "tooltip": "Aspect ratio (FLUX 1.1 Pro Ultra only)"}),
                "raw": ("BOOLEAN", {"default": False, "tooltip": "Return raw output (FLUX 1.1 Pro Ultra only)"}),
                "steps": ("INT", {"default": 20, "min": 1, "max": 50, "tooltip": "Number of steps (FLUX 1.1 Pro, FLUX Pro Canny, FLUX Dev, FLUX Schnell)"}),
                "height": ("INT", {"default": 1024, "min": 256, "max": 1440, "step": 32, "tooltip": "Image height, multiple of 32 (FLUX 1.1 Pro, FLUX Pro Canny, FLUX Dev, FLUX Schnell)"}),
                "width": ("INT", {"default": 1024, "min": 256, "max": 1440, "step": 32, "tooltip": "Image width, multiple of 32 (FLUX 1.1 Pro, FLUX Pro Canny, FLUX Dev, FLUX Schnell)"}),
            }
        }

    def generate_flux_image(self, model_choice, prompt, response_format, output_format, seed, api_url, api_key,
                              image_prompt="", image_prompt_strength=0.5, aspect_ratio="1:1", raw=False,
                              steps=20, height=1024, width=1024):

        actual_model_name = self.MODEL_MAPPING.get(model_choice)
        if not actual_model_name:
            raise ValueError(f"Invalid model choice: {model_choice}. Available: {list(self.MODEL_MAPPING.keys())}")

        payload = {
            "model": actual_model_name,
            "prompt": prompt,
            "response_format": response_format,
            "output_format": output_format,
        }

        if not prompt.strip():
            raise ValueError("Prompt must be a non-empty string.")

        # Parameters for FLUX 1.1 Pro Ultra
        if model_choice == "FLUX 1.1 Pro Ultra":
            if image_prompt.strip():
                payload["image_prompt"] = image_prompt.strip()
            payload["image_prompt_strength"] = image_prompt_strength
            if aspect_ratio != self.INPUT_TYPES()["optional"]["aspect_ratio"]["default"]:
                 payload["aspect_ratio"] = aspect_ratio
            payload["raw"] = raw

        # Parameters for FLUX 1.1 Pro or FLUX Pro Canny
        elif model_choice in ["FLUX 1.1 Pro", "FLUX Pro Canny"]:
            if image_prompt.strip():
                payload["image_prompt"] = image_prompt.strip()
            payload["steps"] = steps
            payload["height"] = height
            payload["width"] = width

        # Parameters for FLUX Dev or FLUX Schnell
        elif model_choice in ["FLUX Dev", "FLUX Schnell"]:
            payload["steps"] = steps
            payload["height"] = height
            payload["width"] = width

        # Validate height and width being multiples of 32 for relevant models
        if model_choice in ["FLUX 1.1 Pro", "FLUX Pro Canny", "FLUX Dev", "FLUX Schnell"]:
            if height % 32 != 0:
                raise ValueError(f"Height must be a multiple of 32 for {model_choice}. Got {height}.")
            if width % 32 != 0:
                raise ValueError(f"Width must be a multiple of 32 for {model_choice}. Got {width}.")

        return self._make_api_call(payload, api_url, api_key, response_format, output_format, seed)


# Node class mappings for ComfyUI discovery
NODE_CLASS_MAPPINGS = {
    "Leon_Google_Image_API_Node": Leon_Google_Image_API_Node,
    "Leon_Luma_AI_Image_API_Node": Leon_Luma_AI_Image_API_Node,
    "Leon_Midjourney_Proxy_API_Node": Leon_Midjourney_Proxy_API_Node,
    "Leon_Image_Split_4Grid_Node": Leon_Image_Split_4Grid_Node,
    "Leon_String_Combine_Node": Leon_String_Combine_Node,
    "Leon_Flux_Image_API_Node": Leon_Flux_Image_API_Node,
    "Leon_ImgBB_Upload_Node": Leon_ImgBB_Upload_Node,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Leon_Google_Image_API_Node": "Leon Google Image API",
    "Leon_Luma_AI_Image_API_Node": "Leon Luma AI Image API",
    "Leon_Midjourney_Proxy_API_Node": "Leon Midjourney Proxy API",
    "Leon_Image_Split_4Grid_Node": "Leon Image Split 4-Grid",
    "Leon_String_Combine_Node": "Leon String Combine",
    "Leon_Flux_Image_API_Node": "Leon FLUX Image API",
    "Leon_ImgBB_Upload_Node": "Leon ImgBB Upload",
} 