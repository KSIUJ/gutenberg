import pytest
from django.core.exceptions import ValidationError

from control.models import validate_n_up, validate_pages_to_print


@pytest.mark.parametrize(
    "value",
    [
        "",
        "1",
        "1-3",
        "1,3-4,10",
    ],
)
def test_validate_pages_to_print_accepts_expected_formats(value):
    # The form and serializer layer should be able to pass these straight through.
    validate_pages_to_print(value)


@pytest.mark.parametrize(
    "value",
    [
        "abc",
        "0",
        "3-1",
        "1,,2",
        "1-2-3",
    ],
)
def test_validate_pages_to_print_rejects_invalid_formats(value):
    with pytest.raises(ValidationError):
        validate_pages_to_print(value)


@pytest.mark.parametrize("value", [1, 2, 4, 8, 9, 18])
def test_validate_n_up_accepts_supported_layouts(value):
    validate_n_up(value)


@pytest.mark.parametrize("value", [3, 5, 6, 7, 10])
def test_validate_n_up_rejects_unsupported_layouts(value):
    with pytest.raises(ValueError):
        validate_n_up(value)
