import json

from app.services.backup_status import read_backup_status


def test_a_missing_status_file_reads_as_none(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("BACKUP_STATUS_FILE", str(tmp_path / "missing.json"))
    from app.config import get_settings

    get_settings.cache_clear()

    assert read_backup_status() is None

    get_settings.cache_clear()


def test_a_written_status_file_is_returned(tmp_path, monkeypatch) -> None:
    path = tmp_path / "status.json"
    path.write_text(json.dumps({"at": "2026-11-18T03:00:00Z", "ok": True}), encoding="utf-8")
    monkeypatch.setenv("BACKUP_STATUS_FILE", str(path))
    from app.config import get_settings

    get_settings.cache_clear()

    status = read_backup_status()

    assert status is not None
    assert status["ok"] is True
    assert status["at"] == "2026-11-18T03:00:00Z"

    get_settings.cache_clear()


def test_a_corrupt_status_file_reads_as_none_rather_than_raising(tmp_path, monkeypatch) -> None:
    path = tmp_path / "status.json"
    path.write_text("{not json", encoding="utf-8")
    monkeypatch.setenv("BACKUP_STATUS_FILE", str(path))
    from app.config import get_settings

    get_settings.cache_clear()

    assert read_backup_status() is None

    get_settings.cache_clear()
