from ..base.hyprlab_base import HyprLabImageGenerationNodeBase

# Qwen Image Generation Nodes

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
                "model": (["qwen-image-max","qwen-image"], {"default": "qwen-image-max", "tooltip": "Qwen image generation model"}),
                "output_format": (["png", "jpeg", "webp"], {"default": "png", "tooltip": "Format of the output image"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Random seed for reproducible results"}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/images/generations", "tooltip": "API URL"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_API_KEY_HERE", "tooltip": "Your HyprLab API key"}),
                "response_format": (["url", "b64_json"], {"default": "url", "tooltip": "Format of the response data"}),
                "aspect_ratio": (["1:1", "16:9", "9:16", "4:3", "3:4"], {"default": "1:1", "tooltip": "Aspect ratio of the generated image"}),
            },
            "optional": {
                "image": ("IMAGE", {"tooltip": "Single input image"}),
                "image_url": ("STRING", {"multiline": False, "default": "", "tooltip": "Hosted image URL"}),
                "input_images_array": ("IMAGE_ARRAY", {"tooltip": "Array of input images. Connect Image Array Builder node output here."}),
            }
        }

    def generate_qwen_image(
        self,
        prompt,
        model,
        output_format,
        seed,
        api_url,
        api_key,
        response_format,
        aspect_ratio="1:1",
        image=None,
        image_url="",
        input_images_array=None
    ):
        if not prompt.strip():
            raise ValueError("Prompt must be a non-empty string")

        payload = {
            "model": model,
            "prompt": prompt,
            "response_format": response_format,
            "output_format": output_format,
            "aspect_ratio": aspect_ratio
        }

        if input_images_array is not None and isinstance(input_images_array, list):
            payload["image"] = input_images_array
            print(f"🟢 {model}: Using {len(input_images_array)} input image(s)")
        else:
            resolved_image = self._resolve_image_input(image, image_url, field_name="image")
            if resolved_image:
                payload["image"] = resolved_image
        
        return self._make_api_call(payload, api_url, api_key, response_format, output_format, seed)
class Leon_Qwen_Image_Edit_API_Node(HyprLabImageGenerationNodeBase):
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "image_url", "seed")
    FUNCTION = "generate_qwen_image_edit"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "Edit the image to look like a watercolor painting", "tooltip": "Text instruction for editing"}),
                "model": (["qwen-image-edit"], {"default": "qwen-image-edit", "tooltip": "Qwen image edit model"}),
                "response_format": (["url", "b64_json"], {"default": "url", "tooltip": "Format of the response data"}),
                "output_format": (["png", "jpeg", "webp"], {"default": "png", "tooltip": "Output image format"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Random seed for reproducible results"}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/images/generations", "tooltip": "API URL"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_API_KEY_HERE", "tooltip": "Your HyprLab API key"}),
            },
            "optional": {
                "input_image": ("IMAGE", {"tooltip": "Image to edit (URL/Data URI is generated from this input)"}),
                "input_image_url": ("STRING", {"multiline": False, "default": "", "tooltip": "Optional hosted image URL to edit (use instead of socket input when needed)"}),
                "aspect_ratio": (["1:1", "16:9", "9:16", "4:3", "3:4"], {"default": "1:1", "tooltip": "Aspect ratio of the generated image"}),
            }
        }

    def generate_qwen_image_edit(
        self,
        prompt,
        model,
        response_format,
        output_format,
        seed,
        api_url,
        api_key,
        input_image=None,
        input_image_url="",
        aspect_ratio="1:1",
    ):
        if not prompt.strip():
            raise ValueError("Prompt must be a non-empty string")

        resolved_input_image = self._resolve_image_input(
            input_image, input_image_url, field_name="input_image"
        )
        if not resolved_input_image:
            raise ValueError("input_image (tensor or URL) is required for qwen-image-edit")

        payload = {
            "model": model,
            "prompt": prompt,
            "response_format": response_format,
            "output_format": output_format,
            "image": resolved_input_image,
        }

        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio

        return self._make_api_call(payload, api_url, api_key, response_format, output_format, seed)


# Node mappings for ComfyUI
QWEN_NODE_CLASS_MAPPINGS = {
    "Leon_Qwen_Image_API_Node": Leon_Qwen_Image_API_Node,
    "Leon_Qwen_Image_Edit_API_Node": Leon_Qwen_Image_Edit_API_Node,
}

QWEN_NODE_DISPLAY_NAME_MAPPINGS = {
    "Leon_Qwen_Image_API_Node": "🤖 Leon Qwen Image API",
    "Leon_Qwen_Image_Edit_API_Node": "🤖 Leon Qwen Image Edit API",
}
