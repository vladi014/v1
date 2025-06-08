import yaml

def load_config(path):
    """Carga la configuración desde un archivo YAML."""
    with open(path, 'r') as f:
        return yaml.safe_load(f)
