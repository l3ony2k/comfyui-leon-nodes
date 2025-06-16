from PIL import Image
import io
import torch
import numpy as np
import base64
import requests # For ImgBB
import json # For ImgBB

class Leon_Image_Split_4Grid_Node:
    CATEGORY = "Leon_Utils"
    RETURN_TYPES = ("IMAGE", "IMAGE", "IMAGE", "IMAGE")
    RETURN_NAMES = ("image_TL", "image_TR", "image_BL", "image_BR")
    FUNCTION = "split_image_grid"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image": ("IMAGE",), 
            }
        }

    def _tensor_to_pil(self, tensor_image):
        if tensor_image.ndim == 4:
            tensor_image = tensor_image[0]
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
        pil_image = pil_image.convert("RGBA")

        width, height = pil_image.size
        mid_w, mid_h = width // 2, height // 2

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
    CATEGORY = "Leon_Utils"
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
        if tensor_image.ndim == 4:
            tensor_image = tensor_image[0]
        np_image = (tensor_image.cpu().numpy() * 255).astype(np.uint8)
        pil_image = Image.fromarray(np_image, 'RGBA' if np_image.shape[-1] == 4 else 'RGB')
        return pil_image

    def upload_to_imgbb(self, image, api_key, expire=False, expiration_time_seconds=3600):
        if not api_key or not api_key.strip():
            raise ValueError("ImgBB API Key is required and cannot be empty.")

        pil_image = self._tensor_to_pil(image)

        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        buffer.seek(0)

        base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

        url = f"https://api.imgbb.com/1/upload?key={api_key}"
        if expire:
            url += f"&expiration={expiration_time_seconds}"

        payload = {"image": base64_image}

        print(f"ImgBB Upload: Posting to {url.split('?key=')[0]}?key=YOUR_API_KEY...")

        try:
            response = requests.post(url, data=payload)
            response.raise_for_status()
            result = response.json()

            if result.get("success") and result.get("data") and result["data"].get("url"):
                return (result["data"]["url"],)
            else:
                error_message = "Unknown error"
                if result.get("error"):
                    if isinstance(result["error"], dict):
                        error_message = result["error"].get("message", "Unknown error from API dictionary")
                    else:
                        error_message = str(result["error"])
                elif result.get("status_txt"):
                     error_message = result.get("status_txt")
                
                status_code = result.get("status_code", response.status_code)
                raise ValueError(f"ImgBB API Error (Code: {status_code}): {error_message}. Full response: {json.dumps(result)}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"ImgBB upload request failed: {str(e)}")
        except Exception as e:
            raise ValueError(f"ImgBB upload error: {str(e)}. Response text (if available): {response.text if 'response' in locals() else 'N/A'}")


class Leon_Hypr_Upload_Node:
    CATEGORY = "Leon_Utils"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("hypr_url",)
    FUNCTION = "upload_to_hypr"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("STRING", {"default": "", "multiline": False, "tooltip": "Your HyprLab API key (Bearer token)"}),
            },
            "optional": {
                # Image tensor to upload. If provided, treated as an image upload via multipart/form-data.
                "image": ("IMAGE",),
                # Local file path to an image or video. If provided, upload via multipart/form-data.
                "file_path": ("STRING", {"default": "", "multiline": False, "tooltip": "Path to a local image/video file"}),
                # Remote URL to an asset. If provided, sent in JSON payload.
                "url": ("STRING", {"default": "", "multiline": False, "tooltip": "Remote URL of an image/video to upload"}),
                # Base64 string for the asset. Sent in JSON payload. (Data URL also supported.)
                "base64_data": ("STRING", {"default": "", "multiline": True, "tooltip": "Raw/base64 or data URL string of the asset"}),
                # For image uploads only: desired output format. Leave empty to keep original.
                "output_format": ("STRING", {"default": "", "multiline": False, "tooltip": "Optional output format for images: png, jpg, webp"}),
            }
        }

    def _tensor_to_bytes(self, tensor_image):
        """Convert a ComfyUI IMAGE tensor to PNG bytes."""
        if tensor_image.ndim == 4:
            tensor_image = tensor_image[0]
        np_image = (tensor_image.cpu().numpy() * 255).astype(np.uint8)
        pil_image = Image.fromarray(np_image, 'RGBA' if np_image.shape[-1] == 4 else 'RGB')
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    def upload_to_hypr(self, api_key, image=None, file_path="", url="", base64_data="", output_format=""):
        if not api_key or not api_key.strip():
            raise ValueError("HyprLab API Key is required and cannot be empty.")

        endpoint = "https://api.hyprlab.io/v1/uploads"
        headers = {"Authorization": f"Bearer {api_key.strip()}"}

        # Decide the upload method based on provided inputs in priority order
        if image is not None:
            # tensor image upload via multipart
            buffer = self._tensor_to_bytes(image)
            files = {"file": ("image.png", buffer, "image/png")}
            data = {}
            if output_format:
                data["output_format"] = output_format
            response = requests.post(endpoint, headers=headers, files=files, data=data)
        elif file_path:
            # Local file upload via multipart
            try:
                import mimetypes
                mime_type, _ = mimetypes.guess_type(file_path)
                mime_type = mime_type or "application/octet-stream"
                with open(file_path, "rb") as f:
                    files = {"file": (file_path.split("/")[-1], f, mime_type)}
                    data = {"output_format": output_format} if output_format else {}
                    response = requests.post(endpoint, headers=headers, files=files, data=data)
            except FileNotFoundError:
                raise ValueError(f"File not found: {file_path}")
        else:
            # JSON body upload (url or base64 data)
            payload = {}
            if url:
                # Determine if image or video by simple extension heuristics
                if any(url.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".gif"]):
                    payload["image"] = url
                    if output_format:
                        payload["output_format"] = output_format
                else:
                    payload["video"] = url
            elif base64_data:
                # Assume caller sets correct asset type in the data URL/header
                # We will default to image unless told otherwise (rudimentary detection)
                if base64_data.strip().startswith("data:video"):
                    payload["video"] = base64_data
                else:
                    payload["image"] = base64_data
                    if output_format:
                        payload["output_format"] = output_format
            else:
                raise ValueError("No valid input provided. Provide an image tensor, file_path, url, or base64_data.")

            headers_json = {**headers, "Content-Type": "application/json"}
            response = requests.post(endpoint, headers=headers_json, json=payload)

        # Handle response
        try:
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.RequestException as e:
            raise ValueError(f"HyprLab upload request failed: {str(e)}")
        except Exception:
            raise ValueError(f"Failed to parse HyprLab response. Status: {response.status_code}. Content: {response.text}")

        # Extract URL from response
        for key in ("imageUrl", "videoUrl", "url"):
            if key in result:
                return (result[key],)
        raise ValueError(f"Unexpected HyprLab response format: {result}")


UTIL_NODE_CLASS_MAPPINGS = {
    "Leon_Image_Split_4Grid_Node": Leon_Image_Split_4Grid_Node,
    "Leon_String_Combine_Node": Leon_String_Combine_Node,
    "Leon_ImgBB_Upload_Node": Leon_ImgBB_Upload_Node,
    "Leon_Hypr_Upload_Node": Leon_Hypr_Upload_Node,
}

UTIL_NODE_DISPLAY_NAME_MAPPINGS = {
    "Leon_Image_Split_4Grid_Node": "🤖 Leon Image Split 4-Grid",
    "Leon_String_Combine_Node": "🤖 Leon String Combine",
    "Leon_ImgBB_Upload_Node": "🤖 Leon ImgBB Upload",
    "Leon_Hypr_Upload_Node": "🤖 Leon Hypr Upload",
} 