from ..base.hyprlab_base import HyprLabImageGenerationNodeBase

# Nano Banana Image Generation Nodes

class Leon_Nano_Banana_API_Node(HyprLabImageGenerationNodeBase):
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "image_url", "seed")
    FUNCTION = "generate_nano_banana_image"
    ASPECT_RATIO_CHOICES = [
        "match_input_image",
        "1:1",
        "9:16",
        "16:9",
        "3:4",
        "4:3",
        "3:2",
        "2:3",
        "5:4",
        "4:5",
        "21:9",
    ]

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "Make the cat jump.", "tooltip": "Main text prompt that influences the output generation"}),
                "model": (["nano-banana-pro", "nano-banana"], {"default": "nano-banana-pro", "tooltip": "Nano Banana model: pro version supports resolution control"}),
                "output_format": (["png", "jpeg", "webp"], {"default": "png", "tooltip": "Format of the output image"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Random seed for reproducible results"}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/images/generations", "tooltip": "API URL"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_API_KEY_HERE", "tooltip": "Your HyprLab API key"}),
                "response_format": (["url", "b64_json"], {"default": "url", "tooltip": "Format in which the response will be returned"}),
            },
            "optional": {
                "input_images_array": ("IMAGE_ARRAY", {"tooltip": "Array of input images (up to 4). Connect Image Array Builder node output here."}),
                "aspect_ratio": (cls.ASPECT_RATIO_CHOICES, {"default": "1:1", "tooltip": "Aspect ratio of the generated image (match_input_image requires at least one image input)"}),
                "resolution": (["1K", "2K", "4K"], {"default": "2K", "tooltip": "🟢 NANO-BANANA-PRO ONLY: Image resolution (1K/2K/4K)"}),
            }
        }

    def generate_nano_banana_image(
        self,
        prompt,
        model,
        output_format,
        seed,
        api_url,
        api_key,
        response_format,
        input_images_array=None,
        aspect_ratio="1:1",
        resolution="2K"
    ):
        if not prompt.strip():
            raise ValueError("Prompt must be a non-empty string")

        payload = {
            "model": model,
            "prompt": prompt,
            "response_format": response_format,
            "output_format": output_format
        }

        # Handle image inputs from IMAGE_ARRAY
        image_inputs = []
        if input_images_array is not None and isinstance(input_images_array, list):
            image_inputs = input_images_array[:4]  # Max 4 images

        # Set image_input in payload based on number of images
        if len(image_inputs) == 1:
            # Single image input - send as string
            payload["image_input"] = image_inputs[0]
            print(f"🟢 {model}: Using 1 input image")
        elif len(image_inputs) > 1:
            # Multiple image inputs - send as array
            payload["image_input"] = image_inputs
            print(f"🟢 {model}: Using {len(image_inputs)} input images")
        # If no image inputs, don't add image_input to payload (text-only mode)

        if aspect_ratio:
            if aspect_ratio == "match_input_image":
                if image_inputs:
                    payload["aspect_ratio"] = aspect_ratio
                else:
                    print(f"⚠️ {model}: 'match_input_image' requires at least one image_input, skipping aspect_ratio")
            else:
                payload["aspect_ratio"] = aspect_ratio

        # Resolution parameter (nano-banana-pro only)
        if model == "nano-banana-pro" and resolution:
            payload["resolution"] = resolution
            print(f"🟢 nano-banana-pro: Using resolution '{resolution}'")
        elif model == "nano-banana" and resolution != "2K":
            print(f"⚠️ nano-banana: 'resolution' parameter only supported by nano-banana-pro")

        return self._make_api_call(payload, api_url, api_key, response_format, output_format, seed)


# Tuzi API Nano Banana Image Generation Node
class Leon_Nano_Banana_Tuzi_API_Node(HyprLabImageGenerationNodeBase):
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "image_url", "seed")
    FUNCTION = "generate_tuzi_image"
    SIZE_CHOICES = [
        "1x1",    # 1024x1024
        "2x3",    # 832x1248
        "3x2",    # 1248x832
        "3x4",    # 864x1184
        "4x3",    # 1184x864
        "4x5",    # 896x1152
        "5x4",    # 1152x896
        "9x16",   # 768x1344
        "16x9",   # 1344x768
        "21x9",   # 1536x672
    ]

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "a cat.", "tooltip": "Text description of the desired image. Maximum length 1000 characters."}),
                "model": (["nano-banana-2", "nano-banana-2-async", "nano-banana-2-vip"], {"default": "nano-banana-2", "tooltip": "Nano Banana 2 model variants"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Random seed for reproducible results"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_API_KEY_HERE", "tooltip": "Your Tuzi API key"}),
                "response_format": (["url", "b64_json"], {"default": "url", "tooltip": "Format for returning the generated image. Must be either url or b64_json."}),
            },
            "optional": {
                "input_images_array": ("IMAGE_ARRAY", {"tooltip": "Array of input images (up to 4). Connect Image Array Builder node output here."}),
                "size": (cls.SIZE_CHOICES, {"default": "1x1", "tooltip": "Size of generated image (format: WxH ratio)"}),
                "quality": (["1k", "2k", "4k"], {"default": "2k", "tooltip": "Image generation quality (only effective for Banana 2)"}),
            }
        }

    def generate_tuzi_image(
        self,
        prompt,
        model,
        seed,
        api_key,
        response_format,
        input_images_array=None,
        size="1x1",
        quality="2k"
    ):
        if not prompt.strip():
            raise ValueError("Prompt must be a non-empty string")

        payload = {
            "model": model,
            "prompt": prompt,
            "response_format": response_format,
        }

        if size:
            payload["size"] = size

        if quality:
            payload["quality"] = quality

        # Handle image inputs from IMAGE_ARRAY
        image_inputs = []
        if input_images_array is not None and isinstance(input_images_array, list):
            image_inputs = input_images_array[:4]  # Max 4 images

        # Set image in payload based on number of images
        if len(image_inputs) == 1:
            payload["image"] = image_inputs[0]
            print(f"🐰 Tuzi {model}: Using 1 input image")
        elif len(image_inputs) > 1:
            payload["image"] = image_inputs
            print(f"🐰 Tuzi {model}: Using {len(image_inputs)} input images")

        api_url = "https://api.tu-zi.com/v1/images/generations"
        return self._make_api_call(payload, api_url, api_key, response_format, "png", seed)


# Tuzi API Nano Banana Image Edit Node
class Leon_Nano_Banana_Edit_Tuzi_API_Node(HyprLabImageGenerationNodeBase):
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "image_url", "seed")
    FUNCTION = "edit_tuzi_image"
    SIZE_CHOICES = [
        "1x1",    # 1024x1024
        "2x3",    # 832x1248
        "3x2",    # 1248x832
        "3x4",    # 864x1184
        "4x3",    # 1184x864
        "4x5",    # 896x1152
        "5x4",    # 1152x896
        "9x16",   # 768x1344
        "16x9",   # 1344x768
        "21x9",   # 1536x672
    ]

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "merge two images", "tooltip": "Text description of the desired image. Maximum length 1000 characters."}),
                "model": (["nano-banana-2", "nano-banana-2-async", "nano-banana-2-vip"], {"default": "nano-banana-2", "tooltip": "Nano Banana 2 model variants"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Random seed for reproducible results"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_API_KEY_HERE", "tooltip": "Your Tuzi API key"}),
                "response_format": (["url", "b64_json"], {"default": "url", "tooltip": "Format for returning the generated image. Must be either url or b64_json."}),
            },
            "optional": {
                "input_images_array": ("IMAGE_ARRAY", {"tooltip": "Array of input images to edit. Connect Image Array Builder node output here. REQUIRED for edit."}),
                "mask_image": ("IMAGE", {"tooltip": "Additional image where fully transparent regions (e.g., areas with alpha zero) will be edited"}),
                "size": (cls.SIZE_CHOICES, {"default": "1x1", "tooltip": "Size of generated image (format: WxH ratio)"}),
                "quality": (["1k", "2k", "4k"], {"default": "2k", "tooltip": "Image generation quality (only effective for Banana 2)"}),
            }
        }

    def edit_tuzi_image(
        self,
        prompt,
        model,
        seed,
        api_key,
        response_format,
        input_images_array=None,
        mask_image=None,
        size="1x1",
        quality="2k"
    ):
        import requests
        import random
        import io
        import base64
        import numpy as np
        from PIL import Image
        import torch

        if not prompt.strip():
            raise ValueError("Prompt must be a non-empty string")

        random.seed(seed)

        api_url = "https://api.tu-zi.com/v1/images/edits"

        headers = {
            "Authorization": f"Bearer {api_key}"
        }

        # Build multipart form data
        form_data = {
            "model": (None, model),
            "prompt": (None, prompt),
            "response_format": (None, response_format),
        }

        if size:
            form_data["size"] = (None, size)

        if quality:
            form_data["quality"] = (None, quality)

        # Handle image inputs from IMAGE_ARRAY - convert to file uploads
        # The Tuzi edit API supports multiple images via multipart form
        image_files = []
        if input_images_array is not None and isinstance(input_images_array, list):
            for i, img_data in enumerate(input_images_array[:4]):
                # img_data could be a base64 data URI or URL
                if isinstance(img_data, str):
                    if img_data.startswith("data:image"):
                        # Extract base64 data and convert to bytes
                        base64_str = img_data.split(",", 1)[1]
                        img_bytes = base64.b64decode(base64_str)
                        image_files.append(("image", (f"image_{i}.png", io.BytesIO(img_bytes), "image/png")))
                        print(f"🐰 Tuzi Edit: Added image {i+1} as file upload")
                    else:
                        # It's a URL - add as file tuple with None for file object
                        image_files.append(("image", (None, img_data)))
                        print(f"🐰 Tuzi Edit: Added image {i+1} as URL: {img_data[:60]}...")
            
            if image_files:
                print(f"🐰 Tuzi Edit: Total {len(image_files)} images for edit request")

        # Handle mask image if provided
        if mask_image is not None:
            mask_base64 = self._tensor_to_base64_data_uri(mask_image)
            if mask_base64 and mask_base64.startswith("data:image"):
                base64_str = mask_base64.split(",", 1)[1]
                mask_bytes = base64.b64decode(base64_str)
                form_data["mask"] = ("mask.png", io.BytesIO(mask_bytes), "image/png")

        try:
            # Combine form_data and image_files for the multipart request
            # Convert form_data dict to list of tuples and append image files
            all_files = [(k, v) for k, v in form_data.items()] + image_files
            response = requests.post(api_url, headers=headers, files=all_files)

            print(f"API Request URL: {api_url}")
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
                actual_image_url = f"data:image/png;base64,{b64_data}"
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
            raise Exception(f"Image edit failed: {str(e)}")


# Node mappings for ComfyUI
NANO_BANANA_NODE_CLASS_MAPPINGS = {
    "Leon_Nano_Banana_API_Node": Leon_Nano_Banana_API_Node,
    "Leon_Nano_Banana_Tuzi_API_Node": Leon_Nano_Banana_Tuzi_API_Node,
    "Leon_Nano_Banana_Edit_Tuzi_API_Node": Leon_Nano_Banana_Edit_Tuzi_API_Node,
}

NANO_BANANA_NODE_DISPLAY_NAME_MAPPINGS = {
    "Leon_Nano_Banana_API_Node": "🤖 Leon Nano Banana API",
    "Leon_Nano_Banana_Tuzi_API_Node": "🤖 Leon Nano Banana Tuzi API 🐰",
    "Leon_Nano_Banana_Edit_Tuzi_API_Node": "🤖 Leon Nano Banana Edit Tuzi API 🐰",
}
