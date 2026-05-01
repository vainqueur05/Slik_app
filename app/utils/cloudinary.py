import cloudinary
import cloudinary.uploader
from flask import current_app

def upload_cloudinary_image(file, folder="slik"):
    """
    Upload un fichier image ou vidéo vers Cloudinary.
    Retourne le public_id.
    """
    cloudinary.config(
        cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
        api_key=current_app.config['CLOUDINARY_API_KEY'],
        api_secret=current_app.config['CLOUDINARY_API_SECRET']
    )

    if not file or not hasattr(file, 'filename'):
        raise ValueError("Fichier invalide pour Cloudinary")

    upload_result = cloudinary.uploader.upload(
        file,
        folder=folder,
        resource_type="auto"
    )

    return upload_result.get('public_id')