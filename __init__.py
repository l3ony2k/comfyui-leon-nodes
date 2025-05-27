from .leon_api_node import *

# Node class mappings for ComfyUI discovery
NODE_CLASS_MAPPINGS = {
    "Leon_Google_Image_API_Node": Leon_Google_Image_API_Node,
    "Leon_Luma_AI_Image_API_Node": Leon_Luma_AI_Image_API_Node,
    "Leon_Midjourney_Proxy_API_Node": Leon_Midjourney_Proxy_API_Node,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Leon_Google_Image_API_Node": "Leon Google Image API",
    "Leon_Luma_AI_Image_API_Node": "Leon Luma AI Image API",
    "Leon_Midjourney_Proxy_API_Node": "Leon Midjourney Proxy API",
}