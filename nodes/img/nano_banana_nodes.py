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


# Node mappings for ComfyUI
NANO_BANANA_NODE_CLASS_MAPPINGS = {
    "Leon_Nano_Banana_API_Node": Leon_Nano_Banana_API_Node,
}

NANO_BANANA_NODE_DISPLAY_NAME_MAPPINGS = {
    "Leon_Nano_Banana_API_Node": "🤖 Leon Nano Banana API",
}
