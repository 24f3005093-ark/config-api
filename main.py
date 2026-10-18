from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS: lets the grader's web page call your API from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- The four config layers (weakest to strongest) ----
DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

YAML_LAYER = {  # config.development.yaml
    "port": 8499,
    "debug": False,
    "log_level": "warning",
    "api_key": "key-jyonaw118j",
}

DOTENV_LAYER = {  # .env file
    "APP_DEBUG": "true",
}

OS_ENV_LAYER = {  # OS env vars
    "APP_WORKERS": "3",
    "APP_DEBUG": "false",
}

ALIASES = {"num_workers": "workers"}


def normalize_key(key: str) -> str:
    """APP_WORKERS -> workers, NUM_WORKERS -> workers"""
    k = key.strip().lower()
    if k.startswith("app_"):
        k = k[4:]
    return ALIASES.get(k, k)


def to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "on"}


def coerce(key: str, value):
    if key in ("port", "workers"):
        return int(value)
    if key == "debug":
        return to_bool(value)
    return str(value)


@app.get("/effective-config")
def effective_config(overrides: list[str] = Query(default=[], alias="set")):
    merged = {}

    # Apply layers in order; later ones overwrite earlier ones
    for layer in (DEFAULTS, YAML_LAYER, DOTENV_LAYER, OS_ENV_LAYER):
        for key, value in layer.items():
            merged[normalize_key(key)] = value

    # CLI overrides: ?set=port=9000&set=debug=true
    for item in overrides:
        if "=" in item:
            key, value = item.split("=", 1)  # split on FIRST "=" only
            merged[normalize_key(key)] = value

    # Convert types
    result = {k: coerce(k, v) for k, v in merged.items()}

    # Hide the secret
    result["api_key"] = "****"
    return result