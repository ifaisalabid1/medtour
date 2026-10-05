import pytest
from django.core.exceptions import ValidationError

from apps.core.uploads import unique_upload_path
from apps.core.validators import validate_image_size, validate_indian_pincode


def test_upload_path_uses_a_random_name_and_keeps_the_extension():
    first = unique_upload_path("hospitals", "My Photo.JPG")
    second = unique_upload_path("hospitals", "My Photo.JPG")

    assert first.startswith("hospitals/")
    assert first.endswith(".jpg")
    assert "My Photo" not in first
    assert first != second


class FakeFile:
    def __init__(self, size):
        self.size = size


def test_image_size_limit():
    validate_image_size(FakeFile(5 * 1024 * 1024))  # exactly 5 MB is fine

    with pytest.raises(ValidationError, match="5 MB or smaller"):
        validate_image_size(FakeFile(5 * 1024 * 1024 + 1))


@pytest.mark.parametrize("pincode", ["12345", "0123456", "012345", "11A001"])
def test_invalid_pincodes_are_rejected(pincode):
    with pytest.raises(ValidationError):
        validate_indian_pincode(pincode)


def test_valid_pincode_is_accepted():
    validate_indian_pincode("600006")
