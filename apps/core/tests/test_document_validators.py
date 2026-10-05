import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.core.validators import validate_document_content, validate_document_size


@pytest.mark.parametrize(
    "content",
    [b"%PDF-1.7 report", b"\xff\xd8\xff\xe0 jpeg", b"\x89PNG\r\n\x1a\n png"],
)
def test_real_pdfs_and_images_are_accepted(content):
    validate_document_content(SimpleUploadedFile("report", content))


def test_a_renamed_file_is_rejected():
    fake_pdf = SimpleUploadedFile("report.pdf", b"MZ\x90\x00 windows executable")

    with pytest.raises(ValidationError, match="PDF, JPG or PNG"):
        validate_document_content(fake_pdf)


def test_checking_the_content_does_not_consume_the_file():
    upload = SimpleUploadedFile("report.pdf", b"%PDF-1.7 report")

    validate_document_content(upload)

    assert upload.read() == b"%PDF-1.7 report"


def test_documents_over_10_mb_are_rejected():
    big = SimpleUploadedFile("big.pdf", b"%PDF-" + b"0" * (10 * 1024 * 1024))

    with pytest.raises(ValidationError, match="10 MB"):
        validate_document_size(big)
