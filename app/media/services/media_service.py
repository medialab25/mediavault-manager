from typing import List
from ..models.media_models import Media
from app.jellyfin.client import JellyfinClient
from app.core.config import settings
from ._merge_media import merge_libraries
import logging

logger = logging.getLogger(__name__)

class MediaService:
    def __init__(self):
        self.jellyfin_client = JellyfinClient()

    async def refresh_media(self):
        """Refresh the media library by calling the Media Library API."""
        try:
            logger.debug("Calling Jellyfin refresh_media")
            response = await self.jellyfin_client.refresh_media()
            logger.debug(f"Jellyfin refresh response: {response}")
            return {"status": "success", "message": "Media library refresh initiated"}
        except Exception as e:
            logger.error(f"Error in refresh_media: {str(e)}", exc_info=True)
            raise

    async def merge_media(self):
        """Merge media files according to the configuration settings."""
        try:
            logger.debug("Starting media merge")
            
            # Get configuration values
            source_path = settings.MEDIA_LIBRARY["default_source_path"]
            source_matrix = settings.MEDIA_LIBRARY["source_matrix"]
            user_id = int(settings.MEDIA_MERGE["user"])
            group_id = int(settings.MEDIA_MERGE["group"])

            # Process each media type in the source matrix
            for media_type, config in source_matrix.items():
                quality_order = config["quality_order"]
                merged_path = config["merged_path"]
                
                logger.debug(f"Merging {media_type} with quality order {quality_order} to {merged_path}")
                
                # Call merge_libraries with the configuration values
                success = merge_libraries(
                    media_type=media_type,
                    source_paths=[source_path],
                    quality_list=quality_order,
                    merged_path=merged_path,
                    user_id=user_id,
                    group_id=group_id
                )
                
                if not success:
                    logger.error(f"Failed to merge {media_type}")
                    return {"status": "error", "message": f"Failed to merge {media_type}"}

            return {"status": "success", "message": "Media merge completed"}
        except Exception as e:
            logger.error(f"Error in merge_media: {str(e)}", exc_info=True)
            raise

# class MediaService:
#     def __init__(self, media_root: str):
#         self.media_root = media_root

#     def scan_directory(self, directory: str) -> List[Media]:
#         """Scan a directory for media files and return Media objects."""
#         media_items = []
        
#         for root, _, files in os.walk(directory):
#             for file in files:
#                 file_path = os.path.join(root, file)
#                 if self._is_media_file(file):
#                     media_items.append(self._create_media_item(file_path))
        
#         return media_items

#     def _is_media_file(self, filename: str) -> bool:
#         """Check if a file is a media file based on its extension."""
#         media_extensions = {
#             # Video
#             '.mp4', '.avi', '.mkv', '.mov', '.wmv',
#             # Audio
#             '.mp3', '.wav', '.flac', '.m4a',
#             # Images
#             '.jpg', '.jpeg', '.png', '.gif'
#         }
#         return os.path.splitext(filename)[1].lower() in media_extensions

#     def _create_media_item(self, file_path: str) -> Media:
#         """Create a Media object from a file path."""
#         stats = os.stat(file_path)
#         return Media(
#             id=str(hash(file_path)),
#             title=os.path.splitext(os.path.basename(file_path))[0],
#             type=self._determine_media_type(file_path),
#             path=file_path,
#             size=stats.st_size,
#             created_at=datetime.fromtimestamp(stats.st_ctime),
#             updated_at=datetime.fromtimestamp(stats.st_mtime)
#         )

#     def _determine_media_type(self, file_path: str) -> str:
#         """Determine the type of media based on file extension."""
#         ext = os.path.splitext(file_path)[1].lower()
#         if ext in {'.mp4', '.avi', '.mkv', '.mov', '.wmv'}:
#             return 'video'
#         elif ext in {'.mp3', '.wav', '.flac', '.m4a'}:
#             return 'audio'
#         elif ext in {'.jpg', '.jpeg', '.png', '.gif'}:
#             return 'image'
#         return 'unknown'