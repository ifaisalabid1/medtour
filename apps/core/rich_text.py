"""Rich text fields for editorial content.

Every field is sanitised with nh3 using rules generated from the same
extensions the editor offers, so the stored HTML can only ever contain the
tags editors can actually create. Sanitising happens in the field's clean(),
which the admin always runs. Code that writes rich text directly must call
`full_clean()` before saving.
"""

from django_prose_editor.fields import ProseEditorField

# Headings start at H2: the page title is the only H1 (good for SEO and
# accessibility).
ARTICLE_EXTENSIONS = {
    "Bold": True,
    "Italic": True,
    "Heading": {"levels": [2, 3]},
    "BulletList": True,
    "OrderedList": True,
    "ListItem": True,
    "Blockquote": True,
    "HardBreak": True,
    "Link": {"enableTarget": False, "protocols": ["http", "https", "mailto"]},
    "Table": True,
    "TableRow": True,
    "TableHeader": True,
    "TableCell": True,
    "History": True,
}

# Short answers and descriptions: no headings or tables.
BASIC_EXTENSIONS = {
    "Bold": True,
    "Italic": True,
    "BulletList": True,
    "OrderedList": True,
    "ListItem": True,
    "HardBreak": True,
    "Link": {"enableTarget": False, "protocols": ["http", "https", "mailto"]},
    "History": True,
}


def RichTextField(*args, **kwargs):
    """Full rich text: headings, lists, links, tables. For long content."""
    return ProseEditorField(
        *args, extensions=ARTICLE_EXTENSIONS, sanitize=True, **kwargs
    )


def BasicRichTextField(*args, **kwargs):
    """Bold, italic, lists and links only. For short descriptions and answers."""
    return ProseEditorField(*args, extensions=BASIC_EXTENSIONS, sanitize=True, **kwargs)
