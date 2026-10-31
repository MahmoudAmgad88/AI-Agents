from decimal import Decimal
from unittest.mock import Mock

import pytest

from agent101.evidence import EvidenceLedger
from agent101.models import (
    ExtractedProductFacts,
    ProcurementRequest,
    SearchHit,
)
from agent101.policy import PolicyError
from agent101.providers import ProviderError


@pytest.fixture
def ledger():
    request = ProcurementRequest(
        product_name="Coffee machine",
        company_context="An example company needs an office coffee machine.",
        allowed_domains=["www.amazon.eg"],
        max_queries=1,
        max_pages=1,
        top_products=1,
    )

    provider = Mock()
    provider.search.return_value = [
        SearchHit(
            title="Fictional demo machine",
            url="https://www.amazon.eg/example-product",
            score=0.9,
        )
    ]
    provider.extract.return_value = ExtractedProductFacts(
        product_name="Fictional demo machine",
        price="2499.50",
        currency="EGP",
        availability="in_stock",
        price_excerpt="Fictional price: EGP 2499.50",
    )

    result = EvidenceLedger(request, provider)
    result.accept_plan(["coffee machine Egypt"])
    result.search("coffee machine Egypt")
    return result


def test_unobserved_url_never_reaches_provider(ledger):
    with pytest.raises(PolicyError, match="observed"):
        ledger.extract("https://www.amazon.eg/unobserved-product")

    ledger.providers.extract.assert_not_called()


def test_failed_extraction_cannot_be_retried(ledger):
    ledger.providers.extract.side_effect = ProviderError("Extraction failed.")
    url = "https://www.amazon.eg/example-product"

    with pytest.raises(PolicyError):
        ledger.extract(url)

    with pytest.raises(PolicyError, match="already failed"):
        ledger.extract(url)

    assert ledger.providers.extract.call_count == 1


def test_successful_extraction_is_cached(ledger):
    url = "https://www.amazon.eg/example-product"

    first = ledger.extract(url)
    second = ledger.extract(url)

    assert first is second
    assert first.source_url == url
    assert first.price == Decimal("2499.50")
    assert ledger.shortlist() == [first]
    assert ledger.providers.extract.call_count == 1
