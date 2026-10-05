import re

import pytest
from model_bakery import baker

from apps.leads.models import Enquiry, EnquiryStatus, generate_reference

pytestmark = pytest.mark.django_db


def test_references_are_readable_and_random():
    references = {generate_reference() for _ in range(200)}

    assert len(references) == 200
    for reference in references:
        assert re.fullmatch(r"MT-[A-HJ-NP-Z2-9]{8}", reference)


def test_status_changes_are_kept_in_the_history():
    enquiry = baker.make(Enquiry, phone="+8801712345678", country="BD")

    enquiry.status = EnquiryStatus.CONTACTED
    enquiry.save()

    statuses = list(
        enquiry.history.order_by("history_date").values_list("status", flat=True)
    )
    assert statuses == [EnquiryStatus.NEW, EnquiryStatus.CONTACTED]
