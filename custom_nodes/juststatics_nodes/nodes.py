"""
juststatics_nodes - ComfyUI custom nodes for queue-based static editing.

Workflow: claim statics from a shared queue, iterate with image generators (Nano Banana 2),
approve to deliver, queue auto-advances to next static.

Configure paths via juststatics_config.json next to this file. See juststatics_config.example.json.
"""
import os
import json
import shutil
import time
import torch
import numpy as np
from PIL import Image, ImageDraw
import folder_paths


def _load_config():
    """Load config from juststatics_config.json next to nodes.py.

    Falls back to sensible defaults if config missing or invalid.
    """
    config_path = os.path.join(os.path.dirname(__file__), "juststatics_config.json")
    defaults = {
        "base_dir": os.path.join(os.path.expanduser("~"), "juststatics-comfy"),
    }
    if os.path.isfile(config_path):
        try:
            with open(config_path, "r", encoding="utf-8-sig") as f:
                user_config = json.load(f)
            defaults.update(user_config)
            print(f"[JustStatics] Loaded config from {config_path}")
        except Exception as e:
            print(f"[JustStatics] Warning: failed to load {config_path}: {e}")
            print(f"[JustStatics] Using defaults: base_dir={defaults['base_dir']}")
    return defaults


_config = _load_config()
JUSTSTATICS_BASE = _config["base_dir"]
NEEDS_EDIT_DIR = os.path.join(JUSTSTATICS_BASE, "needs_edit")
APPROVED_DIR = os.path.join(JUSTSTATICS_BASE, "approved")
PROCESSED_DIR = os.path.join(JUSTSTATICS_BASE, "processed")


def _in_progress_dir(chain_id):
    return os.path.join(JUSTSTATICS_BASE, "in_progress", f"chain_{chain_id}")


def _staging_dir(chain_id):
    return os.path.join(folder_paths.get_output_directory(), "staging", f"chain_{chain_id}")


class LoadStaticAndCritique:
    """Claims next available static from shared queue to chain's in_progress folder.

    On first call (or after approve), claims alphabetically-first file from needs_edit/
    by moving it (image + sidecar JSON) to in_progress/chain_<chain_id>/.
    Subsequent calls reload the same claimed file.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory": ("STRING", {"default": NEEDS_EDIT_DIR}),
                "chain_id": ("INT", {"default": 1, "min": 1, "max": 99}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("image", "critique", "kunde_navn", "filename_stem", "monday_item_id", "drive_folder_id")
    FUNCTION = "load"
    CATEGORY = "JustStatics"

    @classmethod
    def IS_CHANGED(cls, directory, chain_id):
        return float("nan")

    def load(self, directory, chain_id):
        in_progress = _in_progress_dir(chain_id)
        os.makedirs(in_progress, exist_ok=True)
        valid_exts = {".jpg", ".jpeg", ".png", ".webp"}

        claimed = sorted([f for f in os.listdir(in_progress)
                          if os.path.splitext(f)[1].lower() in valid_exts])
        if claimed:
            filename = claimed[0]
            source_dir = in_progress
        else:
            if not os.path.isdir(directory):
                raise FileNotFoundError(f"Queue directory not found: {directory}")
            available = sorted([f for f in os.listdir(directory)
                                if os.path.splitext(f)[1].lower() in valid_exts])
            if not available:
                raise ValueError(f"Queue is empty (no images in {directory})")
            filename = available[0]
            stem = os.path.splitext(filename)[0]
            for ext in [".jpg", ".jpeg", ".png", ".webp", ".json"]:
                src = os.path.join(directory, f"{stem}{ext}")
                if os.path.isfile(src):
                    dst = os.path.join(in_progress, f"{stem}{ext}")
                    shutil.move(src, dst)
            source_dir = in_progress
            print(f"[JustStatics] Chain {chain_id} claimed: {filename}")

        stem = os.path.splitext(filename)[0]
        img_path = os.path.join(source_dir, filename)
        pil_img = Image.open(img_path).convert("RGB")
        img_array = np.array(pil_img).astype(np.float32) / 255.0
        img_tensor = torch.from_numpy(img_array)[None,]

        json_path = os.path.join(source_dir, f"{stem}.json")
        critique = ""
        kunde_navn = ""
        monday_id = ""
        drive_folder_id = ""
        if os.path.isfile(json_path):
            with open(json_path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            critique = data.get("critique", "")
            kunde_navn = data.get("kunde_navn", "")
            monday_id = data.get("monday_item_id", "")
            drive_folder_id = data.get("drive_folder_id", "")

        return (img_tensor, critique, kunde_navn, stem, monday_id, drive_folder_id)


class MockImageGenerator:
    """Drop-in replacement for image generators during workflow testing.

    Returns input image with a yellow overlay band showing prompt + timestamp.
    Instant, no API cost. For mechanic-validation only.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "prompt": ("STRING", {"multiline": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "generate"
    CATEGORY = "JustStatics"

    def generate(self, images, prompt):
        from PIL import ImageFont
        img_array = (images[0].cpu().numpy() * 255.0).astype(np.uint8)
        pil_img = Image.fromarray(img_array).convert("RGB")
        w, h = pil_img.size
        draw = ImageDraw.Draw(pil_img)
        band_height = h // 6
        draw.rectangle([0, 0, w, band_height], fill="yellow")
        big_size = h // 8
        small_size = h // 40
        try:
            big = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", big_size)
            small = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", small_size)
        except Exception:
            big = ImageFont.load_default()
            small = ImageFont.load_default()
        timestamp = time.strftime("%H:%M:%S")
        draw.text((40, 30), f"MOCK | {timestamp}", fill="black", font=big)
        prompt_short = (prompt[:120] if prompt else "(no prompt)")
        draw.text((40, big_size + 60), f"prompt: {prompt_short}", fill="black", font=small)
        result_array = np.array(pil_img).astype(np.float32) / 255.0
        result_tensor = torch.from_numpy(result_array)[None,]
        return (result_tensor,)


class SaveStaging:
    """Writes the latest iteration to a deterministic staging path per chain.

    SaveOnApprove reads from this same path when approving.
    Path: <ComfyUI output>/staging/chain_<chain_id>/<filename_stem>_latest.jpg
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "filename_stem": ("STRING", {"forceInput": True}),
                "chain_id": ("INT", {"default": 1, "min": 1, "max": 99}),
            }
        }

    RETURN_TYPES = ()
    FUNCTION = "save"
    OUTPUT_NODE = True
    CATEGORY = "JustStatics"

    def save(self, image, filename_stem, chain_id):
        staging_dir = _staging_dir(chain_id)
        os.makedirs(staging_dir, exist_ok=True)
        img_array = (image[0].cpu().numpy() * 255.0).astype(np.uint8)
        pil_img = Image.fromarray(img_array)
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")
        path = os.path.join(staging_dir, f"{filename_stem}_latest.jpg")
        pil_img.save(path, format="JPEG", quality=95)
        print(f"[JustStatics] Chain {chain_id} staged: {path}")
        return ()


class SaveOnApprove:
    """When approve=true, copies staging to approved/ and moves source out of in_progress/.

    Reads from disk (no NB2 dependency in execution graph), so approve doesn't
    re-trigger image generation. Queue auto-advances as in_progress empties.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "filename_stem": ("STRING", {"forceInput": True}),
                "approve": ("BOOLEAN", {"default": False}),
                "chain_id": ("INT", {"default": 1, "min": 1, "max": 99}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status",)
    FUNCTION = "maybe_save"
    OUTPUT_NODE = True
    CATEGORY = "JustStatics"

    def maybe_save(self, filename_stem, approve, chain_id):
        if not approve:
            return ("iterating, not saving",)
        staging_dir = _staging_dir(chain_id)
        staging_path = os.path.join(staging_dir, f"{filename_stem}_latest.jpg")
        in_progress = _in_progress_dir(chain_id)
        if not os.path.isfile(staging_path):
            print(f"[JustStatics] approve=true but no staging at {staging_path} - skipping")
            return ("no staging file - skipped",)
        os.makedirs(APPROVED_DIR, exist_ok=True)
        os.makedirs(PROCESSED_DIR, exist_ok=True)
        approved_path = os.path.join(APPROVED_DIR, f"{filename_stem}.jpg")
        shutil.copy2(staging_path, approved_path)
        moved = []
        for ext in [".jpg", ".jpeg", ".png", ".webp", ".json"]:
            src = os.path.join(in_progress, f"{filename_stem}{ext}")
            if os.path.isfile(src):
                dst = os.path.join(PROCESSED_DIR, f"{filename_stem}{ext}")
                shutil.move(src, dst)
                moved.append(os.path.basename(src))
        try:
            os.remove(staging_path)
        except Exception:
            pass
        msg = f"APPROVED chain {chain_id} -> {approved_path} | source moved: {', '.join(moved)}"
        print(f"[JustStatics] {msg}")
        return (msg,)


NODE_CLASS_MAPPINGS = {
    "LoadStaticAndCritique": LoadStaticAndCritique,
    "MockImageGenerator": MockImageGenerator,
    "SaveStaging": SaveStaging,
    "SaveOnApprove": SaveOnApprove,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadStaticAndCritique": "Load Static + Critique (JustStatics)",
    "MockImageGenerator": "Mock Image Generator (JustStatics)",
    "SaveStaging": "Save Staging (JustStatics)",
    "SaveOnApprove": "Save On Approve (JustStatics)",
}