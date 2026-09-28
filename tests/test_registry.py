import json
from pathlib import Path

import pytest

from gpuharbor.registry import ModelDefinition, Registry


RUNTIMES = {
    "vllm": {
        "label": "vLLM",
        "image_env": "RUNTIME_IMAGE_VLLM",
        "backend": "vllm",
        "supports_gguf": False,
    },
    "llama-cpp": {
        "label": "llama",
        "image_env": "RUNTIME_IMAGE_LLAMA_CPP",
        "backend": "llama",
        "supports_gguf": True,
    },
}


def model(**overrides):
    values = {
        "name": "Example",
        "model_id": "org/model",
        "runtime": "vllm",
        "served_names": ["chat"],
        "gpu_type_ids": ["NVIDIA A40"],
    }
    values.update(overrides)
    return ModelDefinition(**values)


def registry(tmp_path: Path, builtins=None, legacy=None) -> Registry:
    builtins_path = tmp_path / "bundled.json"
    runtimes_path = tmp_path / "runtimes.json"
    user_path = tmp_path / "user-models.json"
    legacy_path = tmp_path / "models.json"
    builtins_path.write_text(
        json.dumps({key: value.model_dump(mode="json") for key, value in (builtins or {}).items()})
    )
    runtimes_path.write_text(json.dumps(RUNTIMES))
    if legacy is not None:
        legacy_path.write_text(
            json.dumps({key: value.model_dump(mode="json") for key, value in legacy.items()})
        )
    return Registry(builtins_path, runtimes_path, user_path, legacy_path)


def test_custom_model_round_trip_and_unicode(tmp_path):
    store = registry(tmp_path)
    store.save_model("mein-modell", model(name="Größeres Modell"))
    record = store.records()["mein-modell"]
    assert record.model.name == "Größeres Modell"
    assert record.source == "custom"
    assert "Größeres" in store.user_catalog_path.read_text()


def test_builtin_update_does_not_overwrite_custom_or_override(tmp_path):
    original = model(name="Built-in v1")
    store = registry(tmp_path, {"default-model": original})
    store.save_model("default-model", original.model_copy(update={"context_length": 65536}))
    store.save_model("own-model", model(name="Own"))

    updated = original.model_copy(update={"name": "Built-in v2", "context_length": 131072})
    new_builtin = model(name="New built-in", model_id="org/new")
    store.bundled_models_path.write_text(
        json.dumps(
            {
                "default-model": updated.model_dump(mode="json"),
                "new-model": new_builtin.model_dump(mode="json"),
            }
        )
    )

    records = store.records()
    assert records["default-model"].model.context_length == 65536
    assert records["default-model"].source == "override"
    assert records["own-model"].model.name == "Own"
    assert records["new-model"].source == "builtin"


def test_builtin_override_can_be_reset(tmp_path):
    original = model(name="Built-in")
    store = registry(tmp_path, {"default-model": original})
    store.save_model("default-model", original.model_copy(update={"context_length": 65536}))
    store.reset_builtin("default-model")
    record = store.records()["default-model"]
    assert record.source == "builtin"
    assert record.model.context_length == original.context_length


def test_removed_builtin_override_is_preserved(tmp_path):
    original = model(name="Built-in")
    store = registry(tmp_path, {"default-model": original})
    store.save_model("default-model", original.model_copy(update={"context_length": 65536}))
    store.bundled_models_path.write_text("{}")
    record = store.records()["default-model"]
    assert record.source == "orphaned-override"
    assert record.model.context_length == 65536


def test_legacy_catalog_migrates_without_losing_changes(tmp_path):
    original = model(name="Built-in")
    changed = original.model_copy(update={"context_length": 65536})
    own = model(name="Own", model_id="org/own")
    store = registry(
        tmp_path,
        {"default-model": original},
        {"default-model": changed, "own-model": own},
    )
    assert store.records()["default-model"].source == "override"
    assert store.records()["own-model"].source == "custom"
    assert (tmp_path / "models.json.migrated").exists()


def test_user_catalog_writes_backup_and_exports(tmp_path):
    store = registry(tmp_path)
    store.save_model("first-model", model(name="First"))
    store.save_model("second-model", model(name="Second", model_id="org/second"))
    assert store.user_catalog_path.with_suffix(".json.bak").exists()
    exported = store.export_user_catalog()
    assert exported["schema_version"] == 1
    assert set(exported["custom"]) == {"first-model", "second-model"}


def test_import_merges_without_overwriting_unmentioned_models(tmp_path):
    store = registry(tmp_path)
    store.save_model("first-model", model(name="First"))
    incoming = {
        "schema_version": 1,
        "custom": {"second-model": model(name="Second", model_id="org/second").model_dump(mode="json")},
        "overrides": {},
    }
    store.import_user_catalog(incoming)
    assert set(store.models()) == {"first-model", "second-model"}


def test_future_schema_is_rejected_without_modification(tmp_path):
    store = registry(tmp_path)
    before = store.user_catalog_path.read_text()
    store.user_catalog_path.write_text('{"schema_version": 99, "custom": {}, "overrides": {}}')
    with pytest.raises(ValueError, match="prevent data loss"):
        store.user_catalog()
    assert '"schema_version": 99' in store.user_catalog_path.read_text()
    assert before != store.user_catalog_path.read_text()


def test_rejects_unsafe_id(tmp_path):
    with pytest.raises(ValueError, match="ID must"):
        registry(tmp_path).save_model("../escape", model())


def test_gguf_requires_matching_runtime(tmp_path):
    store = registry(tmp_path)
    with pytest.raises(ValueError, match="do not match"):
        store.save_model("bad-model", model(gguf_file="model.gguf"))


def test_gguf_filename_cannot_escape(tmp_path):
    with pytest.raises(ValueError, match="plain filename"):
        model(runtime="llama-cpp", gguf_file="../model.gguf")


def test_context_limits_are_validated():
    with pytest.raises(ValueError):
        model(context_length=999999)


def test_repository_and_served_names_reject_argument_injection():
    with pytest.raises(ValueError, match="owner/repository"):
        model(model_id="--host")
    with pytest.raises(ValueError, match="API-safe"):
        model(served_names=["--host"])


def test_non_vllm_profile_rejects_vllm_flags():
    with pytest.raises(ValueError, match="only be used with"):
        model(runtime="llama-cpp", gguf_file="model.gguf", trust_remote_code=True)
