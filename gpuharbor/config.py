from __future__ import annotations

import re
from pathlib import Path

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


_REPOSITORY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*$")
INTERNAL_HOSTS = ("controller",)
_DIGEST = re.compile(r"^.+@sha256:[0-9a-fA-F]{64}$")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    runpod_api_key: SecretStr
    control_token: SecretStr
    model_access_token: SecretStr
    runtime_gateway_token: SecretStr
    gpuharbor_admin_username: str = "admin"
    gpuharbor_admin_password: SecretStr
    gpuharbor_session_secret: SecretStr
    gpuharbor_cookie_secure: bool = False
    gpuharbor_trusted_hosts: str = "localhost,127.0.0.1,testserver"
    gpuharbor_login_max_attempts: int = 5
    gpuharbor_login_window_seconds: int = 300
    gpuharbor_max_request_mb: int = 20
    # Opt-in: fetch the latest GitHub release once a day and show an update hint.
    gpuharbor_update_check: bool = False
    gpuharbor_update_repo: str = "lightcr1/gpuharbor"

    runpod_api_base: str = "https://api.runpod.io/v2"
    runpod_pod_name: str = "gpuharbor-model"
    runpod_datacenter_ids: str = "EU-SE-1,CA-MTL-1"
    runpod_container_disk_gb: int = 20
    runpod_idle_stop_minutes: int = 30
    runpod_allow_billable_actions: bool = False
    runpod_pod_id: str = ""

    runtime_image_vllm: str = ""
    runtime_image_llama_cpp: str = ""
    runtime_image_bonsai: str = ""
    huggingface_token: SecretStr | None = None

    # models_path is the legacy mutable catalog and is migrated once if present.
    models_path: Path = Path("/data/models.json")
    user_catalog_path: Path = Path("/data/user-models.json")
    bundled_models_path: Path = Path("registry/models.json")
    runtimes_path: Path = Path("registry/runtimes.json")
    state_path: Path = Path("/data/state.json")
    preferences_path: Path = Path("/data/preferences.json")

    @field_validator("gpuharbor_update_repo")
    @classmethod
    def valid_update_repo(cls, value: str) -> str:
        if not _REPOSITORY.fullmatch(value):
            raise ValueError("GPUHARBOR_UPDATE_REPO must look like owner/name")
        return value

    @model_validator(mode="after")
    def reject_template_credentials(self) -> "Settings":
        """Refuse to serve with the public placeholder values from .env.example."""
        credentials = {
            "CONTROL_TOKEN": self.control_token,
            "MODEL_ACCESS_TOKEN": self.model_access_token,
            "RUNTIME_GATEWAY_TOKEN": self.runtime_gateway_token,
            "GPUHARBOR_ADMIN_PASSWORD": self.gpuharbor_admin_password,
            "GPUHARBOR_SESSION_SECRET": self.gpuharbor_session_secret,
        }
        for name, secret in credentials.items():
            value = secret.get_secret_value()
            if not value or value.lower().startswith("replace"):
                raise ValueError(
                    f"{name} is empty or still the template placeholder. Run ./scripts/init-env."
                )
        return self

    @property
    def datacenter_ids(self) -> list[str]:
        return [value.strip() for value in self.runpod_datacenter_ids.split(",") if value.strip()]

    @property
    def configured_hosts(self) -> list[str]:
        return [value.strip() for value in self.gpuharbor_trusted_hosts.split(",") if value.strip()]

    @property
    def trusted_hosts(self) -> list[str]:
        # Open WebUI and OpenHands reach the controller under its Compose service name.
        hosts = self.configured_hosts
        return hosts + [name for name in INTERNAL_HOSTS if name not in hosts]

    def runtime_image(self, runtime_id: str) -> str:
        return {
            "vllm": self.runtime_image_vllm,
            "llama-cpp": self.runtime_image_llama_cpp,
            "bonsai": self.runtime_image_bonsai,
        }.get(runtime_id, "")

    def runtime_image_ready(self, runtime_id: str) -> bool:
        return bool(_DIGEST.fullmatch(self.runtime_image(runtime_id)))

    def live_errors(self, runtime_id: str) -> list[str]:
        errors: list[str] = []
        values = {
            "RUNPOD_API_KEY": self.runpod_api_key.get_secret_value(),
            "CONTROL_TOKEN": self.control_token.get_secret_value(),
            "MODEL_ACCESS_TOKEN": self.model_access_token.get_secret_value(),
            "RUNTIME_GATEWAY_TOKEN": self.runtime_gateway_token.get_secret_value(),
            "GPUHARBOR_ADMIN_PASSWORD": self.gpuharbor_admin_password.get_secret_value(),
            "GPUHARBOR_SESSION_SECRET": self.gpuharbor_session_secret.get_secret_value(),
        }
        for name, value in values.items():
            if len(value) < 32 or "replace" in value.lower():
                errors.append(f"{name} must be a unique random value with at least 32 characters")
        if len(set(values.values())) != len(values):
            errors.append("Every credential must use a different value")
        if not self.datacenter_ids:
            errors.append("RUNPOD_DATACENTER_IDS must not be empty")
        if not self.configured_hosts:
            errors.append("GPUHARBOR_TRUSTED_HOSTS must not be empty")
        if self.gpuharbor_login_max_attempts < 1:
            errors.append("GPUHARBOR_LOGIN_MAX_ATTEMPTS must be positive")
        if self.gpuharbor_login_window_seconds < 1:
            errors.append("GPUHARBOR_LOGIN_WINDOW_SECONDS must be positive")
        if not 1 <= self.gpuharbor_max_request_mb <= 1024:
            errors.append("GPUHARBOR_MAX_REQUEST_MB must be between 1 and 1024")
        if not self.runtime_image_ready(runtime_id):
            errors.append(f"Runtime image for {runtime_id} must use an immutable sha256 digest")
        return errors
