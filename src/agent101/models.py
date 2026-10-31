from decimal import Decimal
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class ProcurementRequest(BaseModel):
    """Describe the buyer's need and bound the research workload."""

    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        str_strip_whitespace=True,
    )

    product_name: str = Field(min_length=3, max_length=200)
    company_context: str = Field(min_length=10, max_length=2000)

    country: Literal["Egypt"] = "Egypt"
    language: Literal["English"] = "English"
    currency: Literal["EGP"] = "EGP"

    allowed_domains: list[str] = Field(min_length=1, max_length=10)

    max_queries: int = Field(default=2, ge=1, le=5)
    max_results_per_query: int = Field(default=3, ge=1, le=10)
    max_pages: int = Field(default=3, ge=1, le=10)
    top_products: int = Field(default=3, ge=1, le=5)


class SearchHit(BaseModel):
    """One candidate page returned by the search provider."""

    title: str = Field(min_length=1)
    url: str = Field(min_length=1)
    score: float = Field(ge=0, le=1)


class ExtractedProductFacts(BaseModel):
    """The extraction provider may return incomplete information."""

    product_name: str | None
    price: str | None
    currency: str | None
    availability: Literal["in_stock", "out_of_stock", "unknown"] | None
    price_excerpt: str | None


class Product(BaseModel):
    """An eligible offer accepted by our application."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    product_name: str = Field(min_length=1)
    price: Decimal = Field(gt=0, allow_inf_nan=False)
    currency: Literal["EGP"]
    availability: Literal["in_stock"]
    price_excerpt: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    observed_at: AwareDatetime


class QueryPlan(BaseModel):
    queries: list[str] = Field(min_length=1, max_length=5)


class SourceSelection(BaseModel):
    urls: list[str] = Field(min_length=1, max_length=10)


class ReportNarrative(BaseModel):
    executive_summary: str = Field(min_length=10, max_length=1500)
    limitations: list[str] = Field(min_length=1, max_length=5)
