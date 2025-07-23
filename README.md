# ComfyUI Leon API Nodes

A comprehensive collection of ComfyUI custom nodes for AI image generation, LLM chat completions, Midjourney proxy integration, and utility functions via various APIs including HyprLab.

## Overview

This package provides multiple categories of nodes to enhance your ComfyUI workflows:

- **🎨 Image Generation APIs**: Google Imagen, Luma AI, FLUX, FLUX Kontext
- **🤖 LLM APIs**: Chat completions, JSON extraction, model management
- **🎭 Midjourney Proxy**: Generate, describe, and upload images
- **🔧 Utility Nodes**: Image processing, string manipulation, file uploads

## Installation

1. Clone or copy this repository to your ComfyUI custom nodes directory:
   ```bash
   cd ComfyUI/custom_nodes/
   git clone <repository-url> comfyui-leon-nodes
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Restart ComfyUI

## 🎨 Image Generation Nodes

### Leon Google Image API 🤖
Generate images using Google's Imagen models via HyprLab API.

**Features:**
- Models: imagen-4-ultra, imagen-4, imagen-4-fast, imagen-3, imagen-3-fast
- Aspect ratios: 1:1, 3:4, 4:3, 9:16, 16:9
- Output formats: PNG, JPEG, WebP

**Usage Example:**
1. Add "Leon Google Image API" node
2. Enter your HyprLab API key
3. Write your prompt (max 10,000 characters)
4. Select model and settings
5. Connect output to PreviewImage

### Leon Luma AI Image API 🤖
Advanced image generation with reference image support.

**Features:**
- Models: photon, photon-flash
- Image/style/character reference inputs
- Flexible aspect ratios including 9:21, 21:9

**Usage Example:**
1. Add "Leon Luma AI Image API" node
2. Connect reference images (optional)
3. Set reference weights (0.0-1.0)
4. Generate with enhanced control

### Leon FLUX Image API 🤖
High-quality image generation with FLUX models.

**Features:**
- Models: FLUX 1.1 Pro Ultra, FLUX 1.1 Pro, FLUX Pro Canny, FLUX Dev, FLUX Schnell
- Image prompt guidance
- Flexible dimensions (256-1440px, multiples of 32)

**Usage Example:**
1. Select FLUX model variant
2. Add prompt and optional image guidance
3. Configure steps, dimensions, aspect ratio
4. Generate high-quality images

### Leon FLUX Kontext API 🤖
Context-aware image generation with input image support.

**Features:**
- Models: flux-kontext-max, flux-kontext-pro
- Input image context understanding
- Match input image aspect ratio option

## 🤖 LLM API Nodes

### Leon LLM Chat API 🤖
Text and vision chat completions with various LLM models.

**Features:**
- Support for GPT-4o, Claude, Gemini, and more
- Vision capabilities (text + image input)
- Configurable temperature, top_p, max_tokens
- System message support

**Usage Example:**
```
Model Selector → LLM Chat API → Text Output
     ↑              ↑
  "gpt-4o"    "Analyze this image"
                     ↑
                Image Input
```

### Leon LLM JSON API 🤖
Structured data extraction with JSON schema validation.

**Features:**
- JSON schema-based output
- Data extraction and structuring
- Lower temperature for consistency
- Schema validation

**Usage Example:**
```json
Schema: {
  "type": "object",
  "properties": {
    "email": {"type": "string"},
    "name": {"type": "string"}
  }
}
```

### Leon Model Selector 🔧
Dynamic model selection with live configuration.

**Features:**
- Dropdown with popular models
- Custom model input override
- Model information display
- Context length awareness

### Leon Model Config Loader ⚙️
Fetch and manage available models from API.

**Features:**
- Live model list fetching
- Cached fallback configuration
- Save to file option
- Error handling with graceful fallback

## 🎭 Midjourney Proxy Nodes

### Leon Midjourney API Generate 🤖
Generate images using Midjourney via proxy server.

**Features:**
- MID_JOURNEY and NIJI_JOURNEY bot types
- Base64 image array support
- Account filtering
- Polling with timeout handling

**Setup:**
1. Run Midjourney proxy server (e.g., localhost:8080)
2. Configure API key and endpoint
3. Use prompts with Midjourney syntax (--v 7, --ar 1:1)

### Leon Midjourney API Describe 🤖
Get text descriptions of images using Midjourney.

**Features:**
- Upload image and get 4 description variants
- Automatic description parsing
- Same proxy server integration

### Leon Midjourney API Upload 🤖
Upload images to Discord via Midjourney proxy.

**Features:**
- Convert ComfyUI images to Discord URLs
- Account filtering support
- Direct integration with Midjourney workflows

## 🔧 Utility Nodes

### Leon Image Split 4-Grid 🤖
Split images into 4 quadrants (useful for Midjourney grid results).

**Outputs:** Top-Left, Top-Right, Bottom-Left, Bottom-Right images

### Leon String Combine 🤖
Combine two strings with a linking element.

**Usage:** Useful for building complex prompts or file paths

### Leon ImgBB Upload 🤖
Upload images to ImgBB hosting service.

**Features:**
- Expiration time control
- Direct URL output
- Error handling

### Leon Hypr Upload 🤖
Upload images/videos to HyprLab hosting.

**Features:**
- Multiple input methods (tensor, file path, URL, base64)
- Output format conversion
- Multipart and JSON upload support

## 🔗 Common Workflow Patterns

### Basic Image Generation
```
Model Selector → Google/Luma/FLUX API → PreviewImage
```

### Vision Analysis
```
LoadImage → LLM Chat API → Text Output
              ↑
         Model Selector
```

### Midjourney Grid Processing
```
Midjourney Generate → Image Split 4-Grid → 4x PreviewImage
```

### Data Extraction
```
Text Input → LLM JSON API → JSON Output
              ↑
         JSON Schema
```

### Image Upload Chain
```
Generated Image → Hypr Upload → URL → Use in other APIs
```

## 🛠️ Advanced Usage

### Model Management
```
Model Config Loader → Save models.json
Model Selector → Use cached or live models
```

### Multi-Modal Workflows
```
Text + Image → LLM Chat → Analysis
     ↓
Generated Image → Midjourney Describe → Descriptions
     ↓
Upload → Share URLs
```

### Batch Processing
```
Multiple Prompts → Loop through FLUX API → Collect Results
```

## 🔧 Error Handling

All nodes include robust error handling:
- **Retry Logic**: Exponential backoff (up to 5 attempts)
- **Input Validation**: Prompt lengths, required fields
- **API Response Validation**: Proper error messages
- **Network Error Handling**: Graceful degradation
- **Detailed Logging**: Console output for debugging

---

**Acknowledge**: [ComfyUI_BillBum_Nodes](https://github.com/AhBumm/ComfyUI_BillBum_Nodes) | **Integrated with**: [HyprLab API](https://docs.hyprlab.io) 