from .base.hyprlab_base import HyprLabImageGenerationNodeBase

# FLUX Image Generation Nodes

class Leon_Flux_Image_API_Node(HyprLabImageGenerationNodeBase):
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "image_url", "seed")
    FUNCTION = "generate_flux_image"

    MODEL_MAPPING = {
        "FLUX 1.1 Pro Ultra": "flux-1.1-pro-ultra",
        "FLUX 1.1 Pro": "flux-1.1-pro",
        "FLUX Pro Canny": "flux-pro-canny",
        "FLUX Dev": "flux-dev",
        "FLUX Schnell": "flux-schnell",
        "FLUX Krea Dev": "flux-krea-dev"
    }
    ASPECT_RATIOS_ULTRA = ["21:9", "16:9", "3:2", "4:3", "5:4", "1:1", "4:5", "3:4", "2:3", "9:16", "9:21"]

    def __init__(self):
        super().__init__()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_choice": (list(cls.MODEL_MAPPING.keys()), {"default": "FLUX 1.1 Pro"}),
                "prompt": ("STRING", {"multiline": True, "default": "A stunning artistic photo"}),
                "response_format": (["url", "b64_json"], {"default": "url"}),
                "output_format": (["png", "jpeg", "webp"], {"default": "png"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/images/generations"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_HYPRLAB_API_KEY"}),
            },
            "optional": {
                # Legacy single image input for other models
                "input_image_prompt_socket": ("IMAGE", { "tooltip": "Image for image guidance. Must be at least 256x256 pixels (FLUX 1.1 Pro Ultra, FLUX 1.1 Pro, FLUX Pro Canny)."}),
                "input_image_prompt_url": ("STRING", {"multiline": False, "default": "", "tooltip": "Image guidance URL (hosted image for image_prompt/image fields)"}),
                "image_prompt_strength": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01, "tooltip": "Strength of image_prompt (FLUX 1.1 Pro Ultra only)"}),
                "aspect_ratio": (cls.ASPECT_RATIOS_ULTRA, {"default": "1:1", "tooltip": "Aspect ratio (FLUX 1.1 Pro Ultra, FLUX Krea Dev)"}),
                "raw": ("BOOLEAN", {"default": False, "tooltip": "Return raw output (FLUX 1.1 Pro Ultra only)"}),
                "steps": ("INT", {"default": 30, "min": 1, "max": 50, "tooltip": "Number of steps (FLUX 1.1 Pro, FLUX Pro Canny, FLUX Dev, FLUX Schnell)"}),
                "height": ("INT", {"default": 1024, "min": 256, "max": 1440, "step": 32, "tooltip": "Image height, multiple of 32 (FLUX 1.1 Pro, FLUX Pro Canny, FLUX Dev, FLUX Schnell)"}),
                "width": ("INT", {"default": 1024, "min": 256, "max": 1440, "step": 32, "tooltip": "Image width, multiple of 32 (FLUX 1.1 Pro, FLUX Pro Canny, FLUX Dev, FLUX Schnell)"}),
                "prompt_strength": ("FLOAT", {"default": 0.8, "min": 0.0, "max": 1.0, "step": 0.01, "tooltip": "Prompt strength for image-to-image (FLUX Krea Dev only)"}),
                "num_inference_steps": ("INT", {"default": 20, "min": 4, "max": 50, "tooltip": "Number of inference steps (FLUX Krea Dev only)"}),
                "guidance": ("FLOAT", {"default": 3.5, "min": 0.0, "max": 10.0, "step": 0.1, "tooltip": "Guidance scale (FLUX Krea Dev only)"}),
            }
        }

    def generate_flux_image(self, model_choice, prompt, response_format, output_format, seed, api_url, api_key,
                              input_image_prompt_socket=None, input_image_prompt_url="", image_prompt_strength=0.5, aspect_ratio="1:1", raw=False,
                              steps=30, height=1024, width=1024, prompt_strength=0.8, num_inference_steps=20, guidance=3.5):

        actual_model_name = self.MODEL_MAPPING.get(model_choice)
        if not actual_model_name:
            raise ValueError(f"Invalid model choice: {model_choice}.")

        payload = {
            "model": actual_model_name, "prompt": prompt,
            "response_format": response_format, "output_format": output_format,
        }
        if not prompt.strip():
            raise ValueError("Prompt must be a non-empty string.")

        actual_image_prompt_payload = self._resolve_image_input(
            input_image_prompt_socket, input_image_prompt_url, field_name="image_prompt"
        )

        if model_choice == "FLUX 1.1 Pro Ultra":
            if actual_image_prompt_payload: 
                payload["image_prompt"] = actual_image_prompt_payload
            payload["image_prompt_strength"] = image_prompt_strength
            if aspect_ratio != self.INPUT_TYPES()["optional"]["aspect_ratio"][1]["default"]: 
                 payload["aspect_ratio"] = aspect_ratio
            payload["raw"] = raw
        elif model_choice in ["FLUX 1.1 Pro", "FLUX Pro Canny"]:
            if actual_image_prompt_payload: 
                payload["image_prompt"] = actual_image_prompt_payload
            payload["steps"] = steps
            payload["height"] = height
            payload["width"] = width
        elif model_choice in ["FLUX Dev", "FLUX Schnell"]:
            payload["steps"] = steps
            payload["height"] = height
            payload["width"] = width
        elif model_choice == "FLUX Krea Dev":
            if actual_image_prompt_payload:
                payload["image"] = actual_image_prompt_payload
                payload["prompt_strength"] = prompt_strength
            if aspect_ratio != self.INPUT_TYPES()["optional"]["aspect_ratio"][1]["default"]:
                payload["aspect_ratio"] = aspect_ratio
            payload["num_inference_steps"] = num_inference_steps
            payload["guidance"] = guidance

        if model_choice in ["FLUX 1.1 Pro", "FLUX Pro Canny", "FLUX Dev", "FLUX Schnell"]:
            if height % 32 != 0: raise ValueError(f"Height must be a multiple of 32. Got {height}.")
            if width % 32 != 0: raise ValueError(f"Width must be a multiple of 32. Got {width}.")

        return self._make_api_call(payload, api_url, api_key, response_format, output_format, seed)


class Leon_Flux_2_Image_API_Node(HyprLabImageGenerationNodeBase):
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "image_url", "seed")
    FUNCTION = "generate_flux2_image"

    MODEL_MAPPING = {
        "FLUX 2 Pro": "flux-2-pro",
        "FLUX 2 Flex": "flux-2-flex"
    }
    ASPECT_RATIOS = ["match_input_image", "1:1", "16:9", "3:2", "2:3", "4:5", "5:4", "9:16", "3:4", "4:3"]
    RESOLUTION_CHOICES = ["match_input_image", "0.5 MP", "1 MP", "2 MP", "4 MP"]

    def __init__(self):
        super().__init__()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_choice": (list(cls.MODEL_MAPPING.keys()), {"default": "FLUX 2 Pro"}),
                "prompt": ("STRING", {"multiline": True, "default": "A stunning artistic photo"}),
                "response_format": (["url", "b64_json"], {"default": "url"}),
                "output_format": (["png", "jpeg", "webp"], {"default": "png"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/images/generations"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_HYPRLAB_API_KEY"}),
            },
            "optional": {
                "input_images_array": ("IMAGE_ARRAY", {"tooltip": "Array of input images for FLUX 2 Pro (up to 8) or FLUX 2 Flex (up to 10). Connect Image Array Builder node output here."}),
                "aspect_ratio": (cls.ASPECT_RATIOS, {"default": "1:1", "tooltip": "Aspect ratio for generated image"}),
                "resolution": (cls.RESOLUTION_CHOICES, {"default": "1 MP", "tooltip": "Image resolution"}),
                "steps": ("INT", {"default": 30, "min": 1, "max": 50, "tooltip": "Number of steps (FLUX 2 Flex only)"}),
                "guidance": ("FLOAT", {"default": 3.5, "min": 1.5, "max": 10.0, "step": 0.1, "tooltip": "Guidance scale (FLUX 2 Flex only, range: 1.5-10)"}),
            }
        }

    def generate_flux2_image(self, model_choice, prompt, response_format, output_format, seed, api_url, api_key,
                             input_images_array=None, aspect_ratio="1:1", resolution="1 MP",
                             steps=30, guidance=3.5):

        actual_model_name = self.MODEL_MAPPING.get(model_choice)
        if not actual_model_name:
            raise ValueError(f"Invalid model choice: {model_choice}.")

        if not prompt.strip():
            raise ValueError("Prompt must be a non-empty string.")

        payload = {
            "model": actual_model_name,
            "prompt": prompt,
            "response_format": response_format,
            "output_format": output_format,
        }

        # Handle multi-image input
        if input_images_array is not None and isinstance(input_images_array, list):
            max_images = 8 if model_choice == "FLUX 2 Pro" else 10
            input_images = input_images_array[:max_images]
            
            if input_images:
                payload["input_images"] = input_images
                print(f"🟢 {model_choice}: Using {len(input_images)} input image(s) (preserving original dimensions)")

        # Add aspect_ratio and resolution
        if aspect_ratio and aspect_ratio != "1:1":
            payload["aspect_ratio"] = aspect_ratio
        if resolution and resolution != "1 MP":
            payload["resolution"] = resolution

        # FLUX 2 Flex specific parameters
        if model_choice == "FLUX 2 Flex":
            payload["steps"] = steps
            if guidance < 1.5 or guidance > 10.0:
                raise ValueError(f"FLUX 2 Flex guidance must be between 1.5 and 10.0. Got {guidance}.")
            payload["guidance"] = guidance
            print(f"🟢 FLUX 2 Flex: steps={steps}, guidance={guidance}")

        return self._make_api_call(payload, api_url, api_key, response_format, output_format, seed)


class Leon_Flux_Kontext_API_Node(HyprLabImageGenerationNodeBase):
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("image", "image_url", "seed")
    FUNCTION = "generate_flux_kontext_image"

    MODEL_CHOICES = ["flux-kontext-max", "flux-kontext-pro", "flux-kontext-dev"]
    ASPECT_RATIO_CHOICES = [
        "match_input_image", "1:1", "16:9", "9:16", "4:3", "3:4", 
        "3:2", "2:3", "4:5", "5:4", "21:9", "9:21", "2:1", "1:2"
    ]

    def __init__(self):
        super().__init__()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": (cls.MODEL_CHOICES, {"default": "flux-kontext-pro"}),
                "prompt": ("STRING", {"multiline": True, "default": "A detailed artistic scene"}),
                "response_format": (["url", "b64_json"], {"default": "url"}),
                "output_format": (["png", "jpeg", "webp"], {"default": "png"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/images/generations"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_HYPRLAB_API_KEY"}),
            },
            "optional": {
                "input_image": ("IMAGE", {"tooltip": "Input image (required for flux-kontext-dev)"}),
                "input_image_url": ("STRING", {"multiline": False, "default": "", "tooltip": "Hosted image URL for flux-kontext image inputs"}),
                "aspect_ratio": (cls.ASPECT_RATIO_CHOICES, {"default": "1:1"}),
                "num_inference_steps": ("INT", {"default": 20, "min": 4, "max": 50, "tooltip": "Number of inference steps (flux-kontext-dev only)"}),
                "guidance": ("FLOAT", {"default": 3.5, "min": 0.0, "max": 10.0, "step": 0.1, "tooltip": "Guidance scale (flux-kontext-dev only)"}),
            }
        }

    def generate_flux_kontext_image(self, model, prompt, response_format, output_format, seed, 
                                      api_url, api_key, input_image=None, input_image_url="", aspect_ratio="1:1", 
                                      num_inference_steps=20, guidance=3.5):

        if not prompt.strip():
            raise ValueError("Prompt must be a non-empty string.")

        # Validate model-specific requirements
        resolved_input_image = self._resolve_image_input(
            input_image, input_image_url, field_name="input_image"
        )

        if model == "flux-kontext-dev" and not resolved_input_image:
            raise ValueError("flux-kontext-dev model requires an input image")

        payload = {
            "model": model,
            "prompt": prompt,
            "response_format": response_format,
            "output_format": output_format,
        }

        if resolved_input_image:
            payload["input_image"] = resolved_input_image
        
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
            if not resolved_input_image and aspect_ratio == "match_input_image":
                 pass

        # Add flux-kontext-dev specific parameters
        if model == "flux-kontext-dev":
            payload["num_inference_steps"] = num_inference_steps
            payload["guidance"] = guidance

        return self._make_api_call(payload, api_url, api_key, response_format, output_format, seed)




# Node mappings for ComfyUI
FLUX_NODE_CLASS_MAPPINGS = {
    "Leon_Flux_Image_API_Node": Leon_Flux_Image_API_Node,
    "Leon_Flux_2_Image_API_Node": Leon_Flux_2_Image_API_Node,
    "Leon_Flux_Kontext_API_Node": Leon_Flux_Kontext_API_Node,
}

FLUX_NODE_DISPLAY_NAME_MAPPINGS = {
    "Leon_Flux_Image_API_Node": "🤖 Leon FLUX Image API",
    "Leon_Flux_2_Image_API_Node": "🤖 Leon FLUX 2 Image API",
    "Leon_Flux_Kontext_API_Node": "🤖 Leon FLUX Kontext API",
}
