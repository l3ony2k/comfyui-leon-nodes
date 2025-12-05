import torch
import numpy as np
from PIL import Image
import io
import json
import time
import requests # Ensure requests is imported if not already via other means

# Note: Specific imports like base64 might be needed if Leon_Midjourney_Proxy_API_Node uses them directly
# and they are not covered by the common imports above.
# For now, assuming the standard set (torch, numpy, PIL, io, json, time, requests) covers most needs.
# If base64 is used by Midjourney node specifically and not by others, it should be here.
import base64 # Leon_Midjourney_Proxy_API_Node uses json.loads for base64_array_json, but not direct base64 ops.
             # However, it might be good practice to keep it if similar ops are added later.
             # More critically, the original file had it at the top.

class Leon_Midjourney_Proxy_API_Node:
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("image", "image_url", "task_id", "final_prompt_from_api", "message_hash")
    FUNCTION = "generate_mj_image"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mj_proxy_endpoint": ("STRING", {"multiline": False, "default": "http://localhost:8080", "tooltip": "Base URL of your Midjourney Proxy (e.g., http://localhost:8080)"}),
                "api_key": ("STRING", {"multiline": False, "default": "sk-midjourney", "tooltip": "Your API key for the proxy (used for both mj-api-secret and X-Api-Key headers)"}),
                "prompt": ("STRING", {"multiline": True, "default": "dog playing ball --v 7 --ar 1:1"}),
                "bot_type": (["MID_JOURNEY", "NIJI_JOURNEY"], {"default": "MID_JOURNEY"}),
                "polling_interval_seconds": ("INT", {"default": 5, "min": 1, "max": 60, "tooltip": "How often to check task status (seconds)"}),
                "max_polling_attempts": ("INT", {"default": 30, "min": 1, "max": 120, "tooltip": "Max attempts to poll for result before timeout"}),
            },
            "optional": {
                "account_filter_remark": ("STRING", {"multiline": False, "default": "", "tooltip": "Optional: Remark for account filtering (e.g., lzn)"}),
                "base64_array_json": ("STRING", {"multiline": True, "default": "", "tooltip": "Optional: JSON string for base64Array, e.g., [\"data:image/png;base64,YOUR_BASE64\"]"}),
            }
        }

    def _pil_to_rgba_tensor(self, pil_img):
        pil_img = pil_img.convert("RGBA")
        img_array = np.array(pil_img).astype(np.float32) / 255.0
        if img_array.ndim == 3 and img_array.shape[-1] == 3:
            alpha_channel = np.ones_like(img_array[..., :1])
            img_array = np.concatenate((img_array, alpha_channel), axis=-1)
        return torch.from_numpy(img_array).unsqueeze(0)

    def generate_mj_image(self, mj_proxy_endpoint, api_key, prompt, bot_type, 
                          polling_interval_seconds, max_polling_attempts, 
                          account_filter_remark="", base64_array_json=""):
        
        submit_url = f"{mj_proxy_endpoint.rstrip('/')}/mj/submit/imagine"
        headers = {'Content-Type': 'application/json', 'mj-api-secret': api_key, 'X-Api-Key': api_key}
        payload = {"prompt": prompt, "botType": bot_type}

        if account_filter_remark.strip():
            payload["accountFilter"] = {"remark": account_filter_remark.strip()}
        if base64_array_json.strip():
            try:
                payload["base64Array"] = json.loads(base64_array_json)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in base64_array_json: {str(e)}.")

        print(f"MJ Proxy: Submitting to {submit_url}")
        headers_to_print = {k: (v if k not in ['mj-api-secret', 'X-Api-Key'] else '***') for k, v in headers.items()}
        print(f"MJ Proxy: Headers: {json.dumps(headers_to_print)}")
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
            response_content = response.text if 'response' in locals() else 'No response object'
            raise Exception(f"Midjourney task submission failed (Other Exception): {str(e)}, Response: {response_content}")

        if submit_response_json.get("code") != 1:
            raise Exception(f"Midjourney task submission error: {submit_response_json.get('description', 'Unknown error')}, Code: {submit_response_json.get('code')}")
        
        task_id = submit_response_json.get("result")
        if not task_id:
            raise Exception("Midjourney task ID not found in submission response.")
        
        print(f"MJ Proxy: Task {task_id} submitted. Polling...")
        fetch_url = f"{mj_proxy_endpoint.rstrip('/')}/mj/task/{task_id}/fetch"
        
        for attempt in range(max_polling_attempts):
            print(f"MJ Proxy: Polling attempt {attempt + 1}/{max_polling_attempts} for task {task_id}")
            try:
                fetch_response = requests.get(fetch_url, headers=headers)
                fetch_response.raise_for_status()
                task_data = fetch_response.json()
            except requests.exceptions.RequestException as e:
                print(f"MJ Proxy: Polling failed (RequestException): {str(e)}. Retrying...")
                time.sleep(polling_interval_seconds)
                continue
            except Exception as e:
                print(f"MJ Proxy: Polling failed (Other Exception): {str(e)}. Retrying...")
                time.sleep(polling_interval_seconds)
                continue

            status = task_data.get("status")
            image_url = task_data.get("imageUrl")
            final_prompt_from_api = task_data.get("finalPrompt", task_data.get("promptEn", prompt))
            message_hash = task_data.get("properties", {}).get("messageHash", task_data.get("messageHash", ""))

            print(f"MJ Proxy: Task {task_id} status: {status}, Progress: {task_data.get('progress', 'N/A')}")

            if status == "SUCCESS":
                if not image_url:
                    raise Exception(f"Midjourney task {task_id} Succeeded but no imageUrl found.")
                img_download_response = requests.get(image_url)
                img_download_response.raise_for_status()
                pil_img = Image.open(io.BytesIO(img_download_response.content))
                img_tensor = self._pil_to_rgba_tensor(pil_img)
                return (img_tensor, image_url, task_id, final_prompt_from_api, message_hash)
            elif status == "FAILURE":
                raise Exception(f"Midjourney task {task_id} failed: {task_data.get('failReason', 'Unknown reason')}.")
            elif status == "MODAL":
                 raise Exception(f"Midjourney task {task_id} is in MODAL state.")

            if attempt < max_polling_attempts - 1:
                time.sleep(polling_interval_seconds)
            else:
                raise Exception(f"Midjourney task {task_id} timed out. Last status: {status}.")
        
        raise Exception("Midjourney polling loop finished unexpectedly.")


class Leon_Midjourney_Describe_API_Node:
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("description_1", "description_2", "description_3", "description_4", "task_id", "image_url")
    FUNCTION = "describe_mj_image"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mj_proxy_endpoint": ("STRING", {"multiline": False, "default": "http://localhost:8080", "tooltip": "Base URL of your Midjourney Proxy (e.g., http://localhost:8080)"}),
                "api_key": ("STRING", {"multiline": False, "default": "sk-midjourney", "tooltip": "Your API key for the proxy (used for both mj-api-secret and X-Api-Key headers)"}),
                "bot_type": (["MID_JOURNEY", "NIJI_JOURNEY"], {"default": "MID_JOURNEY"}),
                "polling_interval_seconds": ("INT", {"default": 5, "min": 1, "max": 60, "tooltip": "How often to check task status (seconds)"}),
                "max_polling_attempts": ("INT", {"default": 30, "min": 1, "max": 120, "tooltip": "Max attempts to poll for result before timeout"}),
            },
            "optional": {
                "image": ("IMAGE", {"tooltip": "Input image to describe"}),
                "image_url": ("STRING", {"multiline": False, "default": "", "tooltip": "Optional hosted image URL to describe (use instead of socket input)"}),
                "account_filter_remark": ("STRING", {"multiline": False, "default": "", "tooltip": "Optional: Remark for account filtering (e.g., lzn)"}),
            }
        }

    def _tensor_to_base64(self, image_tensor):
        """Convert ComfyUI image tensor to base64 string."""
        # Convert tensor to PIL Image
        # Tensor shape: (batch, height, width, channels)
        if len(image_tensor.shape) == 4:
            image_tensor = image_tensor[0]  # Take first image from batch
        
        # Convert from 0-1 range to 0-255
        if image_tensor.max() <= 1.0:
            image_tensor = image_tensor * 255.0
        
        # Convert to numpy array and ensure it's uint8
        img_array = image_tensor.cpu().numpy().astype(np.uint8)
        
        # Create PIL image
        if img_array.shape[-1] == 4:  # RGBA
            pil_img = Image.fromarray(img_array, 'RGBA')
        elif img_array.shape[-1] == 3:  # RGB
            pil_img = Image.fromarray(img_array, 'RGB')
        else:
            raise ValueError(f"Unsupported image shape: {img_array.shape}")
        
        # Convert to JPEG format for base64 encoding
        buffer = io.BytesIO()
        pil_img.convert('RGB').save(buffer, format='JPEG', quality=95)
        buffer.seek(0)
        
        # Encode to base64
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/jpeg;base64,{img_base64}"

    def _resolve_image_input(self, image_tensor, image_url="", field_name="image"):
        """Prefer an explicit URL when provided, otherwise convert the tensor to base64."""
        url = (image_url or "").strip()
        if image_tensor is not None and url:
            raise ValueError(f"{field_name}: provide either an image tensor or an image URL, not both.")
        if url:
            return url
        if image_tensor is not None:
            return self._tensor_to_base64(image_tensor)
        return None

    def _parse_descriptions(self, prompt_text):
        """Parse the prompt text and extract 4 descriptions."""
        if not prompt_text:
            return ("", "", "", "")
        
        # Split by double newlines
        parts = prompt_text.split('\n\n')
        
        descriptions = []
        for part in parts:
            part = part.strip()
            if part:
                # Remove the emoji and number prefix (e.g., "1️⃣ ")
                if len(part) > 3 and part[0] in ['1', '2', '3', '4'] and '️⃣' in part[:5]:
                    # Find the space after the emoji and number
                    space_idx = part.find(' ', 3)
                    if space_idx != -1:
                        part = part[space_idx + 1:]
                descriptions.append(part.strip())
        
        # Ensure we have exactly 4 descriptions, pad with empty strings if needed
        while len(descriptions) < 4:
            descriptions.append("")
        
        return tuple(descriptions[:4])

    def describe_mj_image(self, mj_proxy_endpoint, api_key, bot_type,
                          polling_interval_seconds, max_polling_attempts,
                          image=None, image_url="", account_filter_remark=""):
        
        image_payload_value = self._resolve_image_input(image, image_url, field_name="image")
        if not image_payload_value:
            raise ValueError("An image tensor or image URL must be provided for Midjourney describe.")
        
        submit_url = f"{mj_proxy_endpoint.rstrip('/')}/mj/submit/describe"
        headers = {'Content-Type': 'application/json', 'mj-api-secret': api_key, 'X-Api-Key': api_key}
        payload = {"botType": bot_type, "base64": image_payload_value}

        if account_filter_remark.strip():
            payload["accountFilter"] = {"remark": account_filter_remark.strip()}

        print(f"MJ Proxy: Submitting describe to {submit_url}")
        headers_to_print = {k: (v if k not in ['mj-api-secret', 'X-Api-Key'] else '***') for k, v in headers.items()}
        print(f"MJ Proxy: Headers: {json.dumps(headers_to_print)}")
        payload_to_print = {k: (v if k != 'base64' else f"data:image/jpeg;base64,[{len(v.split(',')[1]) if ',' in v else 0} chars]") for k, v in payload.items()}
        print(f"MJ Proxy: Payload: {json.dumps(payload_to_print)}")

        try:
            response = requests.post(submit_url, json=payload, headers=headers)
            response.raise_for_status()
            submit_response_json = response.json()
            print(f"MJ Proxy: Submit Response: {json.dumps(submit_response_json)}")
        except requests.exceptions.RequestException as e:
            response_text = e.response.text if e.response else "No response text"
            raise Exception(f"Midjourney describe submission failed (RequestException): {str(e)}, Response: {response_text}")
        except Exception as e:
            response_content = response.text if 'response' in locals() else 'No response object'
            raise Exception(f"Midjourney describe submission failed (Other Exception): {str(e)}, Response: {response_content}")

        if submit_response_json.get("code") != 1:
            raise Exception(f"Midjourney describe submission error: {submit_response_json.get('description', 'Unknown error')}, Code: {submit_response_json.get('code')}")
        
        task_id = submit_response_json.get("result")
        if not task_id:
            raise Exception("Midjourney describe task ID not found in submission response.")
        
        print(f"MJ Proxy: Describe task {task_id} submitted. Polling...")
        fetch_url = f"{mj_proxy_endpoint.rstrip('/')}/mj/task/{task_id}/fetch"
        
        for attempt in range(max_polling_attempts):
            print(f"MJ Proxy: Polling attempt {attempt + 1}/{max_polling_attempts} for describe task {task_id}")
            try:
                fetch_response = requests.get(fetch_url, headers=headers)
                fetch_response.raise_for_status()
                task_data = fetch_response.json()
            except requests.exceptions.RequestException as e:
                print(f"MJ Proxy: Polling failed (RequestException): {str(e)}. Retrying...")
                time.sleep(polling_interval_seconds)
                continue
            except Exception as e:
                print(f"MJ Proxy: Polling failed (Other Exception): {str(e)}. Retrying...")
                time.sleep(polling_interval_seconds)
                continue

            status = task_data.get("status")
            image_url = task_data.get("imageUrl", "")
            prompt_text = task_data.get("prompt", task_data.get("promptEn", ""))

            print(f"MJ Proxy: Describe task {task_id} status: {status}, Progress: {task_data.get('progress', 'N/A')}")

            if status == "SUCCESS":
                descriptions = self._parse_descriptions(prompt_text)
                return (*descriptions, task_id, image_url)
            elif status == "FAILURE":
                raise Exception(f"Midjourney describe task {task_id} failed: {task_data.get('failReason', 'Unknown reason')}.")
            elif status == "MODAL":
                raise Exception(f"Midjourney describe task {task_id} is in MODAL state.")

            if attempt < max_polling_attempts - 1:
                time.sleep(polling_interval_seconds)
            else:
                raise Exception(f"Midjourney describe task {task_id} timed out. Last status: {status}.")
        
        raise Exception("Midjourney describe polling loop finished unexpectedly.")


class Leon_Midjourney_Upload_API_Node:
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("image_url",)
    FUNCTION = "upload_mj_image"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mj_proxy_endpoint": ("STRING", {"multiline": False, "default": "http://localhost:8080", "tooltip": "Base URL of your Midjourney Proxy (e.g., http://localhost:8080)"}),
                "api_key": ("STRING", {"multiline": False, "default": "sk-midjourney", "tooltip": "Your API key for the proxy (used for both mj-api-secret and X-Api-Key headers)"}),
            },
            "optional": {
                "image": ("IMAGE", {"tooltip": "Input image to upload to Discord"}),
                "image_url": ("STRING", {"multiline": False, "default": "", "tooltip": "Optional hosted image URL to upload (use instead of socket input)"}),
                "account_filter_remark": ("STRING", {"multiline": False, "default": "", "tooltip": "Optional: Remark for account filtering (e.g., lzn)"}),
            }
        }

    def _tensor_to_base64(self, image_tensor):
        """Convert ComfyUI image tensor to base64 string."""
        # Convert tensor to PIL Image
        # Tensor shape: (batch, height, width, channels)
        if len(image_tensor.shape) == 4:
            image_tensor = image_tensor[0]  # Take first image from batch
        
        # Convert from 0-1 range to 0-255
        if image_tensor.max() <= 1.0:
            image_tensor = image_tensor * 255.0
        
        # Convert to numpy array and ensure it's uint8
        img_array = image_tensor.cpu().numpy().astype(np.uint8)
        
        # Create PIL image
        if img_array.shape[-1] == 4:  # RGBA
            pil_img = Image.fromarray(img_array, 'RGBA')
        elif img_array.shape[-1] == 3:  # RGB
            pil_img = Image.fromarray(img_array, 'RGB')
        else:
            raise ValueError(f"Unsupported image shape: {img_array.shape}")
        
        # Convert to JPEG format for base64 encoding
        buffer = io.BytesIO()
        pil_img.convert('RGB').save(buffer, format='JPEG', quality=95)
        buffer.seek(0)
        
        # Encode to base64
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/jpeg;base64,{img_base64}"

    def _resolve_image_input(self, image_tensor, image_url=""):
        url = (image_url or "").strip()
        if image_tensor is not None and url:
            raise ValueError("image: provide either an image tensor or an image URL, not both.")
        if url:
            return url
        if image_tensor is not None:
            return self._tensor_to_base64(image_tensor)
        return None

    def upload_mj_image(self, mj_proxy_endpoint, api_key, image=None, image_url="", account_filter_remark=""):
        image_payload_value = self._resolve_image_input(image, image_url)
        if not image_payload_value:
            raise ValueError("Provide an image tensor or an image URL for Midjourney upload.")
        
        submit_url = f"{mj_proxy_endpoint.rstrip('/')}/mj/submit/upload-discord-images"
        headers = {'Content-Type': 'application/json', 'mj-api-secret': api_key, 'X-Api-Key': api_key}
        payload = {"base64Array": [image_payload_value]}

        if account_filter_remark.strip():
            payload["filter"] = {"remark": account_filter_remark.strip()}

        print(f"MJ Proxy: Uploading image to {submit_url}")
        headers_to_print = {k: (v if k not in ['mj-api-secret', 'X-Api-Key'] else '***') for k, v in headers.items()}
        print(f"MJ Proxy: Headers: {json.dumps(headers_to_print)}")
        payload_to_print = {k: (v if k != 'base64Array' else f"[image base64 data: {len(v[0].split(',')[1]) if v and ',' in v[0] else 0} chars]") for k, v in payload.items()}
        print(f"MJ Proxy: Payload: {json.dumps(payload_to_print)}")

        try:
            response = requests.post(submit_url, json=payload, headers=headers)
            response.raise_for_status()
            upload_response_json = response.json()
            print(f"MJ Proxy: Upload Response: {json.dumps(upload_response_json)}")
        except requests.exceptions.RequestException as e:
            response_text = e.response.text if e.response else "No response text"
            raise Exception(f"Midjourney image upload failed (RequestException): {str(e)}, Response: {response_text}")
        except Exception as e:
            response_content = response.text if 'response' in locals() else 'No response object'
            raise Exception(f"Midjourney image upload failed (Other Exception): {str(e)}, Response: {response_content}")

        if upload_response_json.get("code") != 1:
            raise Exception(f"Midjourney image upload error: {upload_response_json.get('description', 'Unknown error')}, Code: {upload_response_json.get('code')}")
        
        result_urls = upload_response_json.get("result", [])
        if not result_urls or len(result_urls) == 0:
            raise Exception("No image URLs returned from upload response.")
        
        # Return the first (and only) uploaded image URL
        image_url = result_urls[0]
        print(f"MJ Proxy: Image uploaded successfully: {image_url}")
        
        return (image_url,)


MJ_PROXY_NODE_CLASS_MAPPINGS = {
    "Leon_Midjourney_Proxy_API_Node": Leon_Midjourney_Proxy_API_Node,
    "Leon_Midjourney_Describe_API_Node": Leon_Midjourney_Describe_API_Node,
    "Leon_Midjourney_Upload_API_Node": Leon_Midjourney_Upload_API_Node,
}

MJ_PROXY_NODE_DISPLAY_NAME_MAPPINGS = {
    "Leon_Midjourney_Proxy_API_Node": "🤖 Leon Midjourney API Generate",
    "Leon_Midjourney_Describe_API_Node": "🤖 Leon Midjourney API Describe",
    "Leon_Midjourney_Upload_API_Node": "🤖 Leon Midjourney API Upload",
} 
