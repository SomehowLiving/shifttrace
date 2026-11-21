"""Runtime configuration. Secrets come only from environment / backend/.env."""
from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent
load_dotenv(BACKEND_DIR / ".env", override=False)


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


@dataclass
class Settings:
    agora_app_id: str = field(default_factory=lambda: _env("AGORA_APP_ID"))
    agora_app_certificate: str = field(default_factory=lambda: _env("AGORA_APP_CERTIFICATE"))
    # Optional Agora RESTful API key (Console > RESTful API: Customer ID + Customer Secret). When set, Conversational AI
    # REST calls use HTTP Basic auth with it; otherwise they use tokens built from the App ID and certificate.
    agora_customer_id: str = field(default_factory=lambda: _env("AGORA_CUSTOMER_ID") or _env("CUSTOMER_ID"))
    agora_customer_secret: str = field(default_factory=lambda: _env("AGORA_CUSTOMER_SECRET") or _env("CUSTOMER_SECRET"))
    murf_api_key: str = field(default_factory=lambda: _env("MURF_API_KEY"))
    murf_voice_id: str = field(default_factory=lambda: _env("MURF_VOICE_ID", "en-IN-isha"))
    murf_locale: str = field(default_factory=lambda: _env("MURF_LOCALE", "en-IN"))
    murf_base_url: str = field(
        default_factory=lambda: _env("MURF_BASE_URL", "wss://global.api.murf.ai/v1/speech/stream-input")
    )
    llm_model: str = field(default_factory=lambda: _env("AGORA_LLM_MODEL", "gpt-4o-mini"))
    # Public URL (tunnel) where Agora cloud can reach the MCP server, e.g. https://x.trycloudflare.com
    mcp_public_url: str = field(default_factory=lambda: _env("MCP_PUBLIC_URL").rstrip("/"))
    # Bearer token Agora must present to the MCP server. Random per process if unset.
    mcp_token: str = field(default_factory=lambda: _env("MCP_TOKEN") or secrets.token_urlsafe(24))
    # Hosted mode (Render and similar): one public port ($PORT) serves the console and /mcp together.
    single_port: bool = field(default_factory=lambda: _env("SHIFTTRACE_SINGLE_PORT") in ("1", "true", "yes"))
    api_port: int = field(default_factory=lambda: int(_env("PORT") if _env("SHIFTTRACE_SINGLE_PORT") in ("1", "true", "yes") and _env("PORT") else _env("API_PORT", "8000")))
    # Required when the console is reachable from the internet (HTTP Basic auth, any user name).
    console_password: str = field(default_factory=lambda: _env("CONSOLE_PASSWORD"))
    mcp_port: int = field(default_factory=lambda: int(_env("MCP_PORT", "8001")))
    db_path: Path = field(default_factory=lambda: Path(_env("SHIFTTRACE_DB", str(BACKEND_DIR / "data" / "shifttrace.db"))))
    media_dir: Path = field(default_factory=lambda: BACKEND_DIR / "data" / "media")
    frontend_dist: Path = field(default_factory=lambda: PROJECT_DIR / "frontend" / "dist")
    # How long approve_procurement_request waits for the technician's spoken "yes" to arrive.
    approval_wait_s: float = field(default_factory=lambda: float(_env("APPROVAL_WAIT_S", "4")))

    @property
    def agora_ready(self) -> bool:
        return bool(self.agora_app_id and self.agora_app_certificate)

    @property
    def murf_ready(self) -> bool:
        return bool(self.murf_api_key)

    def readiness(self) -> dict:
        return {
            "agora_credentials": self.agora_ready,
            "agora_rest_auth": "customer key" if (self.agora_customer_id and self.agora_customer_secret) else "app certificate token",
            "murf_key": self.murf_ready,
            "mcp_public_url": self.mcp_public_url or None,
            "llm_model": self.llm_model,
            "murf_voice_id": self.murf_voice_id,
        }


settings = Settings()
