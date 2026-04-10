from ..base.hyprlab_base import HyprLabImageGenerationNodeBase

class Leon_Pruna_API_Node(HyprLabImageGenerationNodeBase):
    """Pruna AI p-image generation model."""
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "image_url", "seed")
    FUNCTION = "generate_pruna_image"

    ASPECT_RATIO_CHOICES = [
        "1:1", "3:4", "4:3", "9:16", "16:9", "2:3", "3:2", "21:9", "9:21"
    ]

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "a cute cat", "tooltip": "Main text input to guide the generation process"}),
                "output_format": (["png", "jpeg", "webp"], {"default": "png", "tooltip": "Format of the output image"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Random seed for reproducible results"}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/images/generations", "tooltip": "API URL"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_API_KEY_HERE", "tooltip": "Your HyprLab/Pruna API key"}),
                "response_format": (["url", "b64_json"], {"default": "url", "tooltip": "How the response data should be formatted"}),
            },
            "optional": {
                "aspect_ratio": (cls.ASPECT_RATIO_CHOICES, {"default": "1:1", "tooltip": "Aspect ratio of the generated image"}),
            }
        }

    def generate_pruna_image(
        self,
        prompt,
        output_format,
        seed,
        api_url,
        api_key,
        response_format,
        aspect_ratio="1:1"
    ):
        if not prompt.strip():
            raise ValueError("Prompt must be a non-empty string")

        payload = {
            "model": "p-image",
            "prompt": prompt,
            "response_format": response_format,
            "output_format": output_format,
            "aspect_ratio": aspect_ratio
        }

        return self._make_api_call(payload, api_url, api_key, response_format, output_format, seed)


class Leon_Pruna_Image_Edit_Node(HyprLabImageGenerationNodeBase):
    """Pruna AI p-image-edit model for image modifications."""
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "image_url", "seed")
    FUNCTION = "generate_pruna_image_edit"

    ASPECT_RATIO_CHOICES = [
        "1:1", "3:4", "4:3", "9:16", "16:9", "2:3", "3:2", "21:9", "9:21"
    ]

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "make it cyberpunk style", "tooltip": "Main text input to guide the edit process"}),
                "output_format": (["png", "jpeg", "webp"], {"default": "png", "tooltip": "Format of the output image"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Random seed for reproducible results"}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/images/generations", "tooltip": "API URL"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_API_KEY_HERE", "tooltip": "Your HyprLab/Pruna API key"}),
                "response_format": (["url", "b64_json"], {"default": "url", "tooltip": "How the response data should be formatted"}),
            },
            "optional": {
                "input_images_array": ("IMAGE_ARRAY", {"tooltip": "Array of input images for guidance. Connect Image Array Builder node output here."}),
                "aspect_ratio": (cls.ASPECT_RATIO_CHOICES, {"default": "1:1", "tooltip": "Aspect ratio of the generated image"}),
            }
        }

    def generate_pruna_image_edit(
        self,
        prompt,
        output_format,
        seed,
        api_url,
        api_key,
        response_format,
        input_images_array=None,
        aspect_ratio="1:1"
    ):
        if not prompt.strip():
            raise ValueError("Prompt must be a non-empty string")

        payload = {
            "model": "p-image-edit",
            "prompt": prompt,
            "response_format": response_format,
            "output_format": output_format,
            "aspect_ratio": aspect_ratio
        }

        # Handle image inputs from IMAGE_ARRAY
        if input_images_array is not None and isinstance(input_images_array, list):
            # Pass all images
            payload["images"] = input_images_array
            print(f"🟢 p-image-edit: Using {len(input_images_array)} input image(s)")
        else:
            raise ValueError("p-image-edit requires an input image array (images parameter)")

        return self._make_api_call(payload, api_url, api_key, response_format, output_format, seed)


# Node mappings for ComfyUI
PRUNA_NODE_CLASS_MAPPINGS = {
    "Leon_Pruna_API_Node": Leon_Pruna_API_Node,
    "Leon_Pruna_Image_Edit_Node": Leon_Pruna_Image_Edit_Node,
}

PRUNA_NODE_DISPLAY_NAME_MAPPINGS = {
    "Leon_Pruna_API_Node": "🤖 Leon Pruna API",
    "Leon_Pruna_Image_Edit_Node": "🤖 Leon Pruna Image Edit API",
}
