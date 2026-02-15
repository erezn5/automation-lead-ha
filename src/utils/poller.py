from tenacity import retry, stop_after_delay, wait_fixed, retry_if_result
from src.clients.audit_client import AuditVaultClient
from src.models.schemas import JobStatusResponse

# Continue retrying while the job status is pending or processing
def is_job_not_completed(job_status: JobStatusResponse) -> bool:
    return job_status.state in ["pending", "processing"]


class JobPoller:
    def __init__(self, client: AuditVaultClient):
        self.client = client

    @retry(
        stop=stop_after_delay(30),
        wait=wait_fixed(1),
        retry=retry_if_result(is_job_not_completed),
        reraise=True
    )
    def wait_for_job_completion(self, job_id: str) -> JobStatusResponse:
        """
        Polls the job status API until the job is completed or failed.
        """
        print(f"Polling status for job {job_id}...")  # for debugging purposes
        return self.client.get_job_status(job_id)