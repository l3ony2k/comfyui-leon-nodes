from .base.hyprlab_base import HyprLabImageGenerationNodeBase

# ByteDance Seedream 4 Image Generation Node

class Leon_Seedream4_API_Node(HyprLabImageGenerationNodeBase):
    """Seedream 4.0 - Latest ByteDance image generation model with multi-image support."""
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "image_url", "seed")
    FUNCTION = "generate_seedream4_image"

    ASPECT_RATIO_CHOICES = [
        "1:1", "3:4", "4:3", "9:16", "16:9", "2:3", "3:2", "21:9", "9:21", "match_input_image"
    ]

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "a cute cat", "tooltip": "Main text input to guide the generation process (max 10,000 characters)"}),
                "output_format": (["png", "jpeg", "webp"], {"default": "png", "tooltip": "Format of the output image"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Random seed for reproducible results"}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/images/generations", "tooltip": "API URL"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_API_KEY_HERE", "tooltip": "Your HyprLab API key"}),
                "response_format": (["url", "b64_json"], {"default": "url", "tooltip": "How the response data should be formatted"}),
            },
            "optional": {
                "input_images_array": ("IMAGE_ARRAY", {"tooltip": "Array of input images for guidance (up to 4). Connect Image Array Builder node output here."}),
                "aspect_ratio": (cls.ASPECT_RATIO_CHOICES, {"default": "1:1", "tooltip": "Aspect ratio of the generated image"}),
                "size": (["1K", "2K", "4K"], {"default": "4K", "tooltip": "Image resolution (1K/2K/4K)"}),
                "guidance_scale": ("FLOAT", {"default": 2.5, "min": 0.0, "max": 10.0, "step": 0.1, "tooltip": "Prompt adherence (0-10)"}),
            }
        }

    def generate_seedream4_image(
        self,
        prompt,
        output_format,
        seed,
        api_url,
        api_key,
        response_format,
        input_images_array=None,
        aspect_ratio="1:1",
        size="4K",
        guidance_scale=2.5
    ):
        if len(prompt) > 10000:
            raise ValueError("Prompt must not exceed 10,000 characters")
        if not prompt.strip():
            raise ValueError("Prompt must be a non-empty string")

        payload = {
            "model": "seedream-4",
            "prompt": prompt,
            "response_format": response_format,
            "output_format": output_format
        }

        # Handle image inputs from IMAGE_ARRAY
        if input_images_array is not None and isinstance(input_images_array, list):
            input_images = input_images_array[:4]  # Max 4 images for seedream-4
            if len(input_images) == 1:
                payload["image_input"] = input_images[0]
            elif len(input_images) > 1:
                payload["image_input"] = input_images
            print(f"🟢 SEEDREAM-4: Using {len(input_images)} input image(s)")

        # Add parameters
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
        if size:
            payload["size"] = size
            print(f"🟢 SEEDREAM-4: Using size parameter '{size}' (1K/2K/4K)")
        if guidance_scale is not None:
            payload["guidance_scale"] = guidance_scale

        return self._make_api_call(payload, api_url, api_key, response_format, output_format, seed)


class Leon_Seedream3_API_Node(HyprLabImageGenerationNodeBase):
    """Seedream 3 family - includes seedream-3, dreamina-3.1, and seededit-3 models."""
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "image_url", "seed")
    FUNCTION = "generate_seedream3_image"

    ASPECT_RATIO_CHOICES = [
        "1:1", "3:4", "4:3", "9:16", "16:9", "2:3", "3:2", "21:9"
    ]

    MODEL_CHOICES = ["seedream-3", "dreamina-3.1", "seededit-3"]

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "a cute cat", "tooltip": "Main text input to guide the generation process (max 10,000 characters)"}),
                "model": (cls.MODEL_CHOICES, {"default": "seedream-3", "tooltip": "ByteDance model: seedream-3, dreamina-3.1 (enhanced prompt), or seededit-3 (requires image)"}),
                "output_format": (["png", "jpeg", "webp"], {"default": "png", "tooltip": "Format of the output image"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Random seed for reproducible results"}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/images/generations", "tooltip": "API URL"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_API_KEY_HERE", "tooltip": "Your HyprLab API key"}),
                "response_format": (["url", "b64_json"], {"default": "url", "tooltip": "How the response data should be formatted"}),
            },
            "optional": {
                "input_images_array": ("IMAGE_ARRAY", {"tooltip": "Array of input images. SEEDEDIT-3 requires at least 1 image. Connect Image Array Builder node output here."}),
                "aspect_ratio": (cls.ASPECT_RATIO_CHOICES, {"default": "1:1", "tooltip": "🟢 SEEDREAM-3/DREAMINA-3.1: Aspect ratio | ❌ SEEDEDIT-3: Not supported"}),
                "legacy_size": (["small", "regular", "big"], {"default": "big", "tooltip": "🟢 SEEDREAM-3 ONLY: Legacy image dimensions"}),
                "resolution": (["1K", "2K"], {"default": "2K", "tooltip": "🟢 DREAMINA-3.1 ONLY: Image resolution (1K/2K)"}),
                "guidance_scale": ("FLOAT", {"default": 2.5, "min": 0.0, "max": 10.0, "step": 0.1, "tooltip": "🟢 SEEDREAM-3/SEEDEDIT-3: Prompt adherence (min 1.0 for SEEDREAM-3)"}),
                "enhance_prompt": ("BOOLEAN", {"default": False, "tooltip": "🟢 DREAMINA-3.1 ONLY: Enhance the prompt with LLM"}),
            }
        }

    def generate_seedream3_image(
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
        legacy_size="big",
        resolution="2K",
        guidance_scale=2.5,
        enhance_prompt=False
    ):
        if len(prompt) > 10000:
            raise ValueError("Prompt must not exceed 10,000 characters")
        if not prompt.strip():
            raise ValueError("Prompt must be a non-empty string")

        # Get first image from array if available
        image_input = None
        if input_images_array is not None and isinstance(input_images_array, list) and len(input_images_array) > 0:
            image_input = input_images_array[0]
            print(f"🟢 {model.upper()}: Using input image from array")

        # Validate model-specific requirements
        if model == "seededit-3" and image_input is None:
            raise ValueError("SEEDEDIT-3 model requires an input image")

        payload = {
            "model": model,
            "prompt": prompt,
            "response_format": response_format,
            "output_format": output_format
        }

        # Model-specific parameter handling
        if model == "dreamina-3.1":
            if aspect_ratio and aspect_ratio != "match_input_image":
                payload["aspect_ratio"] = aspect_ratio
            if resolution:
                payload["resolution"] = resolution
                print(f"🟢 DREAMINA-3.1: Using resolution parameter '{resolution}' (1K/2K)")
            if enhance_prompt is not None:
                payload["enhance_prompt"] = enhance_prompt
            if seed is not None and seed != 0:
                valid_seed = min(max(0, seed), 4294967295)
                payload["seed"] = valid_seed

        elif model == "seededit-3":
            if image_input:
                payload["image"] = image_input
                print("🟢 SEEDEDIT-3: Image input processed as required reference")
            if guidance_scale is not None:
                payload["guidance_scale"] = guidance_scale
            if aspect_ratio != "1:1":
                print("⚠️ SEEDEDIT-3: aspect_ratio parameter not supported by this model")

        elif model == "seedream-3":
            if aspect_ratio and aspect_ratio not in ["9:21", "match_input_image"]:
                payload["aspect_ratio"] = aspect_ratio
            elif aspect_ratio in ["9:21", "match_input_image"]:
                print(f"⚠️ SEEDREAM-3: '{aspect_ratio}' not supported, skipping aspect_ratio")
            if legacy_size:
                payload["size"] = legacy_size
                print(f"🟢 SEEDREAM-3: Using legacy size parameter '{legacy_size}' (small/regular/big)")
            if guidance_scale is not None:
                guidance_scale = max(1.0, guidance_scale)
                payload["guidance_scale"] = guidance_scale

        # Warn about unused parameters
        if model != "seedream-3" and legacy_size != "big":
            print(f"⚠️ {model.upper()}: 'legacy_size' parameter only supported by SEEDREAM-3")
        if model != "dreamina-3.1" and resolution != "2K":
            print(f"⚠️ {model.upper()}: 'resolution' parameter only supported by DREAMINA-3.1")
        if model != "dreamina-3.1" and enhance_prompt:
            print(f"⚠️ {model.upper()}: 'enhance_prompt' parameter only supported by DREAMINA-3.1")

        return self._make_api_call(payload, api_url, api_key, response_format, output_format, seed)


# Node mappings for ComfyUI
BYTEDANCE_NODE_CLASS_MAPPINGS = {
    "Leon_Seedream4_API_Node": Leon_Seedream4_API_Node,
    "Leon_Seedream3_API_Node": Leon_Seedream3_API_Node,
}

BYTEDANCE_NODE_DISPLAY_NAME_MAPPINGS = {
    "Leon_Seedream4_API_Node": "🤖 Leon Seedream 4 API",
    "Leon_Seedream3_API_Node": "🤖 Leon Seedream 3 API",
}
