from ..base.hyprlab_base import HyprLabImageGenerationNodeBase

class Leon_GPT_Image_API_Node(HyprLabImageGenerationNodeBase):
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "image_url", "seed")
    FUNCTION = "generate_gpt_image"

    def __init__(self):
        super().__init__()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": (["gpt-image-2", "gpt-image-1.5", "gpt-image-1", "gpt-image-1-mini"], {"default": "gpt-image-2"}),
                "prompt": ("STRING", {"multiline": True, "default": "A cute cat.", "tooltip": "Text description of the image to generate"}),
                "quality": (["high", "medium", "low"], {"default": "medium", "tooltip": "Image generation quality"}),
                "size": (["auto", "1024x1024", "1536x1024", "1024x1536", "2048x2048", "2048x1152", "3840x2160", "2160x3840"], {"default": "1024x1024", "tooltip": "Size of the generated image"}),
                "response_format": (["url", "b64_json"], {"default": "url", "tooltip": "Format of the response"}),
                "output_format": (["png", "jpeg", "webp"], {"default": "png", "tooltip": "Output image format"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Random seed for reproducible results"}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/images/generations", "tooltip": "API URL"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_HYPRLAB_API_KEY", "tooltip": "Your HyprLab API key"}),
            },
            "optional": {
                "input_images_array": ("IMAGE_ARRAY", {"tooltip": "Optional multiple input images. Connect Image Array Builder node output here."}),
                "mask_image": ("IMAGE", {"tooltip": "Optional mask image for inpainting"}),
                "mask_image_url": ("STRING", {"multiline": False, "default": "", "tooltip": "Optional mask image URL for inpainting"}),
                "background": (["auto", "transparent", "opaque"], {"default": "auto", "tooltip": "Background setting (for gpt-image-1.5, gpt-image-1, gpt-image-1-mini)"}),
                "input_fidelity": (["low", "high"], {"default": "low", "tooltip": "Input fidelity setting (for gpt-image-1.5, gpt-image-1)"}),
            }
        }

    def generate_gpt_image(
        self,
        model,
        prompt,
        quality,
        size,
        response_format,
        output_format,
        seed,
        api_url,
        api_key,
        input_images_array=None,
        mask_image=None,
        mask_image_url="",
        background="auto",
        input_fidelity="low"
    ):
        if not prompt.strip():
            raise ValueError("Prompt must be a non-empty string")

        payload = {
            "model": model,
            "prompt": prompt,
            "quality": quality,
            "size": size,
            "response_format": response_format,
            "output_format": output_format
        }

        # Handle multiple image inputs
        if input_images_array is not None and isinstance(input_images_array, list) and len(input_images_array) > 0:
            payload["image"] = input_images_array

        # Handle mask image
        resolved_mask = self._resolve_image_input(mask_image, mask_image_url, field_name="mask")
        if resolved_mask:
            payload["mask"] = resolved_mask

        # Apply model-specific parameters
        if model in ["gpt-image-1.5", "gpt-image-1", "gpt-image-1-mini"]:
            payload["background"] = background
        
        if model in ["gpt-image-1.5", "gpt-image-1"]:
            payload["input_fidelity"] = input_fidelity

        return self._make_api_call(payload, api_url, api_key, response_format, output_format, seed)


# Node mappings for ComfyUI
OPENAI_IMAGE_NODE_CLASS_MAPPINGS = {
    "Leon_GPT_Image_API_Node": Leon_GPT_Image_API_Node,
}

OPENAI_IMAGE_NODE_DISPLAY_NAME_MAPPINGS = {
    "Leon_GPT_Image_API_Node": "🤖 Leon GPT-Image API",
}
