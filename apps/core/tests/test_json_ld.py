import json
import re

from django.template import Context, Template


def render(data):
    return Template("{% load json_ld %}{% json_ld data %}").render(
        Context({"data": data})
    )


def test_renders_a_json_ld_script_element():
    html = render({"@type": "Hospital", "name": "Apollo"})

    assert html.startswith('<script type="application/ld+json">')
    payload = re.search(r">(.*)</script>$", html).group(1)
    assert json.loads(payload) == {"@type": "Hospital", "name": "Apollo"}


def test_text_cannot_break_out_of_the_script_element():
    html = render({"name": "Evil</script><script>alert(1)</script> & Co"})

    # Only the real closing tag remains; the injected ones are escaped...
    assert html.count("</script>") == 1
    # ...and the data still reads back exactly as it was written.
    payload = re.search(r">(.*)</script>$", html).group(1)
    assert json.loads(payload)["name"] == "Evil</script><script>alert(1)</script> & Co"
