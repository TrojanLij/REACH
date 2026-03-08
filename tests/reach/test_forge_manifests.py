from __future__ import annotations

from pathlib import Path

from reach.forge.manifests import discover_manifests, load_manifest, validate_manifest_package


def test_load_manifest_with_defaults(tmp_path: Path) -> None:
    item_dir = tmp_path / "local_storage_replay"
    item_dir.mkdir(parents=True)
    manifest_file = item_dir / "manifest.yaml"
    manifest_file.write_text(
        "\n".join(
            [
                "id: web.local_storage_replay",
                "type: exploit",
                "name: Local Storage Replay",
                "version: 0.1.0",
                "forge_api_version: '1'",
                "entry: src/entry.py",
                "entrypoint: run",
                "category: web",
            ]
        ),
        encoding="utf-8",
    )

    manifest = load_manifest(manifest_file)
    assert manifest.item_id == "web.local_storage_replay"
    assert manifest.item_type == "exploit"
    assert manifest.kind == "web_local_storage_replay"
    assert manifest.entrypoint == "run"
    assert manifest.requires_python == []
    assert manifest.requires_system == []
    assert manifest.required_env == []
    assert manifest.optional_env == []


def test_load_manifest_list_fields(tmp_path: Path) -> None:
    item_dir = tmp_path / "xss_gh0st"
    item_dir.mkdir(parents=True)
    manifest_file = item_dir / "manifest.yaml"
    manifest_file.write_text(
        "\n".join(
            [
                "id: xss.gh0st",
                "type: generator",
                "name: Gh0st XSS",
                "version: 0.1.0",
                "forge_api_version: '1'",
                "entry: src/entry.py",
                "kind: xss_gh0st",
                "entrypoint: generate",
                "requires_python:",
                "  - pyfiglet>=0.8",
                "requires_system: [nodejs, chromium]",
                "required_env: [REACH_CALLBACK_URL]",
                "optional_env: [REACH_TIMEOUT, REACH_TAGS]",
            ]
        ),
        encoding="utf-8",
    )

    manifest = load_manifest(manifest_file)
    assert manifest.kind == "xss_gh0st"
    assert manifest.entrypoint == "generate"
    assert manifest.requires_python == ["pyfiglet>=0.8"]
    assert manifest.requires_system == ["nodejs", "chromium"]
    assert manifest.required_env == ["REACH_CALLBACK_URL"]
    assert manifest.optional_env == ["REACH_TIMEOUT", "REACH_TAGS"]


def test_discover_manifests_from_reach_forge_paths(tmp_path: Path, monkeypatch) -> None:
    base = tmp_path / "external"
    item_dir = base / "forge" / "exploits" / "web" / "local_storage_replay"
    item_dir.mkdir(parents=True)
    (item_dir / "manifest.yaml").write_text(
        "\n".join(
            [
                "id: web.local_storage_replay",
                "type: exploit",
                "name: Local Storage Replay",
                "version: 0.1.0",
                "forge_api_version: '1'",
                "entry: src/entry.py",
                "entrypoint: run",
                "category: web",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("REACH_FORGE_PATHS", str(base))
    manifests = discover_manifests(item_type="exploit")
    ids = {manifest.item_id for manifest in manifests}
    assert "web.local_storage_replay" in ids


def test_validate_manifest_package_with_entrypoint(tmp_path: Path) -> None:
    item_dir = tmp_path / "xss_gh0st"
    src_dir = item_dir / "src"
    src_dir.mkdir(parents=True)
    manifest_file = item_dir / "manifest.yaml"
    manifest_file.write_text(
        "\n".join(
            [
                "id: xss.gh0st",
                "type: generator",
                "name: Gh0st XSS",
                "version: 0.1.0",
                "forge_api_version: '1'",
                "entry: src/entry.py",
                "kind: xss_gh0st",
                "entrypoint: generate",
                "required_env: [REACH_FOO]",
                "optional_env: [REACH_BAR]",
            ]
        ),
        encoding="utf-8",
    )
    (src_dir / "entry.py").write_text(
        "def generate(**kwargs):\n    return 'ok'\n",
        encoding="utf-8",
    )

    manifest = load_manifest(manifest_file)
    assert validate_manifest_package(manifest) == []


def test_manifest_rejects_overlapping_env(tmp_path: Path) -> None:
    item_dir = tmp_path / "bad_item"
    item_dir.mkdir(parents=True)
    manifest_file = item_dir / "manifest.yaml"
    manifest_file.write_text(
        "\n".join(
            [
                "id: bad.item",
                "type: generator",
                "name: Bad Item",
                "version: 0.1.0",
                "forge_api_version: '1'",
                "entry: src/entry.py",
                "entrypoint: generate",
                "required_env: [REACH_NAME]",
                "optional_env: [REACH_NAME]",
            ]
        ),
        encoding="utf-8",
    )

    try:
        load_manifest(manifest_file)
    except ValueError as exc:
        assert "both required_env and optional_env" in str(exc)
    else:
        raise AssertionError("expected load_manifest to fail for overlapping env")


def test_manifest_requires_contract_keys(tmp_path: Path) -> None:
    item_dir = tmp_path / "missing_keys"
    item_dir.mkdir(parents=True)
    manifest_file = item_dir / "manifest.yaml"
    manifest_file.write_text(
        "\n".join(
            [
                "id: test.item",
                "type: exploit",
                "entry: src/entry.py",
                "entrypoint: run",
            ]
        ),
        encoding="utf-8",
    )

    try:
        load_manifest(manifest_file)
    except ValueError as exc:
        assert "missing required key 'name'" in str(exc)
    else:
        raise AssertionError("expected load_manifest to fail for missing required keys")
