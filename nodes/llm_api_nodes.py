import tenacity
import base64
from PIL import Image
import io
import requests
import json
import os

# Model configuration - this will be loaded from the models endpoint
MODELS_CONFIG = {
    "object": "list",
    "data": [
        {"id": "gpt-4o", "object": "model", "created": 1715367049, "owned_by": "openai", "context_length": 128000},
        {"id": "gpt-4o-mini", "object": "model", "created": 1721172741, "owned_by": "openai", "context_length": 128000},
        {"id": "claude-3-5-sonnet-latest", "object": "model", "created": 1729555200, "owned_by": "anthropic", "context_length": 200000},
        {"id": "claude-3-5-haiku-latest", "object": "model", "created": 1729555200, "owned_by": "anthropic", "context_length": 200000},
        {"id": "gemini-2.0-flash", "object": "model", "created": 1738713600, "owned_by": "google", "context_length": 1048576},
        {"id": "gemini-1.5-pro", "object": "model", "created": 1716508800, "owned_by": "google", "context_length": 2097152},
        {"id": "o1", "object": "model", "created": 1734375816, "owned_by": "openai", "context_length": 200000},
        {"id": "o1-mini", "object": "model", "created": 1725649008, "owned_by": "openai", "context_length": 128000},
        {"id": "deepseek-chat", "object": "model", "created": 1719532800, "owned_by": "deepseek", "context_length": 64000},
        {"id": "mistral-large-latest", "object": "model", "created": 1706803200, "owned_by": "mistralai", "context_length": 131072}
    ]
}

# Base class for HyprLab LLM Nodes
class HyprLabLLMNodeBase:
    CATEGORY = "Leon_API"
    
    @tenacity.retry(
        wait=tenacity.wait_exponential(multiplier=1.25, min=5, max=30),
        stop=tenacity.stop_after_attempt(5)
    )
    def _make_llm_api_call(self, payload, api_url, api_key):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        try:
            response = requests.post(api_url.rstrip('/'), json=payload, headers=headers)
            
            print(f"LLM API Request URL: {api_url.rstrip('/')}")
            print(f"LLM API Request Payload: {json.dumps(payload, indent=2)}")
            print(f"HTTP status: {response.status_code}")
            
            response.raise_for_status()
            response_json = response.json()
            
            print(f"LLM API Response: {json.dumps(response_json, indent=2)}")
            
            # Extract the response text
            if "choices" in response_json and len(response_json["choices"]) > 0:
                choice = response_json["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    return choice["message"]["content"]
                elif "text" in choice:
                    return choice["text"]
            
            raise Exception(f"Unexpected response format: {response_json}")

        except requests.exceptions.RequestException as e:
            raise Exception(f"LLM API request failed: {str(e)}")
        except Exception as e:
            print(f"Full error response: {response.text if 'response' in locals() else 'Response object not available'}")
            raise Exception(f"LLM API call failed: {str(e)}")

    def _tensor_to_base64_data_uri(self, tensor_image):
        if tensor_image is None:
            return None
        
        if tensor_image.ndim == 4:
            tensor_image = tensor_image[0]
        
        import torch
        import numpy as np
        
        np_image = (tensor_image.cpu().numpy() * 255).astype(np.uint8)
        pil_image = Image.fromarray(np_image, 'RGBA' if np_image.shape[-1] == 4 else 'RGB')
        
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        base64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{base64_str}"


class Leon_LLM_Chat_API_Node(HyprLabLLMNodeBase):
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION = "chat_completion"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("STRING", {"default": "gpt-4o", "tooltip": "Model name to use for chat completion"}),
                "user_message": ("STRING", {"multiline": True, "default": "Hello! How can you help me today?", "tooltip": "User message to send to the model"}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/chat/completions", "tooltip": "API URL for chat completions"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_HYPRLAB_API_KEY", "tooltip": "Your HyprLab API key"}),
            },
            "optional": {
                "system_message": ("STRING", {"multiline": True, "default": "", "tooltip": "System message to set the assistant's behavior"}),
                "max_tokens": ("INT", {"default": 1000, "min": 1, "max": 8192, "tooltip": "Maximum number of tokens to generate"}),
                "temperature": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 2.0, "step": 0.1, "tooltip": "Sampling temperature (0.0 to 2.0)"}),
                "top_p": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.1, "tooltip": "Nucleus sampling parameter"}),
                "input_image": ("IMAGE", {"tooltip": "Optional image input for vision-capable models"}),
            }
        }

    def chat_completion(self, model, user_message, api_url, api_key, system_message="", max_tokens=1000, temperature=0.7, top_p=1.0, input_image=None):
        if not user_message.strip():
            raise ValueError("User message cannot be empty")

        messages = []
        
        # Add system message if provided
        if system_message.strip():
            messages.append({
                "role": "system",
                "content": system_message
            })

        # Prepare user message content
        if input_image is not None:
            # Vision model with image input
            image_data_uri = self._tensor_to_base64_data_uri(input_image)
            user_content = [
                {"type": "text", "text": user_message},
                {"type": "image_url", "image_url": {"url": image_data_uri}}
            ]
        else:
            # Text-only input
            user_content = user_message

        messages.append({
            "role": "user",
            "content": user_content
        })

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p
        }

        response_text = self._make_llm_api_call(payload, api_url, api_key)
        return (response_text,)


class Leon_LLM_JSON_API_Node(HyprLabLLMNodeBase):
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("json_response",)
    FUNCTION = "json_completion"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("STRING", {"default": "gpt-4o", "tooltip": "Model name to use for JSON completion"}),
                "user_message": ("STRING", {"multiline": True, "default": "Extract the email address from this text: Contact us at support@example.com", "tooltip": "User message to send to the model"}),
                "json_schema": ("STRING", {"multiline": True, "default": '{"type": "object", "properties": {"email": {"type": "string", "description": "The extracted email address"}}, "required": ["email"]}', "tooltip": "JSON schema for structured output"}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/chat/completions", "tooltip": "API URL for chat completions"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_HYPRLAB_API_KEY", "tooltip": "Your HyprLab API key"}),
            },
            "optional": {
                "system_message": ("STRING", {"multiline": True, "default": "You are a helpful assistant that extracts structured data.", "tooltip": "System message to set the assistant's behavior"}),
                "max_tokens": ("INT", {"default": 1000, "min": 1, "max": 8192, "tooltip": "Maximum number of tokens to generate"}),
                "temperature": ("FLOAT", {"default": 0.1, "min": 0.0, "max": 2.0, "step": 0.1, "tooltip": "Sampling temperature (lower for more consistent JSON)"}),
            }
        }

    def json_completion(self, model, user_message, json_schema, api_url, api_key, system_message="You are a helpful assistant that extracts structured data.", max_tokens=1000, temperature=0.1):
        if not user_message.strip():
            raise ValueError("User message cannot be empty")

        try:
            # Validate JSON schema
            schema_obj = json.loads(json_schema)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON schema: {str(e)}")

        messages = []
        
        # Add system message
        if system_message.strip():
            messages.append({
                "role": "system",
                "content": system_message
            })

        messages.append({
            "role": "user",
            "content": user_message
        })

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "extraction_schema",
                    "schema": schema_obj
                }
            }
        }

        response_text = self._make_llm_api_call(payload, api_url, api_key)
        return (response_text,)


class Leon_Model_Selector_Node:
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("model_name",)
    FUNCTION = "select_model"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        # Extract model IDs from the config
        model_choices = [model["id"] for model in MODELS_CONFIG["data"]]
        
        return {
            "required": {
                "model_choice": (model_choices, {"default": "gpt-4o", "tooltip": "Select a model from the available options"}),
            },
            "optional": {
                "custom_model": ("STRING", {"default": "", "tooltip": "Enter a custom model name (overrides dropdown selection)"}),
                "show_model_info": ("BOOLEAN", {"default": False, "tooltip": "Print model information to console"}),
            }
        }

    def select_model(self, model_choice, custom_model="", show_model_info=False):
        # Use custom model if provided, otherwise use dropdown selection
        selected_model = custom_model.strip() if custom_model.strip() else model_choice
        
        if show_model_info:
            # Find model info in config
            model_info = None
            for model in MODELS_CONFIG["data"]:
                if model["id"] == selected_model:
                    model_info = model
                    break
            
            if model_info:
                print(f"Selected Model: {model_info['id']}")
                print(f"Owner: {model_info['owned_by']}")
                print(f"Context Length: {model_info['context_length']:,} tokens")
            else:
                print(f"Selected Model: {selected_model} (custom/not in config)")
        
        return (selected_model,)


class Leon_Model_Config_Loader_Node:
    CATEGORY = "Leon_API"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("config_json",)
    FUNCTION = "load_model_config"

    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/models", "tooltip": "API URL to fetch models list"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_HYPRLAB_API_KEY", "tooltip": "Your HyprLab API key"}),
            },
            "optional": {
                "use_cached": ("BOOLEAN", {"default": True, "tooltip": "Use cached model config instead of fetching from API"}),
                "save_to_file": ("BOOLEAN", {"default": False, "tooltip": "Save fetched config to models_config.json"}),
            }
        }

    def load_model_config(self, api_url, api_key, use_cached=True, save_to_file=False):
        if use_cached:
            # Return the hardcoded config
            config_json = json.dumps(MODELS_CONFIG, indent=2)
            print("Using cached model configuration")
            return (config_json,)
        
        # Fetch from API
        try:
            headers = {
                "Authorization": f"Bearer {api_key}"
            }
            
            response = requests.get(api_url.rstrip('/'), headers=headers)
            response.raise_for_status()
            
            config_data = response.json()
            config_json = json.dumps(config_data, indent=2)
            
            if save_to_file:
                # Save to file in the same directory as this script
                script_dir = os.path.dirname(os.path.abspath(__file__))
                config_file = os.path.join(script_dir, "models_config.json")
                with open(config_file, 'w') as f:
                    f.write(config_json)
                print(f"Model config saved to: {config_file}")
            
            print(f"Fetched {len(config_data.get('data', []))} models from API")
            return (config_json,)
            
        except Exception as e:
            print(f"Failed to fetch model config from API: {str(e)}")
            print("Falling back to cached configuration")
            config_json = json.dumps(MODELS_CONFIG, indent=2)
            return (config_json,)


# Node mappings for ComfyUI
LLM_NODE_CLASS_MAPPINGS = {
    "Leon_LLM_Chat_API_Node": Leon_LLM_Chat_API_Node,
    "Leon_LLM_JSON_API_Node": Leon_LLM_JSON_API_Node,
    "Leon_Model_Selector_Node": Leon_Model_Selector_Node,
    "Leon_Model_Config_Loader_Node": Leon_Model_Config_Loader_Node,
}

LLM_NODE_DISPLAY_NAME_MAPPINGS = {
    "Leon_LLM_Chat_API_Node": "🤖 Leon LLM Chat API",
    "Leon_LLM_JSON_API_Node": "🤖 Leon LLM JSON API", 
    "Leon_Model_Selector_Node": "🤖 Leon Model Selector",
    "Leon_Model_Config_Loader_Node": "🤖 Leon Model Config Loader",
}