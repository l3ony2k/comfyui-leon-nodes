from .base.hyprlab_base import HyprLabImageGenerationNodeBase

# Luma Image Generation Nodes

class Leon_Luma_AI_Image_API_Node(HyprLabImageGenerationNodeBase):
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "image_url", "seed")
    FUNCTION = "generate_luma_image"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "A stunning fantasy landscape", "tooltip": "Main text input to guide the generation process (max 10,000 characters)"}),
                "model": (["photon", "photon-flash"], {"default": "photon", "tooltip": "Luma AI model to use for generation"}),
                "output_format": (["png", "jpeg", "webp"], {"default": "png", "tooltip": "Format of the output image"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Random seed for reproducible results (may not be used by Luma API via HyprLab)"}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/images/generations", "tooltip": "API URL"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_API_KEY_HERE", "tooltip": "Your HyprLab API key"}),
                "response_format": (["url", "b64_json"], {"default": "url", "tooltip": "How the response data should be formatted"}),
            },
            "optional": {
                "aspect_ratio": (["1:1", "3:4", "4:3", "9:16", "16:9", "9:21", "21:9"], {"default": "1:1", "tooltip": "Aspect ratio of the output. If not specified, model default may be used."}),
                "input_image_ref_socket": ("IMAGE", { "tooltip": "Image for image reference."}),
                "input_image_ref_url": ("STRING", {"multiline": False, "default": "", "tooltip": "Image reference URL (use when providing a hosted image instead of socket input)"}),
                "image_reference_weight": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01, "tooltip": "Influence of the image reference (0 to 1)."}),
                "input_style_ref_socket": ("IMAGE", { "tooltip": "Image for style reference."}),
                "input_style_ref_url": ("STRING", {"multiline": False, "default": "", "tooltip": "Style reference URL (use when providing a hosted image instead of socket input)"}),
                "style_reference_weight": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01, "tooltip": "Influence of the style reference (0 to 1)."}),
                "input_char_ref_socket": ("IMAGE", { "tooltip": "Image for character reference."}),
                "input_char_ref_url": ("STRING", {"multiline": False, "default": "", "tooltip": "Character reference URL (use when providing a hosted image instead of socket input)"}),
            }
        }

    def generate_luma_image(
        self,
        prompt,
        model,
        output_format,
        seed,
        api_url,
        api_key,
        response_format,
        aspect_ratio="1:1",
        input_image_ref_socket=None,
        input_image_ref_url="",
        image_reference_weight=0.5,
        input_style_ref_socket=None,
        input_style_ref_url="",
        style_reference_weight=0.5,
        input_char_ref_socket=None,
        input_char_ref_url=""
    ):
        if len(prompt) > 10000:
            raise ValueError("Prompt must not exceed 10,000 characters")
        
        actual_image_ref_url = self._resolve_image_input(
            input_image_ref_socket, input_image_ref_url, field_name="image_reference_url"
        )
        actual_style_ref_url = self._resolve_image_input(
            input_style_ref_socket, input_style_ref_url, field_name="style_reference_url"
        )
        actual_char_ref_url = self._resolve_image_input(
            input_char_ref_socket, input_char_ref_url, field_name="character_reference_url"
        )

        if not prompt.strip() and not actual_image_ref_url and not actual_style_ref_url and not actual_char_ref_url:
             raise ValueError("Prompt is required for Luma AI, or at least one reference Image (Socket) must be provided.")

        payload = {
            "model": model,
            "prompt": prompt,
            "response_format": response_format,
            "output_format": output_format
        }

        if aspect_ratio:
             payload["aspect_ratio"] = aspect_ratio
        
        if actual_image_ref_url:
            payload["image_reference_url"] = actual_image_ref_url
            payload["image_reference_weight"] = image_reference_weight
        
        if actual_style_ref_url:
            payload["style_reference_url"] = actual_style_ref_url
            payload["style_reference_weight"] = style_reference_weight

        if actual_char_ref_url:
            payload["character_reference_url"] = actual_char_ref_url

        return self._make_api_call(payload, api_url, api_key, response_format, output_format, seed)


# Node mappings for ComfyUI
LUMA_NODE_CLASS_MAPPINGS = {
    "Leon_Luma_AI_Image_API_Node": Leon_Luma_AI_Image_API_Node,
}

LUMA_NODE_DISPLAY_NAME_MAPPINGS = {
    "Leon_Luma_AI_Image_API_Node": "🤖 Leon Luma AI Image API",
}
