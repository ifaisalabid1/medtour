from pathlib import PurePosixPath
from uuid import uuid4


def unique_upload_path(folder: str, filename: str) -> str:
    """Store uploads under a random name.

    Avoids overwriting files that share a name, and doesn't publish whatever
    the uploader called the file on their computer.
    """
    extension = PurePosixPath(filename).suffix.lower()
    return f"{folder}/{uuid4().hex}{extension}"
