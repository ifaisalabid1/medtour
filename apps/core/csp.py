from django.conf import settings
from django.middleware.csp import ContentSecurityPolicyMiddleware
from django.urls import reverse


class SiteContentSecurityPolicyMiddleware(ContentSecurityPolicyMiddleware):
    """Strict Content-Security-Policy for the public site, ADMIN_CSP for the admin.

    The admin (Unfold and the rich-text editor) needs inline styles, an inline
    import map and the standard Alpine.js build, which evaluates strings as
    code. Those allowances are confined to admin pages, which are only served
    to logged-in staff. Patients only ever get the strict policy.
    """

    def process_response(self, request, response):
        is_admin = request.path.startswith(reverse("admin:index"))
        # Respect a policy set explicitly by a view (Django's csp_override).
        if is_admin and not hasattr(response, "_csp_config"):
            response._csp_config = settings.ADMIN_CSP
        return super().process_response(request, response)
