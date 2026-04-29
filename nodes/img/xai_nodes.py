from ..base.hyprlab_base import HyprLabImageGenerationNodeBase

# Grok Image Generation Nodes

class Leon_Grok2_Image_API_Node(HyprLabImageGenerationNodeBase):
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "image_url", "seed")
    FUNCTION = "generate_grok_image"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "A cute cat.", "tooltip": "Text description of the image to generate"}),
                "model": (["grok-imagine-image", "grok-imagine-image-pro"], {"default": "grok-imagine-image", "tooltip": "Grok image generation model"}),
                "aspect_ratio": (["1:1", "3:4", "4:3", "9:16", "16:9", "2:3", "3:2", "21:9", "9:21"], {"default": "1:1", "tooltip": "Aspect ratio of the generated image"}),
                "resolution": (["1K", "2K"], {"default": "1K", "tooltip": "Resolution for the generated image"}),
                "output_format": (["png", "jpeg", "webp"], {"default": "png", "tooltip": "Format of the output image"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Random seed for reproducible results"}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/images/generations", "tooltip": "API URL"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_API_KEY_HERE", "tooltip": "Your HyprLab API key"}),
                "response_format": (["url", "b64_json"], {"default": "url", "tooltip": "Format of the response data"}),
            },
            "optional": {
                "image": ("IMAGE_ARRAY", {"tooltip": "Array of input images (optional)"}),
            }
        }

    def generate_grok_image(
        self,
        prompt,
        model,
        aspect_ratio,
        resolution,
        output_format,
        seed,
        api_url,
        api_key,
        response_format,
        image=None
    ):
        if not prompt.strip():
            raise ValueError("Prompt must be a non-empty string")

        payload = {
            "model": model,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "response_format": response_format,
            "output_format": output_format
        }

        if image is not None and isinstance(image, list):
            payload["image"] = image

        return self._make_api_call(payload, api_url, api_key, response_format, output_format, seed)

# Node mappings for ComfyUI
XAI_NODE_CLASS_MAPPINGS = {
    "Leon_Grok2_Image_API_Node": Leon_Grok2_Image_API_Node,
}

XAI_NODE_DISPLAY_NAME_MAPPINGS = {
    "Leon_Grok2_Image_API_Node": "🤖 Leon Grok Imagine Image API",
}
