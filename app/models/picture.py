from dataclasses import dataclass
from typing import Optional


@dataclass
class Picture:
    """
    Domain model corresponding 1:1 to the DB table Picture.
    """

    id: Optional[int]
    item_id: int
    file_path: str
    is_main: bool = False

    def __post_init__(self):
        if not self.file_path or not self.file_path.strip():
            raise ValueError("Picture file_path cannot be empty")
