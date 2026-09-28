from __future__ import annotations

import json
import os
import re
from pathlib import Path

from pydantic import BaseModel, field_validator


class ControllerState(BaseModel):
    pod_id: str = ""
    model_id: str = ""
    runtime_id: str = ""
    profile_revision: str = ""
    gpu_type_id: str = ""
    datacenter_id: str = ""
    volume_gb: int = 0

    @field_validator("pod_id")
    @classmethod
    def validate_pod_id(cls, value: str) -> str:
        if value and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,127}", value):
            raise ValueError("Invalid RunPod pod ID in controller state")
        return value


class StateStore:
    def __init__(self, path: Path, initial_pod_id: str = "") -> None:
        self.path = path
        self.initial_pod_id = initial_pod_id

    def read(self) -> ControllerState:
        if not self.path.exists():
            return ControllerState(pod_id=self.initial_pod_id)
        return ControllerState.model_validate_json(self.path.read_text(encoding="utf-8"))

    def write(self, state: ControllerState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(state.model_dump_json(indent=2), encoding="utf-8")
        os.replace(temporary, self.path)
