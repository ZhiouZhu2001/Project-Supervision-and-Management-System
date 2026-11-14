import pytest

from app import main as main_module


def test_production_refuses_to_boot_with_the_development_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_SECRET_KEY", "dev-only-not-a-secret")
    main_module.get_settings.cache_clear()

    try:
        with pytest.raises(RuntimeError, match="APP_SECRET_KEY"):
            main_module.create_app()
    finally:
        monkeypatch.undo()
        main_module.get_settings.cache_clear()
