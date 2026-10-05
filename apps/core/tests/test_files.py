import logging

import pytest
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from model_bakery import baker

from apps.core.files import _delete_quietly
from apps.leads.models import Enquiry, EnquiryDocument

pytestmark = pytest.mark.django_db


@pytest.fixture
def run_on_commit(django_capture_on_commit_callbacks):
    """Run on-commit callbacks (the deletions) at the end of the block."""
    return lambda: django_capture_on_commit_callbacks(execute=True)


@pytest.fixture
def hospital_with_image():
    hospital = baker.make_recipe("apps.providers.tests.hospital")
    hospital.image.save("old.jpg", ContentFile(b"old image"), save=True)
    return hospital


def test_replacing_an_image_deletes_the_old_file(hospital_with_image, run_on_commit):
    old_name = hospital_with_image.image.name

    with run_on_commit():
        hospital_with_image.image.save("new.jpg", ContentFile(b"new"), save=True)

    assert not default_storage.exists(old_name)
    assert default_storage.exists(hospital_with_image.image.name)


def test_removing_an_image_deletes_the_file(hospital_with_image, run_on_commit):
    old_name = hospital_with_image.image.name

    with run_on_commit():
        hospital_with_image.image = ""
        hospital_with_image.save()

    assert not default_storage.exists(old_name)


def test_saving_other_fields_keeps_the_file(hospital_with_image, run_on_commit):
    with run_on_commit():
        hospital_with_image.name = "Renamed Hospital"
        hospital_with_image.save()

    assert default_storage.exists(hospital_with_image.image.name)


def test_deleting_an_enquiry_deletes_its_private_documents(run_on_commit):
    enquiry = baker.make(Enquiry, phone="+8801712345678", country="BD")
    document = EnquiryDocument(enquiry=enquiry, original_name="scan.pdf")
    document.file.save("scan.pdf", ContentFile(b"%PDF-1.7"), save=True)
    storage, name = document.file.storage, document.file.name

    with run_on_commit():
        enquiry.delete()  # e.g. a data-erasure request

    assert not storage.exists(name)


def test_a_failed_deletion_is_logged_not_raised(caplog):
    class BrokenStorage:
        def delete(self, name):
            raise ConnectionError("storage unreachable")

    with caplog.at_level(logging.ERROR):
        _delete_quietly(BrokenStorage(), "hospitals/orphan.jpg")

    assert "hospitals/orphan.jpg" in caplog.text
