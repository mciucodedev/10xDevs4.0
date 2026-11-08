import importlib
import os
from typing import Any
from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from config import settings


def reload_settings(env: dict[str, str]) -> Any:
    with mock.patch.dict(os.environ, {**env, 'DJANGO_SKIP_DOTENV': '1'}, clear=True):
        return importlib.reload(settings)


class SettingsTests(SimpleTestCase):
    def tearDown(self) -> None:
        importlib.reload(settings)

    def test_secret_key_comes_from_env(self) -> None:
        mod = reload_settings({"DJANGO_SECRET_KEY": "abc123"})
        self.assertEqual(mod.SECRET_KEY, "abc123")
        self.assertFalse(mod.DEBUG)

    def test_missing_secret_key_without_debug_raises(self) -> None:
        with self.assertRaises(ImproperlyConfigured):
            reload_settings({})

    def test_debug_without_secret_key_uses_dev_key(self) -> None:
        mod = reload_settings({"DJANGO_DEBUG": "1"})
        self.assertTrue(mod.DEBUG)
        self.assertTrue(mod.SECRET_KEY)

    def test_allowed_hosts_parsed_from_comma_list(self) -> None:
        mod = reload_settings({"DJANGO_SECRET_KEY": "k", "DJANGO_ALLOWED_HOSTS": "a.com, b.com"})
        self.assertEqual(mod.ALLOWED_HOSTS, ["a.com", "b.com"])

    def test_timezone_is_warsaw(self) -> None:
        mod = reload_settings({"DJANGO_SECRET_KEY": "k"})
        self.assertEqual(mod.TIME_ZONE, "Europe/Warsaw")

    def test_min_ratings_to_submit_default_is_3(self) -> None:
        mod = reload_settings({"DJANGO_SECRET_KEY": "k"})
        self.assertEqual(mod.MIN_RATINGS_TO_SUBMIT, 3)
