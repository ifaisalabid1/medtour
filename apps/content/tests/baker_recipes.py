from model_bakery.recipe import Recipe, foreign_key, seq

from apps.catalog.tests.baker_recipes import treatment
from apps.content.models import FAQ, Article, Author, Testimonial

author = Recipe(Author, name=seq("Author "), slug=seq("author-"))

medical_reviewer = author.extend(
    name=seq("Dr Reviewer "), slug=seq("reviewer-"), is_medical_professional=True
)

article = Recipe(
    Article,
    title=seq("Article "),
    slug=seq("article-"),
    summary="A short summary.",
    body="<p>Body</p>",
    author=foreign_key(author),
    medical_reviewer=foreign_key(medical_reviewer),
    reviewed_on="2026-10-01",
    is_published=True,
)

faq = Recipe(
    FAQ,
    question=seq("Question "),
    answer="<p>Answer</p>",
    treatment=foreign_key(treatment),
    condition=None,
    is_published=True,
)

testimonial = Recipe(
    Testimonial,
    patient_display_name=seq("Patient "),
    country="BD",
    quote="Excellent care.",
    consent_obtained_on="2026-09-01",
    is_published=True,
)
