"""
Unit tests for the Config class.
"""
import pytest

from pythonweb_installer.config import Config


class TestConfig:
    """Tests for the Config class."""
    
    def test_init_default(self):
        """Test initialization with default values."""
        config = Config()
        assert config.get("mode") == "development"
        assert config.get("db_mode") == "auto"
        assert "template_repo" in config.config
        assert "install_path" in config.config
    
    def test_get_existing_key(self):
        """Test getting an existing configuration key."""
        config = Config()
        assert config.get("mode") == "development"
    
    def test_get_nonexistent_key(self):
        """Test getting a nonexistent key with default value."""
        config = Config()
        assert config.get("nonexistent_key") is None
        assert config.get("nonexistent_key", "default_value") == "default_value"
    
    def test_set_key(self):
        """Test setting a configuration key."""
        config = Config()
        config.set("new_key", "new_value")
        assert config.get("new_key") == "new_value"
        
        # Test overwriting an existing key
        config.set("mode", "production")
        assert config.get("mode") == "production"
