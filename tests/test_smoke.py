"""Smoke tests so CI can run pytest -m unit."""

import pytest


@pytest.mark.unit
def test_seej_importable():
    import seej  # noqa: F401
