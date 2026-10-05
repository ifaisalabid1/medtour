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
