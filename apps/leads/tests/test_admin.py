import pytest
from django.urls import reverse
from model_bakery import baker

from apps.leads.models import ConsentRecord, Enquiry

pytestmark = pytest.mark.django_db


@pytest.fixture
def enquiry():
    enquiry = baker.make(Enquiry, phone="+8801712345678", country="BD")
    baker.make(ConsentRecord, enquiry=enquiry, purpose="process_enquiry")
    return enquiry


def test_list_and_change_pages_render(admin_client, enquiry):
    assert (
        admin_client.get(reverse("admin:leads_enquiry_changelist")).status_code == 200
    )
    change_url = reverse("admin:leads_enquiry_change", args=[enquiry.pk])
    assert admin_client.get(change_url).status_code == 200
    history_url = reverse("admin:leads_enquiry_history", args=[enquiry.pk])
    assert admin_client.get(history_url).status_code == 200


def test_enquiries_cannot_be_added_by_hand(admin_client):
    assert admin_client.get(reverse("admin:leads_enquiry_add")).status_code == 403


def test_assign_to_me_action(admin_client, admin_user, enquiry):
    admin_client.post(
        reverse("admin:leads_enquiry_changelist"),
        {"action": "assign_to_me", "_selected_action": [enquiry.pk]},
    )

    enquiry.refresh_from_db()
    assert enquiry.assigned_to == admin_user
    assert enquiry.history.first().history_user == admin_user
