# Pytest fixtures (Client setup, Data prep)
import pytest
import requests_mock

from src.clients.audit_client import AuditVaultClient
from src.utils.poller import JobPoller

@pytest.fixture
def mock_api():
    """
    This will provide a fake API environment for testing,
    allowing us to mock responses from the Audit Vault API.
    """
    with requests_mock.Mocker() as m:
        yield m

@pytest.fixture
def client():
    """
    Create an instance of the AuditVaultClient that will be used in tests.
    This client will be configured to point to the mock API.
    """
    return AuditVaultClient()

@pytest.fixture
def poller(client):
    """
    Create an instance of the JobPoller,
    which will be used to wait for job completion in tests.
     It uses the client fixture to interact with the API.
    """
    return JobPoller(client)