import os

from PIL import Image
from flask import current_app
from werkzeug.utils import secure_filename


ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_IMAGE_SIZE_BYTES = 2 * 1024 * 1024


def save_uploaded_image(file_storage, folder, filename_prefix, size=(400, 400)):
    if not file_storage or not getattr(file_storage, "filename", None):
        raise ValueError("No file provided.")

    original_name = secure_filename(file_storage.filename or "")
    if "." not in original_name:
        raise ValueError("Invalid image filename.")

    extension = original_name.rsplit(".", 1)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Invalid image format. Allowed formats: jpg, jpeg, png, webp.")

    file_storage.stream.seek(0, os.SEEK_END)
    file_size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if file_size > MAX_IMAGE_SIZE_BYTES:
        raise ValueError("Image size must be 2 MB or less.")

    safe_prefix = secure_filename(filename_prefix or "image") or "image"
    image_dir = os.path.join(current_app.static_folder, "images", folder)
    os.makedirs(image_dir, exist_ok=True)

    output_filename = f"{safe_prefix}.jpg"
    output_path = os.path.join(image_dir, output_filename)

    with Image.open(file_storage.stream) as img:
        converted = img.convert("RGB")
        converted.thumbnail(size, Image.LANCZOS)
        converted.save(output_path, format="JPEG", quality=85)

    return f"images/{folder}/{output_filename}"


def delete_image(relative_url):
    if not relative_url:
        return

    cleaned = str(relative_url).strip().lstrip("/")
    if not cleaned:
        return

    normalized = cleaned.replace("/", os.sep)
    full_path = os.path.join(current_app.static_folder, normalized)

    try:
        os.remove(full_path)
    except FileNotFoundError:
        return
