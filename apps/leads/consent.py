"""The exact consent wording shown on enquiry forms.

Never edit a text in place. To change the wording, write the new text and
bump CONSENT_TEXT_VERSION, so every stored ConsentRecord still matches what
that patient actually saw. Have a lawyer review the wording before launch.
"""

from .models import ConsentPurpose

CONSENT_TEXT_VERSION = "2026-10-v1"

CONSENT_TEXTS = {
    ConsentPurpose.PROCESS_ENQUIRY: (
        "I agree that you may use the details and medical documents I share to "
        "contact me about my enquiry, and share them with partner hospitals and "
        "doctors in India so they can suggest a treatment plan and an estimated "
        "cost. I can withdraw this consent at any time."
    ),
    ConsentPurpose.MARKETING: (
        "Send me occasional updates about treatments and services by email or "
        "WhatsApp. I can unsubscribe at any time."
    ),
}
