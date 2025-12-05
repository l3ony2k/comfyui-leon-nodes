from .base.hyprlab_base import HyprLabImageGenerationNodeBase

# Google Image Generation Nodes

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


# Node mappings for ComfyUI
GOOGLE_NODE_CLASS_MAPPINGS = {
    "Leon_Google_Image_API_Node": Leon_Google_Image_API_Node,
}

GOOGLE_NODE_DISPLAY_NAME_MAPPINGS = {
    "Leon_Google_Image_API_Node": "🤖 Leon Google Image API",
}
