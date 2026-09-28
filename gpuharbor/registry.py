from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from pathlib import Path
from threading import RLock
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


_ID = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$")
_MODEL_REPOSITORY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*$")
_SERVED_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_GPU_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._()+/-]{1,99}$")
_ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]{2,80}$")
CATALOG_SCHEMA_VERSION = 1


class RuntimeDefinition(BaseModel):
    label: str = Field(min_length=1, max_length=100)
    image_env: str
    backend: Literal["vllm", "llama", "bonsai"]
    supports_gguf: bool = False
    status: Literal["stable", "experimental"] = "experimental"

    @field_validator("image_env")
    @classmethod
    def valid_image_environment_name(cls, value: str) -> str:
        if not _ENV_NAME.fullmatch(value):
            raise ValueError("image_env must be an uppercase environment variable name")
        return value


class ModelDefinition(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    model_id: str = Field(min_length=3, max_length=250)
    runtime: str
    served_names: list[str] = Field(min_length=1, max_length=8)
    capabilities: list[Literal["chat", "code", "tools", "vision"]] = Field(default_factory=list)
    context_length: int = Field(default=32768, ge=1024, le=262144)
    max_sequences: int = Field(default=2, ge=1, le=32)
    gpu_memory_utilization: float = Field(default=0.9, ge=0.5, le=0.99)
    gpu_type_ids: list[str] = Field(min_length=1, max_length=12)
    volume_gb: int = Field(default=64, ge=10, le=1000)
    status: Literal["stable", "experimental", "disabled"] = "experimental"
    license: str = Field(default="unknown", min_length=1, max_length=80)
    gated: bool = False
    verified: bool = False
    gguf_file: str | None = None
    trust_remote_code: bool = False
    reasoning_parser: Literal["qwen3"] | None = None
    tool_call_parser: Literal["qwen3_coder"] | None = None
    enable_auto_tool_choice: bool = False

    @field_validator("name", "description", "license")
    @classmethod
    def reject_control_characters(cls, value: str) -> str:
        if any(ord(character) < 32 and character not in {"\n", "\t"} for character in value):
            raise ValueError("Text must not contain control characters")
        return value.strip()

    @field_validator("model_id")
    @classmethod
    def valid_model_repository(cls, value: str) -> str:
        value = value.strip()
        if not _MODEL_REPOSITORY.fullmatch(value):
            raise ValueError("model_id must use the form owner/repository")
        return value

    @field_validator("runtime")
    @classmethod
    def valid_runtime_id(cls, value: str) -> str:
        if not _ID.fullmatch(value):
            raise ValueError("runtime must be a lowercase registry ID")
        return value

    @field_validator("served_names")
    @classmethod
    def valid_served_names(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if len(cleaned) != len(set(cleaned)) or any(not _SERVED_NAME.fullmatch(value) for value in cleaned):
            raise ValueError("Served names must be unique API-safe identifiers")
        return cleaned

    @field_validator("gpu_type_ids")
    @classmethod
    def valid_gpu_names(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values]
        if len(cleaned) != len(set(cleaned)) or any(not _GPU_NAME.fullmatch(value) for value in cleaned):
            raise ValueError("GPU names contain unsupported characters or duplicates")
        return cleaned

    @model_validator(mode="after")
    def validate_runtime_options(self) -> "ModelDefinition":
        if self.gguf_file:
            if self.gguf_file in {".", ".."} or "/" in self.gguf_file or "\\" in self.gguf_file:
                raise ValueError("gguf_file must be a plain filename")
            if not self.gguf_file.endswith(".gguf"):
                raise ValueError("gguf_file must end in .gguf")
        vllm_options = (
            self.trust_remote_code
            or self.reasoning_parser is not None
            or self.tool_call_parser is not None
            or self.enable_auto_tool_choice
        )
        if self.runtime != "vllm" and vllm_options:
            raise ValueError("vLLM options can only be used with the vllm runtime")
        if self.enable_auto_tool_choice and self.tool_call_parser is None:
            raise ValueError("Automatic tool choice requires a tool-call parser")
        return self


class UserCatalog(BaseModel):
    schema_version: Literal[1] = CATALOG_SCHEMA_VERSION
    custom: dict[str, ModelDefinition] = Field(default_factory=dict)
    overrides: dict[str, ModelDefinition] = Field(default_factory=dict)


class ModelRecord(BaseModel):
    model: ModelDefinition
    source: Literal["builtin", "custom", "override", "orphaned-override"]
    overridden: bool = False
    revision: str


class Registry:
    def __init__(
        self,
        bundled_models_path: Path,
        runtimes_path: Path,
        user_catalog_path: Path,
        legacy_models_path: Path | None = None,
    ) -> None:
        self.bundled_models_path = bundled_models_path
        self.runtimes_path = runtimes_path
        self.user_catalog_path = user_catalog_path
        self.legacy_models_path = legacy_models_path
        self._lock = RLock()
        self.user_catalog_path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            self._migrate_legacy_if_needed()
            if not self.user_catalog_path.exists():
                self._atomic_write_catalog(UserCatalog())

    @staticmethod
    def validate_id(item_id: str) -> None:
        if not _ID.fullmatch(item_id):
            raise ValueError("ID must contain 3-64 lowercase letters, numbers or hyphens")

    @staticmethod
    def revision(model: ModelDefinition) -> str:
        operational = model.model_dump(
            mode="json",
            exclude={"name", "description", "license", "gated", "verified", "status"},
        )
        canonical = json.dumps(operational, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]

    def runtimes(self) -> dict[str, RuntimeDefinition]:
        raw = json.loads(self.runtimes_path.read_text(encoding="utf-8"))
        runtimes = {key: RuntimeDefinition.model_validate(value) for key, value in raw.items()}
        for runtime_id in runtimes:
            self.validate_id(runtime_id)
        return runtimes

    def builtins(self) -> dict[str, ModelDefinition]:
        raw = json.loads(self.bundled_models_path.read_text(encoding="utf-8"))
        return self._validate_models(raw)

    def user_catalog(self) -> UserCatalog:
        with self._lock:
            raw = json.loads(self.user_catalog_path.read_text(encoding="utf-8"))
        version = raw.get("schema_version") if isinstance(raw, dict) else None
        if version != CATALOG_SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported user catalog schema {version!r}; expected {CATALOG_SCHEMA_VERSION}. "
                "Refusing to modify it to prevent data loss."
            )
        catalog = UserCatalog.model_validate(raw)
        self._validate_models(catalog.custom)
        self._validate_models(catalog.overrides)
        return catalog

    def records(self) -> dict[str, ModelRecord]:
        builtins = self.builtins()
        catalog = self.user_catalog()
        records: dict[str, ModelRecord] = {}
        for model_id, model in builtins.items():
            effective = catalog.overrides.get(model_id, model)
            overridden = model_id in catalog.overrides
            records[model_id] = ModelRecord(
                model=effective,
                source="override" if overridden else "builtin",
                overridden=overridden,
                revision=self.revision(effective),
            )
        for model_id, model in catalog.custom.items():
            if model_id in builtins:
                raise ValueError(f"Custom model {model_id} collides with a built-in model")
            records[model_id] = ModelRecord(
                model=model,
                source="custom",
                revision=self.revision(model),
            )
        for model_id, model in catalog.overrides.items():
            if model_id not in builtins:
                records[model_id] = ModelRecord(
                    model=model,
                    source="orphaned-override",
                    overridden=True,
                    revision=self.revision(model),
                )
        return records

    def models(self) -> dict[str, ModelDefinition]:
        return {model_id: record.model for model_id, record in self.records().items()}

    def save_model(self, model_id: str, model: ModelDefinition) -> None:
        self.validate_id(model_id)
        self._validate_runtime_match(model_id, model)
        with self._lock:
            builtins = self.builtins()
            catalog = self.user_catalog()
            if model_id in builtins:
                catalog.overrides[model_id] = model
                catalog.custom.pop(model_id, None)
            elif model_id in catalog.overrides:
                # Preserve an override whose built-in disappeared after an update.
                catalog.overrides[model_id] = model
            else:
                catalog.custom[model_id] = model
            self._atomic_write_catalog(catalog)

    def delete_user_model(self, model_id: str) -> None:
        with self._lock:
            catalog = self.user_catalog()
            if model_id in catalog.custom:
                del catalog.custom[model_id]
            elif model_id in catalog.overrides and model_id not in self.builtins():
                del catalog.overrides[model_id]
            else:
                raise KeyError(model_id)
            self._atomic_write_catalog(catalog)

    def reset_builtin(self, model_id: str) -> None:
        with self._lock:
            if model_id not in self.builtins():
                raise KeyError(model_id)
            catalog = self.user_catalog()
            if model_id not in catalog.overrides:
                raise ValueError("Built-in model has no user override")
            del catalog.overrides[model_id]
            self._atomic_write_catalog(catalog)

    def export_user_catalog(self) -> dict:
        return self.user_catalog().model_dump(mode="json")

    def import_user_catalog(self, payload: dict, replace: bool = False) -> None:
        incoming = UserCatalog.model_validate(payload)
        for model_id, model in {**incoming.custom, **incoming.overrides}.items():
            self.validate_id(model_id)
            self._validate_runtime_match(model_id, model)
        with self._lock:
            if replace:
                result = incoming
            else:
                result = self.user_catalog()
                result.custom.update(incoming.custom)
                result.overrides.update(incoming.overrides)
            builtins = self.builtins()
            collisions = set(result.custom) & set(builtins)
            if collisions:
                raise ValueError(f"Custom IDs collide with built-ins: {sorted(collisions)}")
            self._atomic_write_catalog(result)

    def _validate_models(self, raw: dict) -> dict[str, ModelDefinition]:
        if not isinstance(raw, dict):
            raise ValueError("Model catalog must be an object")
        models = {key: ModelDefinition.model_validate(value) for key, value in raw.items()}
        for model_id, model in models.items():
            self.validate_id(model_id)
            self._validate_runtime_match(model_id, model)
        return models

    def _validate_runtime_match(self, model_id: str, model: ModelDefinition) -> None:
        runtimes = self.runtimes()
        if model.runtime not in runtimes:
            raise ValueError(f"Model {model_id} references unknown runtime {model.runtime}")
        supports_gguf = runtimes[model.runtime].supports_gguf
        if bool(model.gguf_file) != supports_gguf:
            raise ValueError("GGUF filename and runtime type do not match")

    def _migrate_legacy_if_needed(self) -> None:
        if self.user_catalog_path.exists() or self.legacy_models_path is None:
            return
        if not self.legacy_models_path.exists():
            return
        builtins = self.builtins()
        legacy_raw = json.loads(self.legacy_models_path.read_text(encoding="utf-8"))
        legacy = self._validate_models(legacy_raw)
        catalog = UserCatalog()
        for model_id, model in legacy.items():
            if model_id not in builtins:
                catalog.custom[model_id] = model
            elif model != builtins[model_id]:
                catalog.overrides[model_id] = model
        self._atomic_write_catalog(catalog)
        migrated = self.legacy_models_path.with_suffix(self.legacy_models_path.suffix + ".migrated")
        if migrated.exists():
            migrated.unlink()
        os.replace(self.legacy_models_path, migrated)

    def _atomic_write_catalog(self, catalog: UserCatalog) -> None:
        self.user_catalog_path.parent.mkdir(parents=True, exist_ok=True)
        if self.user_catalog_path.exists():
            backup = self.user_catalog_path.with_suffix(self.user_catalog_path.suffix + ".bak")
            shutil.copy2(self.user_catalog_path, backup)
        temporary = self.user_catalog_path.with_suffix(self.user_catalog_path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(catalog.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, self.user_catalog_path)
