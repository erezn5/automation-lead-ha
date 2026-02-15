import os

BASE_URL = os.getenv("AUDIT_VAULT_URL", "http://localhost:8080")
DEFAULT_TIMEOUT = 10