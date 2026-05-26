from ..base.hyprlab_base import HyprLabImageGenerationNodeBase

# Wan & Qwen Image Generation Nodes

WAN_SIZE_OPTIONS = [
    "1024*1024",
    "1K",
    "2K",
    "4K",
    "2048*2048",
    "4096*4096",
    "1280*720",
    "720*1280",
    "2048*1152",
    "1152*2048",
    "4096*2304",
    "2304*4096",
    "1024*768",
    "768*1024",
    "2048*1536",
    "1536*2048",
    "4096*3072",
    "3072*4096"
]

class Leon_Wan_Image_API_Node(HyprLabImageGenerationNodeBase):
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "image_url", "seed")
    FUNCTION = "generate_wan_image"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "A cute cat.", "tooltip": "Text description of the image to generate"}),
                "model": (["wan-2.7-image", "wan-2.7-image-pro"], {"default": "wan-2.7-image", "tooltip": "Wan image generation model (default: wan-2.7-image)"}),
                "size": (WAN_SIZE_OPTIONS, {"default": "1024*1024", "tooltip": "Size of the generated image (default: 1024*1024)"}),
                "output_format": (["png", "jpeg", "webp"], {"default": "png", "tooltip": "Format of the output image"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Random seed for reproducible results"}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/images/generations", "tooltip": "API URL"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_API_KEY_HERE", "tooltip": "Your HyprLab API key"}),
                "response_format": (["url", "b64_json"], {"default": "url", "tooltip": "Format of the response data"}),
            },
            "optional": {
                "image": ("IMAGE", {"tooltip": "Single input image"}),
                "image_url": ("STRING", {"multiline": False, "default": "", "tooltip": "Hosted image URL"}),
                "input_images_array": ("IMAGE_ARRAY", {"tooltip": "Array of input images. Connect Image Array Builder node output here."}),
            }
        }

    def generate_wan_image(
        self,
        prompt,
        model,
        size,
        output_format,
        seed,
        api_url,
        api_key,
        response_format,
        image=None,
        image_url="",
        input_images_array=None
    ):
        if not prompt.strip():
            raise ValueError("Prompt must be a non-empty string")

        payload = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "response_format": response_format,
            "output_format": output_format,
        }

        # Resolve image inputs strictly following the "images" payload key
        resolved_images = []
        if input_images_array is not None and isinstance(input_images_array, list):
            resolved_images = input_images_array[:9]  # max_files: 9
            print(f"🟢 {model}: Using {len(resolved_images)} input image(s) from array")
        else:
            resolved_image = self._resolve_image_input(image, image_url, field_name="images")
            if resolved_image:
                resolved_images = [resolved_image]
                print(f"🟢 {model}: Using single input image")

        if resolved_images:
            payload["images"] = resolved_images

        return self._make_api_call(payload, api_url, api_key, response_format, output_format, seed)


class Leon_Qwen_Image_API_Node(HyprLabImageGenerationNodeBase):
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "image_url", "seed")
    FUNCTION = "generate_qwen_image"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "A cute cat", "tooltip": "Text description of the image to generate"}),
                "model": (["qwen-image-2", "qwen-image-2-pro"], {"default": "qwen-image-2", "tooltip": "Qwen image generation model (default: qwen-image-2)"}),
                "aspect_ratio": (["1:1", "16:9", "9:16", "4:3", "3:4"], {"default": "1:1", "tooltip": "Aspect ratio of the generated image (default: 1:1)"}),
                "output_format": (["png", "jpeg", "webp"], {"default": "png", "tooltip": "Format of the output image"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Random seed for reproducible results"}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/images/generations", "tooltip": "API URL"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_API_KEY_HERE", "tooltip": "Your HyprLab API key"}),
                "response_format": (["url", "b64_json"], {"default": "url", "tooltip": "Format of the response data"}),
            },
            "optional": {
                "image": ("IMAGE", {"tooltip": "Required input image"}),
                "image_url": ("STRING", {"multiline": False, "default": "", "tooltip": "Hosted image URL"}),
            }
        }

    def generate_qwen_image(
        self,
        prompt,
        model,
        aspect_ratio,
        output_format,
        seed,
        api_url,
        api_key,
        response_format,
        image=None,
        image_url=""
    ):
        if not prompt.strip():
            raise ValueError("Prompt must be a non-empty string")

        payload = {
            "model": model,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "response_format": response_format,
            "output_format": output_format,
        }

        resolved_image = self._resolve_image_input(image, image_url, field_name="image")
        if resolved_image:
            payload["image"] = resolved_image

        return self._make_api_call(payload, api_url, api_key, response_format, output_format, seed)


# Node mappings for ComfyUI
QWEN_NODE_CLASS_MAPPINGS = {
    "Leon_Wan_Image_API_Node": Leon_Wan_Image_API_Node,
    "Leon_Qwen_Image_API_Node": Leon_Qwen_Image_API_Node,
}

QWEN_NODE_DISPLAY_NAME_MAPPINGS = {
    "Leon_Wan_Image_API_Node": "🤖 Leon Wan Image API",
    "Leon_Qwen_Image_API_Node": "🤖 Leon Qwen Image API",
}
