from src.config.settings import BASE_URL
from src.models.schemas import IngestRequest, DateRange


def test_infrastructure_brownout(client, poller, mock_api):
    job_id = "job_retry_1"

    # Mocking a failure (503) then success (202)
    mock_api.post(f"{BASE_URL}/v1/ingest", [
        {"json": {"error": "Busy"}, "status_code": 503},
        {"json": {"job_id": job_id, "status": "queued", "estimated_completion_ms": 100}, "status_code": 202}
    ])

    request_body = IngestRequest(
        provider_id="aws_mock_provider",
        range=DateRange(start="2024-01-01T00:00:00Z", end="2024-01-02T00:00:00Z")
    )

    # If retry works, this should return the job_id despite the initial 503
    actual = client.ingest_data(request_body)
    assert actual == job_id
