"""Basic test suite for configuration and session managers."""

from pathlib import Path
from src.core.session import SessionManager
from src.utils.helpers import load_yaml_config

def test_session_manager_initialization():
    session_mgr = SessionManager()
    assert session_mgr.session_file is not None
    assert isinstance(session_mgr.session_file, Path)

def test_load_yaml_config():
    config_path = Path(__file__).resolve().parent.parent / "config" / "settings.example.yaml"
    config = load_yaml_config(config_path)
    assert isinstance(config, dict)
    assert "campaigns" in config
    assert len(config["campaigns"]) > 0
