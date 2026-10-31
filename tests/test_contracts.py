from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from agent101.models import Product
from agent101.policy import PolicyError, validate_url


def test_approved_url():
    url = "https://www.amazon.eg/example-product#details"

    assert validate_url(url, ["www.amazon.eg"]) == ("https://www.amazon.eg/example-product")


@pytest.mark.parametrize(
    "url",
    [
        "http://www.amazon.eg/product",
        "https://www.amazon.eg.evil.com/product",
        "https://www.amazon.eg@evil.com/product",
        "https://user:password@www.amazon.eg/product",
        "https://www.amazon.eg:8443/product",
    ],
)
def test_rejected_urls(url):
    with pytest.raises(PolicyError):
        validate_url(url, ["www.amazon.eg"])


@pytest.mark.parametrize(
    "changes",
    [
        {"price": "0"},
        {"price": "-100"},
        {"currency": "USD"},
        {"availability": "out_of_stock"},
    ],
)
def test_ineligible_product(changes):
    data = {
        "product_name": "Fictional demo coffee machine",
        "price": "3499.99",
        "currency": "EGP",
        "availability": "in_stock",
        "price_excerpt": "Fictional demo price: EGP 3499.99",
        "source_url": "https://www.amazon.eg/example-product",
        "observed_at": datetime.now(UTC),
    }
    data.update(changes)

    with pytest.raises(ValidationError):
        Product.model_validate(data)
