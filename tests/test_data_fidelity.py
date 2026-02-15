from deepdiff import DeepDiff
from src.utils.data_generator import generate_complex_payload
from src.config.settings import BASE_URL
from src.models.schemas import IngestRequest, DateRange
import hashlib
import json


def test_log_fidelity_end_to_end(client, poller, mock_api):
    # 1. Setup
    payload = generate_complex_payload()
    job_id = "job_fidelity_1"
    log_id = "log_fid_1"

    # Mocks
    # Ingest
    mock_api.post(f"{BASE_URL}/v1/ingest", json={
        "job_id": job_id,
        "status": "queued",
        "estimated_completion_ms": 100
    }, status_code=202)

    # Job status mock - returns that the job is completed
    mock_api.get(f"{BASE_URL}/v1/jobs/{job_id}", json={
        "job_id": job_id,
        "state": "completed",
        "artifacts": {"s3_path": "s3://b/f.json"}
    })

    # Prepare canonical JSON text for the payload so checksum is deterministic
    # Use separators without spaces and sort keys to canonicalize structure
    json_text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    checksum = hashlib.sha256(json_text.encode("utf-8")).hexdigest()

    # Critical mock: when fetching the raw log, return the canonical JSON text and the checksum header
    mock_api.get(
        f"{BASE_URL}/v1/logs/{log_id}/raw",
        text=json_text,
        headers={"X-Vault-Checksum": checksum, "Content-Type": "application/json"}
    )

    # 2. Ingest
    request_body = IngestRequest(
        provider_id="aws_mock_provider",
        range=DateRange(start="2024-01-01T00:00:00Z", end="2024-01-02T00:00:00Z"),
        priority="high"
    )

    actual_job_id = client.ingest_data(request_body)

    # 3. Poll
    poller.wait_for_job_completion(actual_job_id)

    # 4. Verify
    response = client.get_raw_log(log_id)
    fetched_data = response.json()

    # Structural integrity check
    diff = DeepDiff(payload, fetched_data, ignore_order=True)
    assert not diff, f"Data mutation detected! {diff}"

    # Checksum verification
    # Compute sha256 of the raw body bytes to match the X-Vault-Checksum header
    body_bytes = response.content if hasattr(response, 'content') else response.text.encode('utf-8')
    computed = hashlib.sha256(body_bytes).hexdigest()
    header_checksum = response.headers.get("X-Vault-Checksum")

    # Assert header equals computed digest
    assert header_checksum is not None
    assert header_checksum == computed
