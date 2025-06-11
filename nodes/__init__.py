# Import mappings from individual node files
from .api_nodes import API_NODE_CLASS_MAPPINGS, API_NODE_DISPLAY_NAME_MAPPINGS
from .midjourney_proxy_node import MJ_PROXY_NODE_CLASS_MAPPINGS, MJ_PROXY_NODE_DISPLAY_NAME_MAPPINGS
from .utility_nodes import UTIL_NODE_CLASS_MAPPINGS, UTIL_NODE_DISPLAY_NAME_MAPPINGS

# Consolidate all mappings for ComfyUI discovery
NODE_CLASS_MAPPINGS = {
    **API_NODE_CLASS_MAPPINGS,
    **MJ_PROXY_NODE_CLASS_MAPPINGS,
    **UTIL_NODE_CLASS_MAPPINGS,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    **API_NODE_DISPLAY_NAME_MAPPINGS,
    **MJ_PROXY_NODE_DISPLAY_NAME_MAPPINGS,
    **UTIL_NODE_DISPLAY_NAME_MAPPINGS,
}

# __all__ helps define the public API of this module when using `from .nodes import *`
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS'] 