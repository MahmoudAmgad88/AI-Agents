import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, SecretStr

from agent101.models import ProcurementRequest
from agent101.policy import PolicyError


class LiveSettings(BaseModel):
    """Credentials and model selection for a live run."""

    openai_key: SecretStr
    tavily_key: SecretStr
    scrapegraph_key: SecretStr
    model: str = "openai/gpt-4o"


# load_request: turns the JSON file into your validated ProcurementRequest
def load_request(path: str | Path) -> ProcurementRequest:
    """Read JSON and validate it before starting external work."""

    text = Path(path).read_text(encoding="utf-8-sig")
    return ProcurementRequest.model_validate_json(text)


# reads only .env in the current directory
def load_settings() -> LiveSettings:
    """Read this project's .env while preserving existing environment values."""

    load_dotenv(Path.cwd() / ".env", override=False)

    names = {
        "openai_key": "OPENAI_API_KEY",
        "tavily_key": "TAVILY_API_KEY",
        "scrapegraph_key": "SGAI_API_KEY",
    }

    values = {field: os.getenv(variable, "").strip() for field, variable in names.items()}

    missing = [names[field] for field, value in values.items() if not value]
    if missing:
        raise PolicyError("Missing environment variables: " + ", ".join(missing))

    model = os.getenv("AGENT101_MODEL", "").strip() or "openai/gpt-4o"
    return LiveSettings(**values, model=model)
