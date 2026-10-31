# Agent101 Procurement Assistant

A Python application using CrewAI to research products,
validate extracted offers, and generate an HTML comparison report.

## Workflow

Request -> Plan -> Search -> Extract -> Compare -> Report


## Setup

Requires Python 3.12 and uv.

Install the locked dependencies with `uv sync --frozen`.

Copy `.env.example` to `.env` and configure the credentials for live mode.

## Commands

- Validate input: `uv run agent101 validate`
- Offline demonstration: `uv run agent101 demo`
- Live workflow: `uv run agent101 run --config examples/live-smoke.json`
- Tests: `uv run pytest`
- Lint: `uv run ruff check src tests`

## Architecture

Four sequential CrewAI agents plan queries, research store pages,
extract offers, and write an assessment.

Python enforces query and extraction limits, approved hosts,
observed URLs, and product eligibility through a run-scoped evidence ledger.

The HTML comparison uses validated product records.
Model commentary appears separately.

## Offline demonstration

Demo mode uses invented products, prices, and URLs.
It bypasses CrewAI, reads no API credentials, and makes no network calls.

## Run artifacts

Each execution creates a separate directory containing:

- `request.json`: validated input.
- `evidence.json`: observations, accepted products, attempts, and rejections.
- `run.json`: execution status and metadata.
- `narrative.json`: assessment after successful generation.
- `report.html`: report after successful rendering.

Failed executions preserve available evidence and failure metadata.

## Limitations

Extraction is model-assisted and may be inaccurate.
Results cover observed eligible offers, not the entire market.
Shipping, taxes, warranty, suitability, and retailer details require review.
The application does not purchase products.