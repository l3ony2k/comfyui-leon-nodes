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
                "prompt": ("STRING", {"multiline": True, "default": "A cute cat", "tooltip": "Text description of the image to generate"}),
                "model": (["grok-2-image"], {"default": "grok-2-image", "tooltip": "Grok image generation model"}),
                "output_format": (["png", "jpeg", "webp"], {"default": "png", "tooltip": "Format of the output image"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Random seed for reproducible results"}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/images/generations", "tooltip": "API URL"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_API_KEY_HERE", "tooltip": "Your HyprLab API key"}),
                "response_format": (["url", "b64_json"], {"default": "url", "tooltip": "Format of the response data"}),
            }
        }

    def generate_grok_image(
        self,
        prompt,
        model,
        output_format,
        seed,
        api_url,
        api_key,
        response_format
    ):
        if not prompt.strip():
            raise ValueError("Prompt must be a non-empty string")

        payload = {
            "model": model,
            "prompt": prompt,
            "response_format": response_format
        }
        
        return self._make_api_call(payload, api_url, api_key, response_format, output_format, seed)

# Node mappings for ComfyUI
XAI_NODE_CLASS_MAPPINGS = {
    "Leon_Grok2_Image_API_Node": Leon_Grok2_Image_API_Node,
}

XAI_NODE_DISPLAY_NAME_MAPPINGS = {
    "Leon_Grok2_Image_API_Node": "🤖 Leon Grok 2 Image API",
}
