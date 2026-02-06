import tenacity
import base64
from PIL import Image
import io
import requests
import json
import os



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
                "model": ("STRING", {"default": "gemini-flash-latest", "tooltip": "Model name to use for chat completion"}),
                "user_message": ("STRING", {"multiline": True, "default": "Hello! How can you help me today?", "tooltip": "User message to send to the model"}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/chat/completions", "tooltip": "API URL for chat completions"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_HYPRLAB_API_KEY", "tooltip": "Your HyprLab API key"}),
            },
            "optional": {
                "system_message": ("STRING", {"multiline": True, "default": "", "tooltip": "System message to set the assistant's behavior"}),
                "max_tokens": ("INT", {"default": 128000, "min": 1, "max": 1048576, "tooltip": "Maximum number of tokens to generate"}),
                "temperature": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 2.0, "step": 0.1, "tooltip": "Sampling temperature (0.0 to 2.0)"}),
                "top_p": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.1, "tooltip": "Nucleus sampling parameter"}),
                "input_image": ("IMAGE", {"tooltip": "Optional single image input for vision-capable models"}),
                "image_url": ("STRING", {"multiline": False, "default": "", "tooltip": "Optional image URL for vision-capable models"}),
                "image_array": ("IMAGE_ARRAY", {"tooltip": "Optional array of images (base64 or URLs) for vision-capable models"}),
            }
        }



    def chat_completion(self, model, user_message, api_url, api_key, system_message="", max_tokens=128000, temperature=0.7, top_p=1.0, input_image=None, image_url="", image_array=None):
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
        has_image_socket = input_image is not None
        has_image_url = image_url.strip() != ""
        has_image_array = image_array is not None and len(image_array) > 0
        
        # Count how many image inputs are provided
        image_input_count = sum([has_image_socket, has_image_url, has_image_array])
        if image_input_count > 1:
            raise ValueError("Please provide only ONE of: input_image, image_url, or image_array")
        
        if has_image_array:
            # Multiple images from IMAGE_ARRAY
            user_content = [{"type": "text", "text": user_message}]
            for img_data in image_array:
                user_content.append({"type": "image_url", "image_url": {"url": img_data}})
            print(f"🟢 LLM Chat: Processing {len(image_array)} images from IMAGE_ARRAY")
        elif has_image_socket or has_image_url:
            # Single image input
            if has_image_socket:
                # Use socket input (convert tensor to base64)
                image_data_uri = self._tensor_to_base64_data_uri(input_image)
            else:
                # Use URL input directly
                image_data_uri = image_url
                
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
                "model": ("STRING", {"default": "", "tooltip": "Model name to use for JSON completion"}),
                "user_message": ("STRING", {"multiline": True, "default": "Extract the email address from this text: Contact us at support@example.com", "tooltip": "User message to send to the model"}),
                "json_schema": ("STRING", {"multiline": True, "default": '{"type": "object", "properties": {"email": {"type": "string", "description": "The extracted email address"}}, "required": ["email"]}', "tooltip": "JSON schema for structured output"}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/chat/completions", "tooltip": "API URL for chat completions"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_HYPRLAB_API_KEY", "tooltip": "Your HyprLab API key"}),
            },
            "optional": {
                "system_message": ("STRING", {"multiline": True, "default": "You are a helpful assistant that extracts structured data.", "tooltip": "System message to set the assistant's behavior"}),
                "max_tokens": ("INT", {"default": 128000, "min": 1, "max": 1048576, "tooltip": "Maximum number of tokens to generate"}),
                "temperature": ("FLOAT", {"default": 0.1, "min": 0.0, "max": 2.0, "step": 0.1, "tooltip": "Sampling temperature (lower for more consistent JSON)"}),
                "input_image": ("IMAGE", {"tooltip": "Optional single image input for vision-capable models"}),
                "image_url": ("STRING", {"multiline": False, "default": "", "tooltip": "Optional image URL for vision-capable models"}),
                "image_array": ("IMAGE_ARRAY", {"tooltip": "Optional array of images (base64 or URLs) for vision-capable models"}),
            }
        }



    def json_completion(self, model, user_message, json_schema, api_url, api_key, system_message="You are a helpful assistant that extracts structured data.", max_tokens=1000, temperature=0.1, input_image=None, image_url="", image_array=None):
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

        # Prepare user message content
        has_image_socket = input_image is not None
        has_image_url = image_url.strip() != ""
        has_image_array = image_array is not None and len(image_array) > 0
        
        # Count how many image inputs are provided
        image_input_count = sum([has_image_socket, has_image_url, has_image_array])
        if image_input_count > 1:
            raise ValueError("Please provide only ONE of: input_image, image_url, or image_array")
        
        if has_image_array:
            # Multiple images from IMAGE_ARRAY
            user_content = [{"type": "text", "text": user_message}]
            for img_data in image_array:
                user_content.append({"type": "image_url", "image_url": {"url": img_data}})
            print(f"🟢 LLM JSON: Processing {len(image_array)} images from IMAGE_ARRAY")
        elif has_image_socket or has_image_url:
            # Single image input
            if has_image_socket:
                # Use socket input (convert tensor to base64)
                image_data_uri = self._tensor_to_base64_data_uri(input_image)
            else:
                # Use URL input directly
                image_data_uri = image_url
                
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
        # Load available models from cached file
        cached_models = cls._load_cached_models()
        model_choices = [model["id"] for model in cached_models]  # Include all available models
        
        return {
            "required": {
                "model_choice": (model_choices, {"default": model_choices[0] if model_choices else "gemini-flash-latest", "tooltip": "Select a model from available options"}),
                "api_url": ("STRING", {"multiline": False, "default": "https://api.hyprlab.io/v1/models", "tooltip": "API URL to fetch models list"}),
                "api_key": ("STRING", {"multiline": False, "default": "YOUR_HYPRLAB_API_KEY", "tooltip": "Your HyprLab API key"}),
            },
            "optional": {
                "fetch_from_endpoint": ("BOOLEAN", {"default": False, "tooltip": "Fetch fresh model list from API endpoint and save to cache"}),
                "custom_model": ("STRING", {"default": "", "tooltip": "Enter custom model name (overrides dropdown selection)"}),
            }
        }

    @classmethod
    def _load_cached_models(cls):
        """Load models from cached models_config.json file"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_file = os.path.join(script_dir, "models_config.json")
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                    return config_data.get('data', [])
        except Exception as e:
            print(f"Failed to load cached models: {str(e)}")
        
        # Fallback to empty list if file doesn't exist or fails to load
        return []

    def _fetch_and_save_models(self, api_url, api_key):
        """Fetch models from API and save to models_config.json"""
        try:
            headers = {
                "Authorization": f"Bearer {api_key}"
            }
            
            print(f"Fetching models from: {api_url}")
            response = requests.get(api_url.rstrip('/'), headers=headers)
            response.raise_for_status()
            
            config_data = response.json()
            
            # Save to file
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_file = os.path.join(script_dir, "models_config.json")
            
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            print(f"Successfully fetched and saved {len(config_data.get('data', []))} models to {config_file}")
            return config_data.get('data', [])
            
        except Exception as e:
            print(f"Failed to fetch models from API: {str(e)}")
            print("Using cached models instead")
            return self._load_cached_models()

    def select_model(self, model_choice, api_url, api_key, fetch_from_endpoint=False, custom_model=""):
        # If fetch from endpoint is enabled, fetch fresh data
        if fetch_from_endpoint:
            available_models = self._fetch_and_save_models(api_url, api_key)
        else:
            available_models = self._load_cached_models()
        
        # Use custom model if provided, otherwise use dropdown selection
        selected_model = custom_model.strip() if custom_model.strip() else model_choice
        
        # Validate that selected model exists in available models (optional info)
        model_found = any(model["id"] == selected_model for model in available_models)
        if not model_found and not custom_model.strip():
            print(f"Warning: Selected model '{selected_model}' not found in available models list")
        
        print(f"Selected model: {selected_model}")
        return (selected_model,)


# Node mappings for ComfyUI
LLM_NODE_CLASS_MAPPINGS = {
    "Leon_LLM_Chat_API_Node": Leon_LLM_Chat_API_Node,
    "Leon_LLM_JSON_API_Node": Leon_LLM_JSON_API_Node,
    "Leon_Model_Selector_Node": Leon_Model_Selector_Node,
}

LLM_NODE_DISPLAY_NAME_MAPPINGS = {
    "Leon_LLM_Chat_API_Node": "🤖 Leon LLM Chat API",
    "Leon_LLM_JSON_API_Node": "🤖 Leon LLM JSON API",
    "Leon_Model_Selector_Node": "🤖 Leon Model Selector",
}