import pytest
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()
PASSWORD = "a-long-test-password"

pytestmark = pytest.mark.django_db


def test_create_user_normalises_email():
    user = User.objects.create_user(
        email="  Priya.Sharma@Example.COM ", password=PASSWORD
    )

    assert user.email == "priya.sharma@example.com"
    assert user.check_password(PASSWORD)
    assert not user.is_staff
    assert not user.is_superuser


def test_create_user_requires_email():
    with pytest.raises(ValueError, match="email"):
        User.objects.create_user(email="", password=PASSWORD)


def test_create_superuser_sets_flags():
    admin = User.objects.create_superuser(email="admin@example.com", password=PASSWORD)

    assert admin.is_staff
    assert admin.is_superuser


def test_create_superuser_rejects_non_staff():
    with pytest.raises(ValueError, match="is_staff"):
        User.objects.create_superuser(
            email="admin@example.com", password=PASSWORD, is_staff=False
        )


def test_login_email_is_case_insensitive():
    User.objects.create_user(email="doctor@example.com", password=PASSWORD)

    assert authenticate(username="Doctor@Example.com", password=PASSWORD) is not None


def test_email_uniqueness_ignores_case():
    User.objects.create_user(email="dup@example.com", password=PASSWORD)
    duplicate = User(email="DUP@example.com")

    with pytest.raises(ValidationError) as exc:
        duplicate.full_clean(exclude=["password"])

    assert "email" in exc.value.message_dict
