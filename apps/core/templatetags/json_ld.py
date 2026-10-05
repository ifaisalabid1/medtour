import json

from django import template
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.safestring import mark_safe

register = template.Library()

# Escaping <, > and & means text such as "</script>" inside the data (a
# hospital name typed by an editor, say) can never close the script element
# early and inject HTML. JSON parsers read the escapes back as the original
# characters. This mirrors Django's own json_script filter.
_ESCAPES = {ord("<"): "\\u003C", ord(">"): "\\u003E", ord("&"): "\\u0026"}


@register.simple_tag
def json_ld(data: dict) -> str:
    """Render structured data as <script type="application/ld+json">."""
    payload = json.dumps(data, cls=DjangoJSONEncoder, ensure_ascii=False)
    # Safe: every character that could end the element is escaped above.
    return mark_safe(  # noqa: S308
        f'<script type="application/ld+json">{payload.translate(_ESCAPES)}</script>'
    )
