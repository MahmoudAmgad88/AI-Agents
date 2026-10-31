import httpx
import pytest

from agent101.config import LiveSettings
from agent101.providers import LiveProviders, ProviderError


def fake_settings() -> LiveSettings:
    return LiveSettings(
        openai_key="fake-openai-key",
        tavily_key="fake-tavily-key",
        scrapegraph_key="fake-scrapegraph-key",
    )


def test_search_returns_validated_candidates():
    def handler(request):
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "title": "Fictional coffee machine",
                        "url": "https://www.amazon.eg/example-product",
                        "score": 0.92,
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)

    with httpx.Client(transport=transport) as client:
        provider = LiveProviders(client, fake_settings())
        hits = provider.search("coffee machine", ["www.amazon.eg"], limit=1)

    assert len(hits) == 1
    assert hits[0].url == "https://www.amazon.eg/example-product"
    assert hits[0].score == 0.92


@pytest.mark.parametrize("status", [401, 429, 500])
def test_provider_errors_hide_response_body(status):
    def handler(request):
        return httpx.Response(
            status,
            json={"error": "sensitive provider details"},
        )

    transport = httpx.MockTransport(handler)

    with httpx.Client(transport=transport) as client:
        provider = LiveProviders(client, fake_settings())

        with pytest.raises(ProviderError) as caught:
            provider.search("coffee machine", ["www.amazon.eg"], limit=1)

    assert str(caught.value) == f"Provider returned HTTP {status}."


def test_extract_parses_product_facts():
    def handler(request):
        return httpx.Response(
            200,
            json={
                "json": {
                    "product_name": "Fictional demo machine",
                    "price": "2499.50",
                    "currency": "EGP",
                    "availability": "in_stock",
                    "price_excerpt": "Fictional price: EGP 2499.50",
                }
            },
        )

    transport = httpx.MockTransport(handler)

    with httpx.Client(transport=transport) as client:
        provider = LiveProviders(client, fake_settings())
        facts = provider.extract("https://www.amazon.eg/example-product")

    assert facts.price == "2499.50"
    assert facts.currency == "EGP"
