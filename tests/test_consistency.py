import pytest
from src.config.settings import BASE_URL
from src.clients.errors import NotFoundError


def test_consistency_orphaned_log_file(client, mock_api):
    """
    SCENARIO 3: Data Inconsistency (Creative Challenge)
    """
    # 1. Setup
    log_id = "log_orphaned_999"

    # (Metadata exists)
    mock_api.get(f"{BASE_URL}/v1/logs", json={
        "data": [{"id": log_id, "checksum": "sha256:...", "timestamp": "2024-01-01"}],
        "meta": {"total_count": 1}
    })

    error_message = "Integrity Error: Metadata exists but S3 object is missing."
    mock_api.get(f"{BASE_URL}/v1/logs/{log_id}/raw", status_code=404, json={"error": error_message})

    # 2. Execution & Validation
    print(f"\n🧪 Testing consistency for log ID: {log_id}")

    with pytest.raises(NotFoundError) as exc_info:
        client.get_raw_log(log_id)

    # 3. Analyze the Error
    err = exc_info.value
    print(f"✅ Caught expected NotFoundError: status={err.status_code} body={err.body}")

    assert err.status_code == 404
    assert error_message in err.body
