from typing import Any

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.http import HttpRequest


class EmailOrUsernameBackend(ModelBackend):
    """Authenticate with either the username or the (case-insensitive) email."""

    def authenticate(
        self, request: HttpRequest | None, username: str | None = None,
        password: str | None = None, **kwargs: Any,
    ) -> User | None:
        if not username or password is None:
            return None
        if "@" in username:
            user = User.objects.filter(email__iexact=username).first()
            if user is not None and user.check_password(password) and self.user_can_authenticate(user):
                return user
            return None
        result = super().authenticate(request, username=username, password=password, **kwargs)
        return result if isinstance(result, User) else None
