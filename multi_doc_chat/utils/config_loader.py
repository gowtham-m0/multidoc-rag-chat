from pathlib import Path
import os
import yaml

def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]

def load_config(config_path: str | None = None)-> dict:
    """
    Resolve config path reliably irrespective of CWD.
    Priority: explicity arg > CONFIG_PATH env > <project_root>/config.config.yaml
    """
    
    env_path = os.getenv("CONFIG_PATH")
    if config_path is None:
        config_path = env_path or str(_project_root()  / "config" / "config.yml")
        
    path = Path(config_path)
    if not path.is_absolute():
        path = _project_root() / path
        
    if not path.exists():
        raise FileNotFoundError(f"Config file not found at: {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    
    return config

load_config()