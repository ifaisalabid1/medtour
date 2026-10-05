from apps.core.rich_text import BasicRichTextField, RichTextField


def clean(field, html):
    return field.clean(html, None)


def test_scripts_and_event_handlers_are_removed():
    html = '<p onclick="steal()">Hi <strong>there</strong></p><script>alert(1)</script>'

    assert clean(RichTextField(), html) == "<p>Hi <strong>there</strong></p>"


def test_javascript_links_are_neutralised_and_safe_links_kept():
    html = '<p><a href="javascript:alert(1)">bad</a> <a href="https://example.com">good</a></p>'

    assert clean(RichTextField(), html) == (
        '<p><a>bad</a> <a href="https://example.com">good</a></p>'
    )


def test_only_h2_and_h3_headings_are_allowed():
    # The page title is the only H1.
    html = "<h1>Title</h1><h2>Section</h2><h3>Sub</h3><h4>Deep</h4>"

    assert clean(RichTextField(), html) == "Title<h2>Section</h2><h3>Sub</h3>Deep"


def test_basic_rich_text_has_no_headings_or_tables():
    html = "<h2>Heading</h2><table><tr><td>Cell</td></tr></table><p><em>ok</em></p>"

    assert clean(BasicRichTextField(), html) == "HeadingCell<p><em>ok</em></p>"
