import tenacity
import base64
from PIL import Image
import io
import requests
import json
import random
import torch
import numpy as np


# ===========================================================================
#  Google Official API Nodes – uses Google's native REST endpoint directly
#  (generativelanguage.googleapis.com) instead of OpenAI-compatible proxies.
# ===========================================================================

GOOGLE_API_BASE = "https://generativelanguage.googleapis.com/v1beta"

# ---- helpers shared by both nodes -----------------------------------------

def _sanitize_for_log(obj):
    """Truncate long base64 strings so logs stay readable."""
    if isinstance(obj, dict):
        return {k: _sanitize_for_log(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_sanitize_for_log(v) for v in obj]
    elif isinstance(obj, str) and len(obj) > 200:
        if len(obj) > 1000:
            return obj[:50] + f"... [truncated {len(obj)} chars]"
    return obj


def _format_error(err_text):
    try:
        parsed = json.loads(err_text)
        return json.dumps(_sanitize_for_log(parsed))
    except Exception:
        if len(err_text) > 5000:
            return err_text[:5000] + "...[truncated]"
        return err_text


def _tensor_to_base64(tensor_image):
    """Convert a ComfyUI IMAGE tensor (B,H,W,C) to raw base64 PNG string."""
    if tensor_image is None:
        return None
    if tensor_image.ndim == 4:
        tensor_image = tensor_image[0]
    np_image = (tensor_image.cpu().numpy() * 255).astype(np.uint8)
    mode = "RGBA" if np_image.shape[-1] == 4 else "RGB"
    pil_image = Image.fromarray(np_image, mode)
    if mode == "RGBA":
        pil_image = pil_image.convert("RGB")
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# ===========================================================================
#  1. Official Gemini Node (LLM)
# ===========================================================================

class Leon_Official_Gemini_Node:
    """
    Calls Google's native generateContent REST endpoint for LLM chat.
    Supports text, vision (image input), system instructions, thinking
    level, and temperature.
    """
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION = "generate"

    MODEL_CHOICES = [
        "gemini-3.1-flash-lite-preview",
        "gemini-3.1-pro-preview",
        "gemini-3-flash-preview",
    ]

    THINKING_LEVELS = ["high", "medium", "low", "minimal"]

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": (cls.MODEL_CHOICES, {"default": "gemini-3-flash-preview", "tooltip": "Gemini model to use (Google native API)"}),
                "user_message": ("STRING", {"multiline": True, "default": "Hello! How can you help me today?", "tooltip": "User message to send"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_GEMINI_API_KEY", "tooltip": "Your Google Gemini API key"}),
            },
            "optional": {
                "system_message": ("STRING", {"multiline": True, "default": "", "tooltip": "System instruction to set model behaviour"}),
                "temperature": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.1, "tooltip": "Sampling temperature (Google recommends 1.0 for Gemini 3)"}),
                "thinking_level": (cls.THINKING_LEVELS, {"default": "minimal", "tooltip": "Thinking depth: high (default) → minimal (fastest)"}),
                "input_image": ("IMAGE", {"tooltip": "Optional image input for vision-capable models"}),
                "image_array": ("IMAGE_ARRAY", {"tooltip": "Optional array of images (base64 data URIs or URLs)"}),
                "custom_model": ("STRING", {"default": "", "tooltip": "Override model name with a custom string"}),
            }
        }

    @tenacity.retry(
        wait=tenacity.wait_exponential(multiplier=1.25, min=5, max=30),
        stop=tenacity.stop_after_attempt(5),
    )
    def _call_google_api(self, model, payload, api_key):
        url = f"{GOOGLE_API_BASE}/models/{model}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        }

        print(f"🌐 Official Gemini – POST {url}")
        print(f"🌐 Payload: {json.dumps(_sanitize_for_log(payload), indent=2)}")

        response = requests.post(url, json=payload, headers=headers)
        print(f"🌐 HTTP {response.status_code}")

        if not response.ok:
            # Drop out of the retry loop manually for 400s since it's likely a bad request payload
            print(f"🌐 Error response body from Google API: {response.text}")
            if response.status_code == 400:
                raise tenacity.TryAgain if False else ValueError(f"Google API HTTP 400: {response.text}")

        response.raise_for_status()
        return response.json()

    # ---- main entry point ---------------------------------------------------

    def generate(
        self,
        model,
        user_message,
        api_key,
        system_message="",
        temperature=1.0,
        thinking_level="high",
        input_image=None,
        image_array=None,
        custom_model="",
    ):
        if not user_message.strip():
            raise ValueError("User message cannot be empty")

        active_model = custom_model.strip() if custom_model.strip() else model

        # Build parts list for the user turn
        parts = [{"text": user_message}]

        # Single tensor image
        if input_image is not None:
            b64 = _tensor_to_base64(input_image)
            if b64:
                parts.append({"inlineData": {"mimeType": "image/png", "data": b64}})

        # IMAGE_ARRAY (base64 data-URI strings or plain base64)
        if image_array is not None and len(image_array) > 0:
            for img_data in image_array:
                if isinstance(img_data, str):
                    if img_data.startswith("data:image"):
                        # strip the data URI prefix
                        raw_b64 = img_data.split(",", 1)[1]
                        mime = img_data.split(";")[0].split(":")[1]
                    else:
                        raw_b64 = img_data
                        mime = "image/png"
                    parts.append({"inlineData": {"mimeType": mime, "data": raw_b64}})
            print(f"🌐 Official Gemini: Added {len(image_array)} image(s) from IMAGE_ARRAY")

        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "temperature": temperature,
                "thinkingConfig": {"thinkingLevel": thinking_level},
            },
        }

        # System instruction
        if system_message.strip():
            payload["systemInstruction"] = {
                "parts": [{"text": system_message}]
            }

        try:
            resp_json = self._call_google_api(active_model, payload, api_key)
            print(f"🌐 Response: {json.dumps(_sanitize_for_log(resp_json), indent=2)}")

            # Extract text from candidates
            text_parts = []
            candidates = resp_json.get("candidates", [])
            if candidates:
                for part in candidates[0].get("content", {}).get("parts", []):
                    if "text" in part:
                        text_parts.append(part["text"])

            if not text_parts:
                raise Exception(f"No text in response: {resp_json}")

            return ("\n".join(text_parts),)

        except requests.exceptions.RequestException as e:
            raise Exception(f"Google Gemini API request failed: {str(e)}")
        except Exception as e:
            err_text = response.text if "response" in dir() else "N/A"
            print(f"🌐 Error response: {_format_error(str(e))}")
            raise Exception(f"Google Gemini API call failed: {str(e)}")


# ===========================================================================
#  2. Official Nano Banana Node (Image Generation)
# ===========================================================================

class Leon_Official_Nano_Banana_Node:
    """
    Calls Google's native generateContent REST endpoint for Nano Banana
    (Gemini image generation). Supports text-to-image and image editing
    with optional aspect ratio, image size (up to 4K), and response
    modality control.
    """
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "description", "seed")
    FUNCTION = "generate_image"

    MODEL_CHOICES = [
        "gemini-3.1-flash-image-preview",
        "gemini-3-pro-image-preview",
        "gemini-2.5-flash-image",
    ]

    ASPECT_RATIO_CHOICES = [
        "1:1", "3:4", "4:3", "9:16", "16:9",
        "1:4", "4:1", "1:8", "8:1",
    ]

    IMAGE_SIZE_CHOICES = ["1K", "2K", "4K"]

    RESPONSE_MODALITY_CHOICES = [
        "TEXT_AND_IMAGE",
        "IMAGE_ONLY",
    ]

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "A beautiful painting of a nano banana dish in a fancy restaurant", "tooltip": "Text prompt for image generation"}),
                "model": (cls.MODEL_CHOICES, {"default": "gemini-3.1-flash-image-preview", "tooltip": "Nano Banana model variant"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_GEMINI_API_KEY", "tooltip": "Your Google Gemini API key"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Random seed for reproducible results"}),
            },
            "optional": {
                "aspect_ratio": (cls.ASPECT_RATIO_CHOICES, {"default": "1:1", "tooltip": "Aspect ratio of the output image"}),
                "image_size": (cls.IMAGE_SIZE_CHOICES, {"default": "1K", "tooltip": "Output resolution: 1K (default), 2K, or 4K. Must use uppercase K."}),
                "response_modalities": (cls.RESPONSE_MODALITY_CHOICES, {"default": "IMAGE_ONLY", "tooltip": "TEXT_AND_IMAGE returns descriptive text + image. IMAGE_ONLY returns image only."}),
                "input_image": ("IMAGE", {"tooltip": "Optional reference image for editing"}),
                "image_array": ("IMAGE_ARRAY", {"tooltip": "Optional array of reference images (up to 14). Connect Image Array Builder."}),
                "custom_model": ("STRING", {"default": "", "tooltip": "Override model name with a custom string"}),
            }
        }

    @tenacity.retry(
        wait=tenacity.wait_exponential(multiplier=1.25, min=5, max=30),
        stop=tenacity.stop_after_attempt(5),
    )
    def _call_google_api(self, model, payload, api_key):
        url = f"{GOOGLE_API_BASE}/models/{model}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        }

        print(f"🌐 Official Nano Banana – POST {url}")
        print(f"🌐 Payload: {json.dumps(_sanitize_for_log(payload), indent=2)}")

        response = requests.post(url, json=payload, headers=headers)
        print(f"🌐 HTTP {response.status_code}")

        if not response.ok:
            print(f"🌐 Error response body from Google API: {response.text}")
            if response.status_code == 400:
                raise tenacity.TryAgain if False else ValueError(f"Google API HTTP 400: {response.text}")

        resp_text = response.text
        if "data" in resp_text and len(resp_text) > 1000:
            print(f"🌐 Response: {resp_text[:500]}... (truncated)")
        else:
            print(f"🌐 Response: {resp_text}")

        response.raise_for_status()
        return response.json()

    # ---- main entry point ---------------------------------------------------

    def generate_image(
        self,
        prompt,
        model,
        api_key,
        seed,
        aspect_ratio="1:1",
        image_size="1K",
        response_modalities="TEXT_AND_IMAGE",
        input_image=None,
        image_array=None,
        custom_model="",
    ):
        if not prompt.strip():
            raise ValueError("Prompt must be a non-empty string")

        random.seed(seed)
        active_model = custom_model.strip() if custom_model.strip() else model

        # Build parts
        parts = [{"text": prompt}]

        # Single tensor image for editing
        if input_image is not None:
            b64 = _tensor_to_base64(input_image)
            if b64:
                parts.append({"inlineData": {"mimeType": "image/png", "data": b64}})
                print(f"🌐 Official Nano Banana: Added 1 input image tensor")

        # IMAGE_ARRAY for multi-image reference
        if image_array is not None and len(image_array) > 0:
            for img_data in image_array:
                if isinstance(img_data, str):
                    if img_data.startswith("data:image"):
                        raw_b64 = img_data.split(",", 1)[1]
                        mime = img_data.split(";")[0].split(":")[1]
                    else:
                        raw_b64 = img_data
                        mime = "image/png"
                    parts.append({"inlineData": {"mimeType": mime, "data": raw_b64}})
            print(f"🌐 Official Nano Banana: Added {len(image_array)} image(s) from IMAGE_ARRAY")

        # Response modalities
        modalities = ["TEXT", "IMAGE"] if response_modalities == "TEXT_AND_IMAGE" else ["IMAGE"]

        # Build payload
        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "responseModalities": modalities,
                "imageConfig": {
                    "aspectRatio": aspect_ratio,
                    "imageSize": image_size,
                },
            },
        }

        try:
            resp_json = self._call_google_api(active_model, payload, api_key)

            # Parse response – iterate parts for text and image
            description_parts = []
            pil_img = None

            candidates = resp_json.get("candidates", [])
            if not candidates:
                raise Exception(f"No candidates in response: {resp_json}")

            for part in candidates[0].get("content", {}).get("parts", []):
                if "text" in part:
                    description_parts.append(part["text"])
                elif "inlineData" in part:
                    img_b64 = part["inlineData"]["data"]
                    img_bytes = base64.b64decode(img_b64)
                    pil_img = Image.open(io.BytesIO(img_bytes))

            if pil_img is None:
                raise Exception(f"No image data found in response parts")

            # Convert to RGBA tensor for ComfyUI
            pil_img = pil_img.convert("RGBA")
            img_array = np.array(pil_img).astype(np.float32) / 255.0

            if img_array.ndim == 3 and img_array.shape[-1] == 3:
                alpha = np.ones_like(img_array[..., :1])
                img_array = np.concatenate((img_array, alpha), axis=-1)

            img_tensor = torch.from_numpy(img_array).unsqueeze(0)
            description = "\n".join(description_parts) if description_parts else ""

            return (img_tensor, description, seed)

        except requests.exceptions.RequestException as e:
            raise Exception(f"Google Nano Banana API request failed: {str(e)}")
        except Exception as e:
            print(f"🌐 Error: {_format_error(str(e))}")
            raise Exception(f"Google Nano Banana image generation failed: {str(e)}")


# ===========================================================================
#  Node Mappings
# ===========================================================================

GOOGLE_OFFICIAL_NODE_CLASS_MAPPINGS = {
    "Leon_Official_Gemini_Node": Leon_Official_Gemini_Node,
    "Leon_Official_Nano_Banana_Node": Leon_Official_Nano_Banana_Node,
}

GOOGLE_OFFICIAL_NODE_DISPLAY_NAME_MAPPINGS = {
    "Leon_Official_Gemini_Node": "🤖 Leon Official Gemini 🌐",
    "Leon_Official_Nano_Banana_Node": "🤖 Leon Official Nano Banana 🌐",
}
