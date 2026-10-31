from datetime import UTC, datetime

from pydantic import ValidationError

from agent101.models import ProcurementRequest, Product, SearchHit
from agent101.policy import PolicyError, validate_url
from agent101.providers import ProviderError


class EvidenceLedger:
    """Keep the plan, observations, attempts, and accepted offers for one run."""

    def __init__(self, request: ProcurementRequest, providers):
        self.request = request
        self.providers = providers

        self.queries: list[str] = []
        self.searches: dict[str, list[SearchHit] | None] = {}
        self.hits: dict[str, SearchHit] = {}
        self.products: dict[str, Product] = {}
        self.extraction_attempts: set[str] = set()
        self.rejections: list[dict[str, str]] = []

    def accept_plan(self, queries: list[str]) -> list[str]:
        """Approve a bounded, distinct set of queries."""

        queries = [query.strip() for query in queries]

        if not queries or any(not query for query in queries):
            raise PolicyError("The plan must contain nonempty queries.")

        if len(queries) > self.request.max_queries:
            raise PolicyError("The plan exceeds the query limit.")

        if len(set(queries)) != len(queries):
            raise PolicyError("Planned queries must be distinct.")

        if self.queries and queries != self.queries:
            raise PolicyError("An approved plan cannot be replaced.")

        self.queries = queries
        return queries

    def search(self, query: str) -> list[SearchHit]:
        """Execute an approved query once and remember approved candidates."""

        query = query.strip()

        if query not in self.queries:
            raise PolicyError("Search only a query in the approved plan.")

        if query in self.searches:
            cached = self.searches[query]
            if cached is None:
                raise PolicyError("This search already failed; no automatic retry.")
            return cached

        self.searches[query] = None

        found = self.providers.search(
            query,
            self.request.allowed_domains,
            self.request.max_results_per_query,
        )

        accepted = []

        for hit in found[: self.request.max_results_per_query]:
            try:
                url = validate_url(hit.url, self.request.allowed_domains)
            except PolicyError as exc:
                self.rejections.append({"stage": "search", "target": hit.url, "reason": str(exc)})
                continue

            normalized = hit.model_copy(update={"url": url})
            self.hits[url] = normalized
            accepted.append(normalized)

        self.searches[query] = accepted
        return accepted

    def extract(self, url: str) -> Product:
        """Extract an observed URL, enforcing the page budget."""

        url = validate_url(url, self.request.allowed_domains)

        if url not in self.hits:
            raise PolicyError("Extract only a URL observed in this run's searches.")

        if url in self.products:
            return self.products[url]

        if url in self.extraction_attempts:
            raise PolicyError("This extraction already failed; no automatic retry.")

        if len(self.extraction_attempts) >= self.request.max_pages:
            raise PolicyError("The extraction page budget is exhausted.")

        self.extraction_attempts.add(url)

        try:
            facts = self.providers.extract(url)

            product = Product.model_validate(
                {
                    **facts.model_dump(),
                    "source_url": url,
                    "observed_at": datetime.now(UTC),
                }
            )
        except (ProviderError, ValidationError) as exc:
            message = (
                str(exc)
                if isinstance(exc, ProviderError)
                else "Extracted offer is incomplete or ineligible."
            )
            self.rejections.append({"stage": "extract", "target": url, "reason": message})
            raise PolicyError(message) from None

        self.products[url] = product
        return product

    def shortlist(self) -> list[Product]:
        """Return the lowest observed eligible item prices."""

        if not self.products:
            raise PolicyError("No eligible products were extracted.")

        ordered = sorted(
            self.products.values(),
            key=lambda product: (product.price, product.source_url),
        )

        return ordered[: self.request.top_products]
