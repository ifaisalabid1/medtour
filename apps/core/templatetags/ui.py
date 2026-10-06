"""Class lists for UI components, kept in Python so they live in one place.

Tailwind scans this file (see frontend/tailwind.css), so every class written
here ends up in the stylesheet.
"""

from django import template

register = template.Library()

_BASE = (
    "inline-flex items-center justify-center gap-2 rounded-full font-semibold "
    "transition-colors disabled:cursor-not-allowed disabled:opacity-60"
)
_VARIANTS = {
    # White on brand blue: 5.8:1 contrast (7.9:1 on hover).
    "primary": "bg-brand-600 text-white hover:bg-brand-700",
    "dark": "bg-brand-950 text-white hover:bg-brand-900",
    "outline": (
        "border border-slate-300 bg-white text-slate-900 "
        "hover:border-brand-600 hover:text-brand-700"
    ),
    # WhatsApp green is too light for white text, so the text is near-black.
    "whatsapp": "bg-[#25d366] text-slate-950 hover:bg-[#3ee07a]",
}
_SIZES = {
    "sm": "px-4 py-2 text-sm",
    "md": "px-5 py-2.5 text-sm",
    "lg": "px-7 py-3.5 text-base",
}


@register.simple_tag
def button_classes(variant: str = "primary", size: str = "md") -> str:
    return f"{_BASE} {_VARIANTS.get(variant, _VARIANTS['primary'])} {_SIZES.get(size, _SIZES['md'])}"
