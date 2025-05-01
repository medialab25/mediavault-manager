# method to hard link a list of file paths to a target path and perform error handling
import os
import logging

# Configure logger
logger = logging.getLogger(__name__)

def os_adapter_hard_link_file(source_file_path: str, target_file_path: str) -> None:
    try:
        # Create folder structure if not exists
        os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
        os.link(source_file_path, target_file_path)
    except Exception as e:
        logger.error(f"Error hard linking file {source_file_path}: {str(e)}")

