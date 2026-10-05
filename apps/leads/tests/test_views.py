import pytest
from django.contrib.auth.models import Permission
from django.core.files.base import ContentFile
from django.urls import reverse
from model_bakery import baker

from apps.leads.models import Enquiry, EnquiryDocument

pytestmark = pytest.mark.django_db


@pytest.fixture
def document():
    enquiry = baker.make(Enquiry, phone="+8801712345678", country="BD")
    doc = EnquiryDocument(enquiry=enquiry, original_name="mri-scan.pdf")
    doc.file.save("mri.pdf", ContentFile(b"%PDF-1.7 scan"), save=True)
    return doc


def download_url(document):
    return reverse("leads:download_document", args=[document.pk])


def test_anonymous_visitors_are_sent_to_login(client, document):
    response = client.get(download_url(document))

    assert response.status_code == 302
    assert "login" in response.url


def test_staff_without_permission_are_refused(client, django_user_model, document):
    staff = django_user_model.objects.create_user(
        email="staff@example.com", password="x", is_staff=True
    )
    client.force_login(staff)

    assert client.get(download_url(document)).status_code == 403


def test_permitted_staff_download_as_attachment(client, django_user_model, document):
    staff = django_user_model.objects.create_user(
        email="manager@example.com", password="x", is_staff=True
    )
    staff.user_permissions.add(Permission.objects.get(codename="view_enquiry"))
    client.force_login(staff)

    response = client.get(download_url(document))

    assert response.status_code == 200
    assert b"".join(response.streaming_content) == b"%PDF-1.7 scan"
    assert response["Content-Disposition"].startswith("attachment")
    assert "mri-scan.pdf" in response["Content-Disposition"]
