"""
Configuration management for PythonWeb Installer.
"""

class Config:
    """Configuration manager for the installer."""
    
    def __init__(self, config_file=None):
        """Initialize configuration."""
        self.config = {
            # Default configuration values
            "mode": "development",
            "db_mode": "auto",
            "template_repo": "https://github.com/yourusername/PythonWeb.git",
            "install_path": "C:/Projects/templates/PythonWeb",
        }
        
    def get(self, key, default=None):
        """Get a configuration value."""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set a configuration value."""
        self.config[key] = value

