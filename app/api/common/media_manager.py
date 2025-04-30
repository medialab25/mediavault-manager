# Management of media using the file_manager class
from pathlib import Path

class MediaDataManager:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)


