from pathlib import PurePosixPath

from cloudinary_storage.storage import MediaCloudinaryStorage, RESOURCE_TYPES


class PortfolioCloudinaryStorage(MediaCloudinaryStorage):
    """Choose Cloudinary's resource type from the portfolio file extension."""

    IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "bmp", "tif", "tiff"}
    VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm", "m4v"}

    def _get_resource_type(self, name):
        path_parts = PurePosixPath(name).parts
        if "video" in path_parts:
            return RESOURCE_TYPES["VIDEO"]
        if "audio" in path_parts or "document" in path_parts:
            return RESOURCE_TYPES["RAW"]
        if "image" in path_parts:
            return RESOURCE_TYPES["IMAGE"]

        extension = PurePosixPath(name).suffix.lower().lstrip(".")
        if extension in self.IMAGE_EXTENSIONS:
            return RESOURCE_TYPES["IMAGE"]
        if extension in self.VIDEO_EXTENSIONS:
            return RESOURCE_TYPES["VIDEO"]
        return RESOURCE_TYPES["RAW"]
