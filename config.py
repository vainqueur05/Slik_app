import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Cloudinary (LOI 8)
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

    # APScheduler
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = "Africa/Lubumbashi"

    # Upload limits
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 Mo global
    MAX_IMAGE_SIZE = 5 * 1024 * 1024       # 5 Mo par image
    MAX_VIDEO_SIZE = 20 * 1024 * 1024      # 20 Mo par vidéo

    # Seuils de suspension (LOI 14)
    SUSPENSION_DAYS = 35
    PAYMENT_GRACE_DAYS = 30

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False