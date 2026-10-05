from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, RegexValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

MAX_IMAGE_SIZE_MB = 5

validate_image_extension = FileExtensionValidator(
    allowed_extensions=["jpg", "jpeg", "png", "webp"]
)

validate_indian_pincode = RegexValidator(
    regex=r"^[1-9][0-9]{5}$",
    message=_("Enter a valid 6-digit PIN code."),
)


def validate_image_size(file) -> None:
    if file.size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise ValidationError(
            _("Image must be %(max)s MB or smaller."),
            code="file_too_large",
            params={"max": MAX_IMAGE_SIZE_MB},
        )


def current_year() -> int:
    """Used as a callable limit, so the maximum moves forward every year."""
    return timezone.localdate().year


MAX_DOCUMENT_SIZE_MB = 10

validate_document_extension = FileExtensionValidator(
    allowed_extensions=["pdf", "jpg", "jpeg", "png"]
)

# The first bytes of each allowed file type. Checking them stops a renamed
# file (say, an .exe saved as report.pdf) from being accepted.
_FILE_SIGNATURES = (
    b"%PDF-",  # PDF
    b"\xff\xd8\xff",  # JPEG
    b"\x89PNG\r\n\x1a\n",  # PNG
)


def validate_document_size(file) -> None:
    if file.size > MAX_DOCUMENT_SIZE_MB * 1024 * 1024:
        raise ValidationError(
            _("Each file must be %(max)s MB or smaller."),
            code="file_too_large",
            params={"max": MAX_DOCUMENT_SIZE_MB},
        )


def validate_document_content(file) -> None:
    """Reject files whose contents don't match an allowed type."""
    position = file.tell()
    header = file.read(8)
    file.seek(position)
    if not header.startswith(_FILE_SIGNATURES):
        raise ValidationError(
            _("Upload a PDF, JPG or PNG file."), code="invalid_file_type"
        )
