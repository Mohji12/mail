import io
import os
import uuid
from typing import Optional

import cloudinary
import cloudinary.uploader

from app.env_loader import load_app_env, require_env


def _configure_cloudinary() -> None:
    load_app_env()
    cloudinary.config(
        cloud_name=require_env("CLOUDINARY_CLOUD_NAME"),
        api_key=require_env("CLOUDINARY_API_KEY"),
        api_secret=require_env("CLOUDINARY_API_SECRET"),
        secure=True,
    )


def upload_banner(data: bytes, filename: str, kind: str) -> str:
    """Upload banner image or PDF; returns HTTPS URL for use in emails."""
    _configure_cloudinary()
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    resource_type = "raw" if kind == "pdf" else "image"
    options = {
        "folder": "email-banners",
        "resource_type": resource_type,
        "public_id": uuid.uuid4().hex,
        "overwrite": True,
    }
    if resource_type == "image" and ext:
        options["format"] = ext
    result = cloudinary.uploader.upload(io.BytesIO(data), **options)
    return result["secure_url"]


def upload_recipient_list(data: bytes, original_filename: str) -> Optional[str]:
    """Store CSV/Excel privately on Cloudinary. Returns public_id or None."""
    try:
        _configure_cloudinary()
        safe_base = os.path.basename(original_filename or "recipients.csv").replace("\\", "_").replace("/", "_")
        result = cloudinary.uploader.upload(
            io.BytesIO(data),
            folder="recipient-lists",
            resource_type="raw",
            type="private",
            public_id=f"{uuid.uuid4().hex}_{os.path.splitext(safe_base)[0]}",
            overwrite=True,
        )
        return result.get("public_id")
    except Exception as e:
        print(f"Warning: Could not upload recipient list to Cloudinary: {e}")
        return None
