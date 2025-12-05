from .base.hyprlab_base import HyprLabImageGenerationNodeBase

# Ideogram Image Generation Nodes

class Leon_Ideogram_Image_API_Node(HyprLabImageGenerationNodeBase):
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "image_url", "seed")
    FUNCTION = "generate_ideogram_image"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "cat", "tooltip": "Main text input to guide the generation process (max 10,000 characters)"}),
                "model": (["ideogram-v2", "ideogram-v2-turbo"], {"default": "ideogram-v2", "tooltip": "Ideogram AI model to use for generation"}),
                "output_format": (["png", "jpeg", "webp"], {"default": "webp", "tooltip": "Format of the output image"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Random seed for reproducible results"}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/images/generations", "tooltip": "API URL"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_API_KEY_HERE", "tooltip": "Your HyprLab API key"}),
                "response_format": (["url", "b64_json"], {"default": "url", "tooltip": "How the response data should be formatted"}),
            },
            "optional": {
                "negative_prompt": ("STRING", {"multiline": True, "default": "", "tooltip": "Input that defines what NOT to include during generation (max 10,000 characters)"}),
                "aspect_ratio": (["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "16:10", "10:16", "3:1", "1:3"], {"default": "1:1", "tooltip": "Aspect ratio of the generated image"}),
                "style_type": (["Auto", "General", "Realistic", "Design", "Render 3D", "Anime"], {"default": "Auto", "tooltip": "Artistic style or genre for the output"}),
                "magic_prompt_option": (["Auto", "On", "Off"], {"default": "Auto", "tooltip": "Toggle for automatic magic prompt system"}),
            }
        }

    def generate_ideogram_image(
        self,
        prompt,
        model,
        output_format,
        seed,
        api_url,
        api_key,
        response_format,
        negative_prompt="",
        aspect_ratio="1:1",
        style_type="Auto",
        magic_prompt_option="Auto"
    ):
        if len(prompt) > 10000:
            raise ValueError("Prompt must not exceed 10,000 characters")
        if not prompt.strip():
            raise ValueError("Prompt must be a non-empty string")
        
        if negative_prompt and len(negative_prompt) > 10000:
            raise ValueError("Negative prompt must not exceed 10,000 characters")

        payload = {
            "model": model,
            "prompt": prompt,
            "response_format": response_format,
            "output_format": output_format
        }

        # Add optional parameters
        if negative_prompt.strip():
            payload["negative_prompt"] = negative_prompt
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
        if style_type:
            payload["style_type"] = style_type
        if magic_prompt_option:
            payload["magic_prompt_option"] = magic_prompt_option
        
        return self._make_api_call(payload, api_url, api_key, response_format, output_format, seed)


# Node mappings for ComfyUI
IDEOGRAM_NODE_CLASS_MAPPINGS = {
    "Leon_Ideogram_Image_API_Node": Leon_Ideogram_Image_API_Node,
}

IDEOGRAM_NODE_DISPLAY_NAME_MAPPINGS = {
    "Leon_Ideogram_Image_API_Node": "🤖 Leon Ideogram Image API",
}
