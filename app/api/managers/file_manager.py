# File Manager: All low-level os related functions

from pathlib import Path

class FileManager:
    def __init__(self, base_path: Path):
        self.base_path = base_path