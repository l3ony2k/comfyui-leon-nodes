import torch
import numpy as np
from PIL import Image, ImageEnhance, ImageChops

def normalize_gray(image: Image) -> Image:
    """Normalize a grayscale image using histogram equalization."""
    if image.mode != 'L':
        image = image.convert('L')
    img = np.asarray(image)
    balanced_img = img.copy()
    hist, bins = np.histogram(img.reshape(-1), 256, (0, 256))
    bmin = np.min(np.where(hist > (hist.sum() * 0.0005)))
    bmax = np.max(np.where(hist > (hist.sum() * 0.0005)))
    balanced_img = np.clip(img, bmin, bmax)
    if bmax != bmin:
        balanced_img = ((balanced_img - bmin) / (bmax - bmin) * 255)
    else:
        balanced_img = np.zeros_like(img)
    return Image.fromarray(balanced_img.astype(np.uint8)).convert('L')

def image_channel_split(image: Image, mode: str = 'RGBA') -> tuple:
    """Split image into channels based on color mode."""
    _image = image.convert('RGBA')
    channel1 = Image.new('L', size=_image.size, color='black')
    channel2 = Image.new('L', size=_image.size, color='black')
    channel3 = Image.new('L', size=_image.size, color='black')
    channel4 = Image.new('L', size=_image.size, color='black')

    if mode == 'RGBA':
        channel1, channel2, channel3, channel4 = _image.split()
    elif mode == 'RGB':
        channel1, channel2, channel3 = _image.convert('RGB').split()
    elif mode == 'YCbCr':
        channel1, channel2, channel3 = _image.convert('YCbCr').split()
    elif mode == 'LAB':
        channel1, channel2, channel3 = _image.convert('LAB').split()
    elif mode == 'HSV':
        channel1, channel2, channel3 = _image.convert('HSV').split()

    return channel1, channel2, channel3, channel4

def image_channel_merge(channels: tuple, mode: str = 'RGB') -> Image:
    """Merge channels back into an image based on color mode."""
    channel1 = channels[0].convert('L')
    channel2 = channels[1].convert('L')
    channel3 = channels[2].convert('L')
    channel4 = Image.new('L', size=channel1.size, color='white')

    if mode == 'RGBA':
        if len(channels) > 3:
            channel4 = channels[3].convert('L')
        ret_image = Image.merge('RGBA', [channel1, channel2, channel3, channel4])
    elif mode == 'RGB':
        ret_image = Image.merge('RGB', [channel1, channel2, channel3])
    elif mode == 'YCbCr':
        ret_image = Image.merge('YCbCr', [channel1, channel2, channel3]).convert('RGB')
    elif mode == 'LAB':
        ret_image = Image.merge('LAB', [channel1, channel2, channel3]).convert('RGB')
    elif mode == 'HSV':
        ret_image = Image.merge('HSV', [channel1, channel2, channel3]).convert('RGB')

    return ret_image

def balance_to_gamma(balance: int) -> float:
    """Convert color balance value to gamma value."""
    return 0.00005 * balance * balance - 0.01 * balance + 1

def gamma_trans(image: Image, gamma: float) -> Image:
    """Apply gamma correction to an image."""
    if gamma == 1.0:
        return image
    img_array = np.array(image)
    img_array = np.power(img_array / 255.0, gamma) * 255.0
    return Image.fromarray(img_array.astype(np.uint8))

def RGB2RGBA(image: Image, mask: Image) -> Image:
    """Convert RGB image to RGBA using provided mask."""
    if image.mode != 'RGB':
        image = image.convert('RGB')
    if mask.mode != 'L':
        mask = mask.convert('L')
    return Image.merge('RGBA', (*image.split(), mask))

def chop_image_v2(background_image: Image, layer_image: Image, blend_mode: str, opacity: int) -> Image:
    """Blend two images together with specified blend mode and opacity."""
    if background_image.mode != 'RGB':
        background_image = background_image.convert('RGB')
    if layer_image.mode != 'RGB':
        layer_image = layer_image.convert('RGB')

    # Convert opacity to float (0-1)
    opacity = opacity / 100.0

    # Create a copy of the background image
    result = background_image.copy()

    # Apply blend mode
    if blend_mode == "normal":
        result = Image.blend(background_image, layer_image, opacity)
    elif blend_mode == "multiply":
        result = ImageChops.multiply(background_image, layer_image)
        result = Image.blend(background_image, result, opacity)
    elif blend_mode == "screen":
        result = ImageChops.screen(background_image, layer_image)
        result = Image.blend(background_image, result, opacity)
    elif blend_mode == "overlay":
        result = ImageChops.overlay(background_image, layer_image)
        result = Image.blend(background_image, result, opacity)

    return result

def auto_adjust(image: Image, strength: int = 100, brightness: int = 0,
                contrast: int = 0, saturation: int = 0, 
                red: int = 0, green: int = 0, blue: int = 0,
                mode: str = 'RGB') -> Image:
    """
    Apply automatic adjustments to an image.
    """
    def auto_level_gray(image):
        """Apply auto levels to a grayscale image."""
        gray_image = Image.new("L", image.size, color='gray')
        gray_image.paste(image.convert('L'))
        return normalize_gray(gray_image)

    # Calculate adjustment factors
    if brightness < 0:
        brightness_offset = brightness / 100 + 1
    else:
        brightness_offset = brightness / 50 + 1

    if contrast < 0:
        contrast_offset = contrast / 100 + 1
    else:
        contrast_offset = contrast / 50 + 1

    if saturation < 0:
        saturation_offset = saturation / 100 + 1
    else:
        saturation_offset = saturation / 50 + 1

    # Get color channel gammas
    red_gamma = balance_to_gamma(red)
    green_gamma = balance_to_gamma(green)
    blue_gamma = balance_to_gamma(blue)

    # Process image based on mode
    if mode == 'RGB':
        r, g, b, _ = image_channel_split(image, mode='RGB')
        r = auto_level_gray(r)
        g = auto_level_gray(g)
        b = auto_level_gray(b)
        ret_image = image_channel_merge((r, g, b), 'RGB')
    elif mode == 'lum + sat':
        h, s, v, _ = image_channel_split(image, mode='HSV')
        s = auto_level_gray(s)
        ret_image = image_channel_merge((h, s, v), 'HSV')
        l, a, b, _ = image_channel_split(ret_image, mode='LAB')
        l = auto_level_gray(l)
        ret_image = image_channel_merge((l, a, b), 'LAB')
    elif mode == 'luminance':
        l, a, b, _ = image_channel_split(image, mode='LAB')
        l = auto_level_gray(l)
        ret_image = image_channel_merge((l, a, b), 'LAB')
    elif mode == 'saturation':
        h, s, v, _ = image_channel_split(image, mode='HSV')
        s = auto_level_gray(s)
        ret_image = image_channel_merge((h, s, v), 'HSV')
    else:  # mono
        gray = image.convert('L')
        ret_image = auto_level_gray(gray).convert('RGB')

    # Apply color channel adjustments if not in mono mode
    if (red or green or blue) and mode != "mono":
        r, g, b, _ = image_channel_split(ret_image, mode='RGB')
        if red:
            r = gamma_trans(r, red_gamma).convert('L')
        if green:
            g = gamma_trans(g, green_gamma).convert('L')
        if blue:
            b = gamma_trans(b, blue_gamma).convert('L')
        ret_image = image_channel_merge((r, g, b), 'RGB')

    # Apply brightness, contrast, and saturation
    if brightness:
        brightness_image = ImageEnhance.Brightness(ret_image)
        ret_image = brightness_image.enhance(factor=brightness_offset)

    if contrast:
        contrast_image = ImageEnhance.Contrast(ret_image)
        ret_image = contrast_image.enhance(factor=contrast_offset)

    if saturation:
        color_image = ImageEnhance.Color(ret_image)
        ret_image = color_image.enhance(factor=saturation_offset)

    # Blend with original image based on strength
    ret_image = chop_image_v2(image, ret_image, blend_mode="normal", opacity=strength)

    # Handle RGBA mode
    if image.mode == 'RGBA':
        ret_image = RGB2RGBA(ret_image, image.split()[-1])

    return ret_image

class Leon_Yellow_Tint_Cleaner_Node:
    CATEGORY = "Leon_Utils"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "clean_yellow_tint"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "strength": ("INT", {"default": 100, "min": 0, "max": 100, "step": 1}),
                "brightness": ("INT", {"default": 0, "min": -100, "max": 100, "step": 1}),
                "contrast": ("INT", {"default": 0, "min": -100, "max": 100, "step": 1}),
                "saturation": ("INT", {"default": 0, "min": -100, "max": 100, "step": 1}),
                "red": ("INT", {"default": 0, "min": -100, "max": 100, "step": 1}),
                "green": ("INT", {"default": 0, "min": -100, "max": 100, "step": 1}),
                "blue": ("INT", {"default": 0, "min": -100, "max": 100, "step": 1}),
                "mode": (["RGB", "lum + sat", "luminance", "saturation", "mono"], {"default": "RGB"}),
            }
        }

    def tensor_to_pil(self, tensor):
        # Convert batched tensor (B, H, W, C) to list of PIL Images
        pil_images = []
        for i in range(tensor.shape[0]):
            img = tensor[i].cpu().numpy()
            img = (img * 255.0).astype(np.uint8)
            mode = 'RGBA' if img.shape[-1] == 4 else 'RGB'
            pil_images.append(Image.fromarray(img, mode=mode))
        return pil_images

    def pil_to_tensor(self, pil_images):
        # Convert list of PIL Images back to batched tensor (B, H, W, C)
        tensors = []
        for img in pil_images:
            img_np = np.array(img).astype(np.float32) / 255.0
            tensors.append(torch.from_numpy(img_np))
        return torch.stack(tensors, dim=0)

    def clean_yellow_tint(self, image, strength=100, brightness=0, contrast=0, saturation=0, red=0, green=0, blue=0, mode='RGB'):
        pil_images = self.tensor_to_pil(image)
        adjusted_images = []
        
        for pil_img in pil_images:
            adjusted = auto_adjust(
                pil_img,
                strength=strength,
                brightness=brightness,
                contrast=contrast,
                saturation=saturation,
                red=red,
                green=green,
                blue=blue,
                mode=mode
            )
            adjusted_images.append(adjusted)
            
        return (self.pil_to_tensor(adjusted_images),)

UTIL_NODE_CLASS_MAPPINGS = {
    "Leon_Yellow_Tint_Cleaner_Node": Leon_Yellow_Tint_Cleaner_Node
}

UTIL_NODE_DISPLAY_NAME_MAPPINGS = {
    "Leon_Yellow_Tint_Cleaner_Node": "🤖 Leon Yellow Tint Cleaner"
}
