# ComfyUI Leon API Nodes

A custom ComfyUI node for generating images using Google's Imagen models via the HyprLab API.

## Overview

This package provides a custom node called `Leon_Google_Image_API_Node` that integrates Google's Imagen models (imagen-4, imagen-3, imagen-3-fast) into ComfyUI workflows through the HyprLab API service.

## Features

- **Google Imagen Models**: Support for imagen-4, imagen-3, and imagen-3-fast
- **Multiple Aspect Ratios**: 1:1, 3:4, 4:3, 9:16, 16:9
- **Output Formats**: PNG, JPEG, WebP
- **Response Formats**: URL or Base64 JSON
- **Seed Support**: For reproducible image generation
- **Error Handling**: Robust retry mechanism with exponential backoff
- **Validation**: Input validation including prompt length limits (10,000 characters)

## Installation

1. Clone or copy this repository to your ComfyUI custom nodes directory:
   ```
   cd ComfyUI/custom_nodes/
   git clone <repository-url> comfyui-leon-nodes
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Restart ComfyUI

## Usage

### Node: Leon Google Image API

The main node for generating images with Google's Imagen models.

#### Inputs

**Required:**
- `prompt` (STRING): Main text input to guide image generation (max 10,000 characters)
- `model` (COMBO): Choose from imagen-4, imagen-3, or imagen-3-fast
- `aspect_ratio` (COMBO): Select from 1:1, 3:4, 4:3, 9:16, 16:9
- `output_format` (COMBO): Choose PNG, JPEG, or WebP
- `seed` (INT): Random seed for reproducible results
- `api_url` (STRING): HyprLab API base URL (default: https://api.hyprlab.io/v1)
- `api_key` (STRING): Your HyprLab API key

**Optional:**
- `response_format` (COMBO): Choose between "url" or "b64_json"

#### Outputs

- `image` (IMAGE): Generated image as ComfyUI tensor
- `image_url` (STRING): Image URL or base64 data URL
- `seed` (INT): The seed used for generation

## API Configuration

To use this node, you need:

1. **HyprLab API Key**: Sign up at [HyprLab](https://hyprlab.io) to get your API key
2. **API Access**: The service provides access to Google's Imagen models with a 50% discount

### Pricing (as per HyprLab documentation)
- imagen-4: $0.02 per image (50% off)
- imagen-3: $0.02 per image (50% off)  
- imagen-3-fast: $0.01 per image (50% off)

## Example Workflow

1. Add the "Leon Google Image API" node to your ComfyUI workflow
2. Enter your API key in the `api_key` field
3. Write your prompt in the `prompt` field
4. Select your preferred model, aspect ratio, and output format
5. Set a seed value if you want reproducible results
6. Connect the output `image` to a PreviewImage node or other image processing nodes

## Error Handling

The node includes robust error handling:
- Automatic retry with exponential backoff (up to 5 attempts)
- Input validation (prompt length, empty prompts)
- API response validation
- Network error handling
- Detailed error messages for debugging

## Technical Details

- Built using the same patterns as BillBum nodes for consistency
- Uses `tenacity` for retry logic
- Supports both URL and base64 response formats
- Automatically converts images to ComfyUI tensor format
- Includes proper image format conversion (RGBA)

## Dependencies

- tenacity: For retry mechanism
- requests: For HTTP API calls
- pillow: For image processing
- torch: For tensor operations
- numpy: For array operations

## License

This project follows the same license as the reference BillBum nodes.

## Support

For issues related to:
- **API access**: Contact HyprLab support
- **Node functionality**: Create an issue in this repository
- **ComfyUI integration**: Check ComfyUI documentation

---

Based on the reference implementation from [ComfyUI_BillBum_Nodes](https://github.com/AhBumm/ComfyUI_BillBum_Nodes) and integrated with [HyprLab API](https://docs.hyprlab.io/browse-models/model-list/google/image). 