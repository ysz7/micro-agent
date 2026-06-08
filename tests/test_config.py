"""Config loader: reads settings.yaml + persona.md, applies provider defaults."""

from agent.config import load_config


def test_defaults_when_empty(tmp_path, monkeypatch):
    for var in ("PROVIDER", "MODEL", "API_KEY", "BASE_URL"):
        monkeypatch.delenv(var, raising=False)
    cfg = load_config(tmp_path)
    assert cfg.provider == "openai"
    assert cfg.model == "gpt-4o-mini"
    assert cfg.persona  # falls back to a built-in general persona
    assert (tmp_path / "workspace").is_dir()  # created on load


def test_reads_files(tmp_path, monkeypatch):
    monkeypatch.setenv("PROVIDER", "ollama")
    monkeypatch.setenv("MODEL", "llama3.1:8b")
    (tmp_path / "persona.md").write_text("You are a test bot.", encoding="utf-8")
    (tmp_path / "settings.yaml").write_text(
        "name: testbot\nfeeds: [a, b]\n", encoding="utf-8"
    )
    cfg = load_config(tmp_path)
    assert cfg.provider == "ollama"
    assert cfg.persona == "You are a test bot."
    assert cfg.settings["feeds"] == ["a", "b"]
    assert cfg.agent_name == "testbot"


def test_ollama_base_url_default(tmp_path, monkeypatch):
    monkeypatch.setenv("PROVIDER", "ollama")
    monkeypatch.delenv("BASE_URL", raising=False)
    cfg = load_config(tmp_path)
    assert cfg.base_url == "http://localhost:11434/v1"
