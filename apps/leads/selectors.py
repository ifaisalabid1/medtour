from django.db.models import QuerySet

from .models import Enquiry, EnquiryStatus


def enquiries_awaiting_first_contact() -> QuerySet[Enquiry]:
    """New enquiries, oldest first: the case managers' to-do list.

    Response time decides whether a lead converts, so the oldest
    uncontacted enquiry is always at the top.
    """
    return (
        Enquiry.objects.filter(status=EnquiryStatus.NEW)
        .select_related("treatment", "assigned_to")
        .order_by("created_at")
    )
