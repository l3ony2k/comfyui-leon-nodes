# Import consolidated mappings from the .nodes sub-package
from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

# Optional: If you want to make other things from .nodes directly available, list them in .nodes.__all__
# and then you could do `from .nodes import *` if that was desired, but specific is often better.

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']