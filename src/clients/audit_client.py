import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from src.config.settings import BASE_URL, DEFAULT_TIMEOUT
# Note: updated imports for models
from src.models.schemas import (
    IngestRequest, IngestResponse, JobStatusResponse,
    ProviderValidationRequest, ConnectionResponse, LogSearchResponse
)
from src.clients.errors import ApiError, NotFoundError
import uuid


class AuditVaultClient:
    def __init__(self, base_url: str = BASE_URL, session: requests.Session | None = None, retry: Retry | None = None):
        self.base_url = base_url
        # Allow injection of a preconfigured session for testability
        self.session = session or requests.Session()

        # Set default headers
        self.session.headers.update({"Content-Type": "application/json"})

        # --- Resilience Strategy (Scenario 2 Coverage) ---
        # If no retry provided, use default that retries 3 times
        if retry is None:
            retries = Retry(
                total=3,  # total retry attempts
                backoff_factor=0.5,  # backoff between retries (0.5s, 1s, 2s)
                status_forcelist=[500, 502, 503, 504],  # which status codes to retry on
                allowed_methods=["GET", "POST"]  # allow Retry for POST as well (unusual but required here)
            )
        else:
            retries = retry

        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Keep a lightweight retry policy for client-level retry loops (used when tests mock requests)
        self._client_retry_attempts = 3
        self._client_retry_statuses = {500, 502, 503, 504}

    def _handle_error(self, response: requests.Response):
        """Helper to raise descriptive structured errors"""
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            status = response.status_code
            body = response.text
            url = response.url
            if status == 404:
                raise NotFoundError(status, body, url, e)
            raise ApiError(status, body, url, e)

    def _idempotency_header(self, key: str | None = None) -> dict:
        if key is None:
            key = str(uuid.uuid4())
        return {"Idempotency-Key": key}

    def ingest_data(self, request_data: IngestRequest, idempotency_key: str | None = None) -> str:
        """Triggers data ingestion. Returns: job_id (str)

        Notes: We implement a small client-side retry loop for transient 5xx errors so tests that
        use requests-mock (which bypasses HTTPAdapter retry behavior) still exercise retry logic.
        """
        url = f"{self.base_url}/v1/ingest"
        headers = self._idempotency_header(idempotency_key)

        last_resp = None
        for attempt in range(1, self._client_retry_attempts + 1):
            resp = self.session.post(url, json=request_data.model_dump(), timeout=DEFAULT_TIMEOUT, headers=headers)
            last_resp = resp
            # If it's a transient 5xx and we have attempts left, try again
            if resp.status_code in self._client_retry_statuses and attempt < self._client_retry_attempts:
                continue

            # Either success or non-retryable error — handle and return/raise
            self._handle_error(resp)
            data = IngestResponse(**resp.json())
            return data.job_id

        # If we fall through, raise based on last response
        if last_resp is not None:
            self._handle_error(last_resp)
        raise ApiError(0, "No response received", url)

    def get_job_status(self, job_id: str) -> JobStatusResponse:
        """Fetch job execution status"""
        url = f"{self.base_url}/v1/jobs/{job_id}"
        resp = self.session.get(url, timeout=DEFAULT_TIMEOUT)
        self._handle_error(resp)
        return JobStatusResponse(**resp.json())

    def get_raw_log(self, log_id: str) -> requests.Response:
        """Returns the raw response stream"""
        url = f"{self.base_url}/v1/logs/{log_id}/raw"
        resp = self.session.get(url, stream=True, timeout=DEFAULT_TIMEOUT)
        self._handle_error(resp)
        return resp

    # --- New Methods for Full API Coverage ---

    def validate_provider(self, provider_type: str, api_key: str) -> ConnectionResponse:
        """Endpoint 5: Provider Connection Test"""
        url = f"{self.base_url}/v1/providers/validate"
        payload = ProviderValidationRequest(provider_type=provider_type, api_key=api_key)
        resp = self.session.post(url, json=payload.model_dump(), timeout=DEFAULT_TIMEOUT)
        self._handle_error(resp)
        return ConnectionResponse(**resp.json())

    def search_logs(self, limit: int = 50) -> LogSearchResponse:
        """Endpoint 3: Audit Metadata Search"""
        url = f"{self.base_url}/v1/logs"
        resp = self.session.get(url, params={"limit": limit}, timeout=DEFAULT_TIMEOUT)
        self._handle_error(resp)
        return LogSearchResponse(**resp.json())