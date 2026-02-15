from src.config.settings import BASE_URL
from src.models.schemas import IngestRequest, DateRange


def test_ingest_idempotency(client, mock_api):
    job_id = "job_idempotent_1"
    idempotency_key = "fixed-key-123"

    # Mock behavior: if same idempotency key is used, server returns same job_id
    # requests-mock can inspect headers on incoming requests; we'll respond with job_id
    # for any POST to /v1/ingest (but test will ensure client sent the header both times)
    mock_api.post(f"{BASE_URL}/v1/ingest", json={"job_id": job_id, "status": "queued", "estimated_completion_ms": 100}, status_code=202)

    request_body = IngestRequest(
        provider_id="aws_mock_provider",
        range=DateRange(start="2024-01-01T00:00:00Z", end="2024-01-02T00:00:00Z")
    )

    # First call with explicit idempotency key
    first = client.ingest_data(request_body, idempotency_key=idempotency_key)
    assert first == job_id

    # Second call with same idempotency key
    second = client.ingest_data(request_body, idempotency_key=idempotency_key)
    assert second == job_id

    # Verify that requests were made and that the Idempotency-Key header was sent both times
    history = mock_api.request_history
    ingest_calls = [r for r in history if r.method == 'POST' and r.path == f"/v1/ingest"]
    assert len(ingest_calls) == 2
    for call in ingest_calls:
        assert call.headers.get('Idempotency-Key') == idempotency_key
