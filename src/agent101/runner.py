import json
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import httpx
from pydantic import BaseModel

from agent101.config import load_settings
from agent101.demo import DemoProviders
from agent101.evidence import EvidenceLedger
from agent101.models import ProcurementRequest, ReportNarrative
from agent101.policy import PolicyError
from agent101.providers import LiveProviders, ProviderError
from agent101.report import render_report


def run(
    request: ProcurementRequest,
    output: str | Path = "outputs",
    *,
    demo: bool = False,
) -> Path:
    now = datetime.now(UTC)
    run_id = now.strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]

    directory = (Path(output) / run_id).resolve()
    directory.mkdir(parents=True, exist_ok=False)

    manifest = {
        "run_id": run_id,
        "mode": "demo" if demo else "live",
        "status": "running",
        "started_at": now.isoformat(),
    }
    ledger = None

    write_json(directory / "request.json", request)

    try:
        with ExitStack() as stack:
            if demo:
                providers = DemoProviders()
            else:
                settings = load_settings()
                client = stack.enter_context(httpx.Client())
                providers = LiveProviders(client, settings)
                manifest["model"] = settings.model

            ledger = EvidenceLedger(request, providers)

            if demo:
                narrative = execute_demo(ledger)
            else:
                from agent101.crew import build_crew

                result = build_crew(ledger, settings).kickoff()

                if result.pydantic is not None:
                    narrative = ReportNarrative.model_validate(result.pydantic.model_dump())
                else:
                    narrative = ReportNarrative.model_validate_json(result.raw)

                manifest["token_usage"] = result.token_usage

            products = ledger.shortlist()

            write_json(directory / "narrative.json", narrative)

            html = render_report(
                request,
                products,
                narrative,
                demo=demo,
                run_id=run_id,
            )
            (directory / "report.html").write_text(html, encoding="utf-8")
            manifest["status"] = "success"

    except Exception as exc:
        manifest["status"] = "failed"
        manifest["error_type"] = type(exc).__name__

        reason = str(exc) if isinstance(exc, (PolicyError, ProviderError)) else type(exc).__name__
        manifest["reason"] = reason

        raise RunFailure(f"Run failed: {reason}. Artifacts: {directory}") from None

    finally:
        if ledger is not None:
            write_json(
                directory / "evidence.json",
                {
                    "queries": ledger.queries,
                    "searches": ledger.searches,
                    "products": list(ledger.products.values()),
                    "extraction_attempts": sorted(ledger.extraction_attempts),
                    "rejections": ledger.rejections,
                },
            )
            manifest["search_attempts"] = len(ledger.searches)
            manifest["extraction_attempts"] = len(ledger.extraction_attempts)

        manifest["finished_at"] = datetime.now(UTC).isoformat()
        write_json(directory / "run.json", manifest)

    return directory


class RunFailure(RuntimeError):
    """Execution failed; inspect the saved run artifacts."""


def write_json(path: Path, data):
    def encode(value):
        if isinstance(value, BaseModel):
            return value.model_dump(mode="json")
        raise TypeError(f"Unsupported JSON value: {type(value).__name__}")

    path.write_text(
        json.dumps(data, default=encode, indent=2),
        encoding="utf-8",
    )


def execute_demo(ledger: EvidenceLedger) -> ReportNarrative:
    query = "fictional office coffee machine demo"

    ledger.accept_plan([query])
    ledger.search(query)

    for url in list(ledger.hits)[: ledger.request.max_pages]:
        ledger.extract(url)

    ledger.shortlist()

    return ReportNarrative(
        executive_summary=(
            "This offline demonstration compares two invented coffee machines. "
            "The table is sorted by their fictional item prices."
        ),
        limitations=[
            "All products, URLs, and prices are invented.",
            "This demonstration bypasses CrewAI and all external APIs.",
        ],
    )
