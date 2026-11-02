import os
import sys
from pathlib import Path
from functools import lru_cache

BACKEND_ROOT = Path(__file__).resolve().parent.parent  # backend/
MODEL_ROOT = BACKEND_ROOT / "src" / "model"

if str(MODEL_ROOT) not in sys.path:
    sys.path.insert(0, str(MODEL_ROOT))


def _env(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name, default)


STORAGE_ACCOUNT_URL = _env("STORAGE_ACCOUNT_URL")

_AZURITE_CONNECTION_STRING = (
    "DefaultEndpointsProtocol=http;"
    "AccountName=devstoreaccount1;"
    "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
    "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
    "QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;"
    "TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;"
)
STORAGE_CONNECTION_STRING = _env("STORAGE_CONNECTION_STRING") or (
    None if STORAGE_ACCOUNT_URL else _AZURITE_CONNECTION_STRING
)

COSMOS_ENDPOINT = _env("COSMOS_ENDPOINT") or "https://localhost:8081"

_EMULATOR_KEY = "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="

COSMOS_KEY = _env("COSMOS_KEY") or (
    _EMULATOR_KEY if COSMOS_ENDPOINT == "https://localhost:8081" else None
)

COSMOS_DATABASE = _env("COSMOS_DATABASE", "asset-risk-engine")
COSMOS_EIOPA_DATABASE = _env("COSMOS_EIOPA_DATABASE", "eiopa-data")
ALLOWED_ORIGINS = [
    o.strip() for o in _env("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
]


@lru_cache(maxsize=1)
def get_model_settings():
    """Singleton for the model's `Settings` class (reads the two reference .xlsx files)."""
    import model.settings as model_settings_module

    return model_settings_module.Settings()
