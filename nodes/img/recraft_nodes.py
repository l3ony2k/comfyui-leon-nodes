from ..base.hyprlab_base import HyprLabImageGenerationNodeBase

# Recraft Image Generation Nodes

class Leon_Recraft_Image_API_Node(HyprLabImageGenerationNodeBase):
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "image_url", "seed")
    FUNCTION = "generate_recraft_image"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "cat", "tooltip": "Main text that influences the image generation (max 10,000 characters)"}),
                "model": (["recraft-v3"], {"default": "recraft-v3", "tooltip": "Recraft AI model to use for generation"}),
                "output_format": (["png", "jpeg", "webp"], {"default": "webp", "tooltip": "Format of the output image"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Random seed for reproducible results"}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/images/generations", "tooltip": "API URL"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_API_KEY_HERE", "tooltip": "Your HyprLab API key"}),
                "response_format": (["url", "b64_json"], {"default": "url", "tooltip": "How the response data should be formatted"}),
            },
            "optional": {
                "size": ([
                    "1024x1024", "1365x1024", "1024x1365", "1536x1024", "1024x1536",
                    "1820x1024", "1024x1820", "1024x2048", "2048x1024", "1434x1024",
                    "1024x1434", "1024x1280", "1280x1024", "1024x1707", "1707x1024"
                ], {"default": "1024x1024", "tooltip": "Dimensions of the generated image"}),
                "style": ([
                    "digital_illustration", "digital_illustration/pixel_art", "digital_illustration/hand_drawn",
                    "digital_illustration/grain", "digital_illustration/infantile_sketch", "digital_illustration/2d_art_poster",
                    "digital_illustration/handmade_3d", "digital_illustration/hand_drawn_outline", "digital_illustration/engraving_color",
                    "digital_illustration/2d_art_poster_2", "realistic_image", "realistic_image/b_and_w",
                    "realistic_image/hard_flash", "realistic_image/hdr", "realistic_image/natural_light",
                    "realistic_image/studio_portrait", "realistic_image/enterprise", "realistic_image/motion_blur",
                    "vector_illustration", "vector_illustration/engraving", "vector_illustration/line_art",
                    "vector_illustration/line_circuit", "vector_illustration/linocut"
                ], {"default": "realistic_image", "tooltip": "Artistic style or filter applied to the generated image"}),
            }
        }

    def generate_recraft_image(
        self,
        prompt,
        model,
        output_format,
        seed,
        api_url,
        api_key,
        response_format,
        size="1024x1024",
        style="realistic_image"
    ):
        if len(prompt) > 10000:
            raise ValueError("Prompt must not exceed 10,000 characters")
        if not prompt.strip():
            raise ValueError("Prompt must be a non-empty string")

        payload = {
            "model": model,
            "prompt": prompt,
            "response_format": response_format,
            "output_format": output_format
        }

        # Add optional parameters
        if size:
            payload["size"] = size
        if style:
            payload["style"] = style
        
        return self._make_api_call(payload, api_url, api_key, response_format, output_format, seed)


# Node mappings for ComfyUI
RECRAFT_NODE_CLASS_MAPPINGS = {
    "Leon_Recraft_Image_API_Node": Leon_Recraft_Image_API_Node,
}

RECRAFT_NODE_DISPLAY_NAME_MAPPINGS = {
    "Leon_Recraft_Image_API_Node": "🤖 Leon Recraft Image API",
}
