import os
import toml

def get_app_version():
    """Reads the application version from appversion.toml in the project root."""
    try:
        # Assuming this file is in project_root/utils/version_utils.py
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base_dir, 'appversion.toml')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = toml.load(f)
                return data.get("DotVis", {}).get("version", "Unknown")
    except Exception: 
        pass
    return "Unknown"
