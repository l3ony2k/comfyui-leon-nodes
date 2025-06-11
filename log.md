## ComfyUI Leon API Nodes Development Log

This log documents the development and troubleshooting process for the custom API nodes in `leon_api_node.py`.

### Initial Goal: Add Multiple API-based Image Generation Nodes

- **Google Imagen Node**: Implement a node to interact with Google Imagen models via the HyprLab API.
- **Luma AI Node**: Implement a node for Luma AI (photon, photon-flash) via HyprLab API.
- **Midjourney Proxy Node**: Implement a node to interact with a self-hosted Midjourney proxy.

### Core Development Steps & Architectural Decisions

1.  **HyprLab API Base Class (`HyprLabImageGenerationNodeBase`):**
    *   Created to encapsulate common logic for nodes interacting with the HyprLab `/images/generations` endpoint.
    *   Handles API authentication, request formation (POST), response handling (b64_json and URL), image downloading, and conversion to an RGBA PyTorch tensor.
    *   Includes Tenacity for retry logic on API calls.
    *   Ensures output tensors are always 4-channel (RGBA) by explicitly adding an alpha channel if the source image is RGB. This addressed an early `RuntimeError` related to tensor dimension mismatches when interacting with downstream nodes expecting RGBA.

2.  **Google Imagen Node (`Leon_Google_Image_API_Node`):**
    *   Inherits from `HyprLabImageGenerationNodeBase`.
    *   Defines specific `INPUT_TYPES` for Google Imagen (prompt, model, aspect_ratio, output_format, seed, api_url, api_key, response_format).
    *   The `generate_image` method constructs the Google Imagen-specific payload and calls the base class's `_make_api_call`.

3.  **Luma AI Node (`Leon_Luma_AI_Image_API_Node`):**
    *   Inherits from `HyprLabImageGenerationNodeBase`.
    *   Defines `INPUT_TYPES` based on Luma AI documentation (prompt, model, output_format, seed, api_url, api_key, response_format, and optional parameters like aspect_ratio, image_reference_url, style_reference_url, etc.).
    *   The `generate_luma_image` method constructs the Luma AI-specific payload, adding optional parameters if provided, and calls `_make_api_call`.

4.  **Midjourney Proxy Node (`Leon_Midjourney_Proxy_API_Node`):**
    *   Implemented as a standalone class due to its different API interaction pattern (submit task, then poll for results).
    *   **Inputs**: Initially `mj_proxy_endpoint`, `prompt`, `bot_type`, etc. Refactored to include `mj_api_secret`, `x_api_key`, `account_filter_remark`, `base64_array_json` based on detailed API examples.
    *   **Outputs**: `image` (RGBA tensor), `image_url`, `task_id`. Refactored to add `final_prompt_from_api` and `message_hash`.
    *   **Logic**:
        *   Submits an `/mj/submit/imagine` request to the proxy using appropriate headers (`mj-api-secret`, `X-Api-Key`) and payload (`accountFilter`, `base64Array`).
        *   Polls the `/mj/task/{id}/fetch` endpoint for task status, ensuring headers are also sent for these calls.
        *   Handles `SUCCESS` (downloads image, converts to RGBA tensor) and `FAILURE` states.
        *   Extracts and returns `finalPrompt` and `messageHash` from the task data upon success.

5.  **Image Utility Node (`Leon_Image_Split_4Grid_Node`):**
    *   Created to split a 2x2 grid image into four separate image outputs (TL, TR, BL, BR).
    *   Input: Single image tensor.
    *   Outputs: Four image tensors.
    *   Placed in a new category: `Leon_Utils`.

6.  **String Utility Node (`Leon_String_Combine_Node`):**
    *   Created to combine two strings with a user-defined linking element.
    *   Inputs: `string_1`, `string_2`, `linking_element` (defaults to a space).
    *   Output: `combined_string`.
    *   Placed in a new category: `Leon_Utils`.

7.  **FLUX Image API Node (`Leon_Flux_Image_API_Node`):**
    *   Inherits from `HyprLabImageGenerationNodeBase`.
    *   Supports multiple FLUX model variants (`FLUX 1.1 Pro Ultra`, `FLUX 1.1 Pro`, `FLUX Pro Canny`, `FLUX Dev`, `FLUX Schnell`) via HyprLab, based on [HyprLab Black Forest Labs Docs](https://docs.hyprlab.io/browse-models/model-list/black-forest-labs).
    *   Default model set to `FLUX 1.1 Pro`.
    *   **Inputs**: `model_choice`, `prompt`, `response_format`, `output_format`, `seed`, `api_url`, `api_key`, and optional model-specific parameters (`image_prompt`, `image_prompt_strength`, `aspect_ratio`, `raw`, `steps`, `height`, `width`) with tooltips indicating applicability.
    *   Dynamically constructs the API payload based on the selected FLUX model variant, mapping display names to specific API model strings (e.g., `flux-1.1-pro-ultra`, `flux-1.1-pro`, `flux-pro-canny`, `flux-dev`, `flux-schnell`).
    *   `FLUX Pro Canny` assumes similar parameters to `FLUX 1.1 Pro` (including `image_prompt`, `steps`, `height`, `width`).
    *   Includes validation for `height` and `width` (must be multiples of 32) for relevant models.
    *   Placed in the `Leon_API` category.

8.  **Node Registration & `__init__.py`:**
    *   All nodes are registered in `NODE_CLASS_MAPPINGS` and `NODE_DISPLAY_NAME_MAPPINGS` at the end of `leon_api_node.py`.
    *   **Crucially**, these mappings must also be correctly updated in the project's root `__init__.py` file for ComfyUI to discover all nodes, especially after adding new ones like the image split, string combine, and FLUX nodes. Failure to do so was a cause for new nodes not appearing.

### Troubleshooting: Nodes Not Appearing in ComfyUI

**Symptom**: After adding new nodes, they were sometimes not visible in ComfyUI.

**Troubleshooting Steps Taken:**

1.  **Standard Checks**: Hard browser refresh, checking ComfyUI console errors, deleting `__pycache__` folders (in the node directory, custom_nodes directory, and even the main ComfyUI directory).
2.  **Node Definition Review**: Ensuring `CATEGORY`, `RETURN_TYPES`, `RETURN_NAMES`, `FUNCTION`, and `INPUT_TYPES` were explicitly and correctly defined in each node class.
3.  **`__init__.py` Verification**: **This was a key recurring point.** Ensuring that `NODE_CLASS_MAPPINGS` and `NODE_DISPLAY_NAME_MAPPINGS` in the main `__init__.py` of the custom node package were updated with *every* new node. Importing with `from .leon_api_node import *` is not enough; the mappings need to be explicitly maintained in `__init__.py` as well for ComfyUI's loader.

**Outcome of Troubleshooting**: Consistent application of cache clearing and meticulous updates to both `leon_api_node.py` mappings and `__init__.py` mappings resolved visibility issues.

### Bug Fixes During Development

*   **`TypeError` in `Leon_Luma_AI_Image_API_Node`**: Corrected an issue where the default `aspect_ratio` was being accessed incorrectly from the `INPUT_TYPES` tuple. The access method `self.INPUT_TYPES()["optional"]["aspect_ratio"]["default"]` was changed to `self.INPUT_TYPES()["optional"]["aspect_ratio"][1]["default"]` to correctly index the dictionary within the tuple.
*   **Luma AI Node Payload Omission**: Fixed an issue in `Leon_Luma_AI_Image_API_Node` where the `aspect_ratio` was not being added to the API request payload if its value was the same as the default. The logic was changed to always include the `aspect_ratio` from the UI in the payload.

### Key Takeaways for Future Development

*   **`__init__.py` is CRITICAL**: For custom node packages, `__init__.py` is not just for imports. ComfyUI relies on its `NODE_CLASS_MAPPINGS` and `NODE_DISPLAY_NAME_MAPPINGS` to discover nodes. *Always update it when adding or renaming nodes.*
*   **Cache Clearing**: Aggressively clear `__pycache__` (in multiple relevant locations) and browser cache when nodes don't appear or update.
*   **Explicit Node Attributes**: Be explicit with node registration attributes in each class.
*   **Console Logging**: Use `print()` statements in your node file during development (e.g., at import time, before class definitions, in `__init__` methods of nodes) to trace execution if ComfyUI has trouble loading them. Check the ComfyUI console.
*   **Clear `__pycache__`**: This is often a first-line fix for custom node update issues in ComfyUI.
*   **Explicit Node Attributes**: For node registration attributes (`CATEGORY`, `RETURN_TYPES`, `RETURN_NAMES`, `FUNCTION`, `INPUT_TYPES`), while inheritance is a good Python practice, being explicit in each node class can prevent subtle loading issues with ComfyUI.
*   **Console Errors are Gold**: Always check the ComfyUI startup console for Python errors. They often point directly to the problematic code in a custom node file.
*   **Iterative Testing**: When adding multiple nodes or complex features, test frequently to catch integration issues early.
*   **Base Classes for Common Logic**: Using base classes (like `HyprLabImageGenerationNodeBase`) is effective for keeping code DRY when multiple nodes share significant functionality (e.g., interacting with the same API provider under a common path).

9.  **ImgBB Upload Utility Node (`Leon_ImgBB_Upload_Node`):**
    *   Created to upload images to ImgBB.
    *   Inputs: `image` (tensor), `api_key` (string), `expire` (boolean, optional), `expiration_time_seconds` (int, optional).
    *   Output: `image_url` (string).
    *   Converts tensor to PIL, saves as PNG to buffer, base64 encodes, and posts to ImgBB API.
    *   Handles API key validation, expiration parameter, and error responses.
    *   Placed in the `Leon_Utils` category.
    *   Added to `NODE_CLASS_MAPPINGS` and `NODE_DISPLAY_NAME_MAPPINGS` in both `leon_api_node.py` and the root `__init__.py`.

### Major Refactoring: Splitting `leon_api_node.py`

To improve maintainability as the number of nodes grew, `leon_api_node.py` was split into two separate files:

1.  **`api_nodes.py`**: Contains all API-interacting nodes:
    *   `HyprLabImageGenerationNodeBase` (base class)
    *   `Leon_Google_Image_API_Node`
    *   `Leon_Luma_AI_Image_API_Node`
    *   `Leon_Midjourney_Proxy_API_Node`
    *   `Leon_Flux_Image_API_Node`
    *   This file includes its own `API_NODE_CLASS_MAPPINGS` and `API_NODE_DISPLAY_NAME_MAPPINGS` specific to these nodes.

2.  **`utility_nodes.py`**: Contains all utility nodes:
    *   `Leon_Image_Split_4Grid_Node`
    *   `Leon_String_Combine_Node`
    *   `Leon_ImgBB_Upload_Node`
    *   This file includes its own `UTIL_NODE_CLASS_MAPPINGS` and `UTIL_NODE_DISPLAY_NAME_MAPPINGS` specific to these nodes.

3.  **`__init__.py` Update**: The main `__init__.py` for the `comfyui-leon-nodes` package was updated to:
    *   Import `API_NODE_CLASS_MAPPINGS`, `API_NODE_DISPLAY_NAME_MAPPINGS` from `.api_nodes`.
    *   Import `UTIL_NODE_CLASS_MAPPINGS`, `UTIL_NODE_DISPLAY_NAME_MAPPINGS` from `.utility_nodes`.
    *   The global `NODE_CLASS_MAPPINGS` and `NODE_DISPLAY_NAME_MAPPINGS` are now constructed by merging the mappings from these two files (e.g., `NODE_CLASS_MAPPINGS = {**API_NODE_CLASS_MAPPINGS, **UTIL_NODE_CLASS_MAPPINGS}`).
    *   Added `__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']`.

4.  **Deletion**: The original `leon_api_node.py` file was deleted after its contents were successfully migrated.

This refactoring organizes the codebase more logically and makes it easier to manage and extend different types of nodes separately.

10. **FLUX Kontext API Node (`Leon_Flux_Kontext_API_Node`):**
    *   Added to `api_nodes.py` and inherits from `HyprLabImageGenerationNodeBase`.
    *   Supports `flux-kontext-max` and `flux-kontext-pro` models.
    *   Category: `Leon_API`.
    *   Display Name: `🤖 Leon FLUX Kontext API`.
    *   **Inputs**:
        *   `model`: Dropdown for FLUX Kontext model selection.
        *   `prompt`: Required string.
        *   `input_image` (IMAGE, optional): If provided, converted to base64 PNG data URI and sent in payload.
        *   `aspect_ratio`: Dropdown including `match_input_image` and standard ratios.
        *   Standard HyprLab inputs: `response_format`, `output_format`, `seed`, `api_url`, `api_key`.
    *   The `generate_flux_kontext_image` method constructs the payload, including the optional base64 `input_image` and `aspect_ratio`, then calls `_make_api_call`.
    *   Automatically included in `__init__.py` mappings via the consolidated approach.

11. **Enhanced Image Inputs for Luma and FLUX Nodes:**
    *   The `_tensor_to_base64_data_uri` helper method was moved from `Leon_Flux_Kontext_API_Node` to the base class `HyprLabImageGenerationNodeBase` for wider use.
    *   **`Leon_Luma_AI_Image_API_Node` Updates**:
        *   Added optional IMAGE input sockets:
            *   `input_image_ref_socket` (for `image_reference_url`)
            *   `input_style_ref_socket` (for `style_reference_url`)
            *   `input_char_ref_socket` (for `character_reference_url`)
        *   The node logic now prioritizes these socket inputs. If an image is provided via a socket, it's converted to a base64 data URI and used for the respective API payload parameter, overriding the corresponding string URL input.
        *   Tooltips and prompt validation messages were updated.
    *   **`Leon_Flux_Image_API_Node` Updates**:
        *   Added an optional IMAGE input socket: `input_image_prompt_socket`.
        *   The node logic now prioritizes this socket. If an image is provided, it's converted to a base64 data URI and used for the `image_prompt` API parameter, overriding the string URL `image_prompt` input.
        *   Tooltips were updated.

12. **Streamlined Image Inputs (Socket Only) for Luma and FLUX Nodes:**
    *   Following the addition of image socket inputs, the corresponding string URL input fields were removed from both `Leon_Luma_AI_Image_API_Node` and `Leon_Flux_Image_API_Node` to simplify the UI and avoid redundancy.
    *   **`Leon_Luma_AI_Image_API_Node` Changes**:
        *   Removed `image_reference_url`, `style_reference_url`, and `character_reference_url` string inputs from `INPUT_TYPES` and the `generate_luma_image` method.
        *   Image data for references now comes exclusively from `input_image_ref_socket`, `input_style_ref_socket`, and `input_char_ref_socket`.
    *   **`Leon_Flux_Image_API_Node` Changes**:
        *   Removed the `image_prompt` string input from `INPUT_TYPES` and the `generate_flux_image` method.
        *   The `image_prompt` payload parameter is now solely derived from `input_image_prompt_socket`.
        *   Tooltips were updated.

### Project Structure Refactoring (II)

To further improve organization and prepare for more complex node development, the project was restructured:

1.  **`nodes` Subdirectory Created**: A new directory named `nodes` was created at the root of the `comfyui-leon-nodes` package.

2.  **File Relocations & Creation**:
    *   The existing `api_nodes.py` (containing HyprLab-based API nodes) was moved to `nodes/api_nodes.py`.
    *   The existing `utility_nodes.py` was moved to `nodes/utility_nodes.py`.
    *   **`Leon_Midjourney_Proxy_API_Node` Extraction**: This node was moved from `api_nodes.py` into its own dedicated file: `nodes/midjourney_proxy_node.py`. This file now contains the `Leon_Midjourney_Proxy_API_Node` class, its specific imports, and its own mappings (`MJ_PROXY_NODE_CLASS_MAPPINGS`, `MJ_PROXY_NODE_DISPLAY_NAME_MAPPINGS`).

3.  **Updated `nodes/api_nodes.py`**: After moving the Midjourney node, this file was updated to remove its class definition and mappings.

4.  **New `nodes/__init__.py`**: This file was created to act as a central point for aggregating node mappings within the `nodes` subdirectory. It imports:
    *   `API_NODE_CLASS_MAPPINGS`, `API_NODE_DISPLAY_NAME_MAPPINGS` from `.api_nodes`
    *   `MJ_PROXY_NODE_CLASS_MAPPINGS`, `MJ_PROXY_NODE_DISPLAY_NAME_MAPPINGS` from `.midjourney_proxy_node`
    *   `UTIL_NODE_CLASS_MAPPINGS`, `UTIL_NODE_DISPLAY_NAME_MAPPINGS` from `.utility_nodes`
    It then consolidates these into package-level `NODE_CLASS_MAPPINGS` and `NODE_DISPLAY_NAME_MAPPINGS` and exports them via `__all__`.

5.  **Updated Root `__init__.py`**:
    *   The main `__init__.py` (at `comfyui-leon-nodes/__init__.py`) was simplified to import the consolidated `NODE_CLASS_MAPPINGS` and `NODE_DISPLAY_NAME_MAPPINGS` directly from the `.nodes` sub-package (e.g., `from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS`).

This structure provides a clearer separation of node types and makes the project more scalable. 