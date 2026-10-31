from agent101.models import (
    ExtractedProductFacts,
    ProcurementRequest,
    SearchHit,
)
from agent101.providers import ProviderError

OFFERS = {
    "https://store.example/basic": ("Fictional Basic Machine", "2499.50"),
    "https://store.example/plus": ("Fictional Plus Machine", "3999.00"),
}


def demo_request() -> ProcurementRequest:
    return ProcurementRequest(
        product_name="office coffee machine",
        company_context="A fictional office needs a coffee machine in Egypt.",
        allowed_domains=["store.example"],
        max_queries=1,
        max_results_per_query=2,
        max_pages=2,
        top_products=2,
    )


class DemoProviders:
    """Implement the provider interface entirely with invented local data."""

    def search(self, query, domains, limit):
        return [SearchHit(title=name, url=url, score=0.9) for url, (name, price) in OFFERS.items()][
            :limit
        ]

    def extract(self, url):
        if url not in OFFERS:
            raise ProviderError("No demo data exists for this URL.")

        name, price = OFFERS[url]

        return ExtractedProductFacts(
            product_name=name,
            price=price,
            currency="EGP",
            availability="in_stock",
            price_excerpt=f"Invented demo price: EGP {price}",
        )
