from datetime import timedelta

import pytest
from django.utils import timezone
from model_bakery import baker

from apps.leads.models import Enquiry, EnquiryStatus
from apps.leads.selectors import enquiries_awaiting_first_contact

pytestmark = pytest.mark.django_db


def make_enquiry(hours_ago, **fields):
    enquiry = baker.make(Enquiry, phone="+8801712345678", country="BD", **fields)
    Enquiry.objects.filter(pk=enquiry.pk).update(
        created_at=timezone.now() - timedelta(hours=hours_ago)
    )
    return enquiry


def test_oldest_new_enquiries_come_first():
    recent = make_enquiry(hours_ago=1)
    oldest = make_enquiry(hours_ago=30)
    make_enquiry(hours_ago=50, status=EnquiryStatus.CONTACTED)

    assert list(enquiries_awaiting_first_contact()) == [oldest, recent]
