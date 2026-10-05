from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse
from django.shortcuts import get_object_or_404

from .models import EnquiryDocument


@staff_member_required
def download_document(request, pk):
    """Stream a private medical document to staff allowed to view enquiries.

    Sent as an attachment, never displayed inline, so a malicious file can't
    run in the browser on our domain.
    """
    if not request.user.has_perm("leads.view_enquiry"):
        raise PermissionDenied
    document = get_object_or_404(EnquiryDocument, pk=pk)
    return FileResponse(
        document.file.open("rb"),
        as_attachment=True,
        filename=document.original_name,
    )
