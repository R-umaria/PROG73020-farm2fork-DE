from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    with patch("app.services.delivery_actions_service.SessionLocal") as mock_sl:
        mock_sl.return_value = MagicMock()

        from app.main import app
        return TestClient(app)


@pytest.fixture
def mock_actions_service():
    #  fake service for tests
    with patch("app.api.routes.delivery_actions.service") as mock_svc:
        yield mock_svc


# POST /api/deliveries/{id}/start

class TestStartDeliveryRoute:

    def test_start_delivery_returns_200(self, client, mock_actions_service):
        # GIVEN: the service returns a valid execution object
        fake_exec = MagicMock()
        fake_exec.id = uuid4()
        fake_exec.current_status = "Out for Delivery"
        mock_actions_service.start_delivery.return_value = fake_exec

        # WHEN: we POST to the start endpoint
        response = client.post(f"/api/deliveries/{fake_exec.id}/start")

        # THEN: we should get a 200 back
        assert response.status_code == 200

    def test_start_delivery_returns_status_in_body(self, client, mock_actions_service):
        # GIVEN: the service returns an execution with status "Out for Delivery"
        fake_exec = MagicMock()
        fake_exec.id = uuid4()
        fake_exec.current_status = "Out for Delivery"
        mock_actions_service.start_delivery.return_value = fake_exec

        # WHEN: we POST to the start endpoint
        response = client.post(f"/api/deliveries/{fake_exec.id}/start")

        # THEN: the response body should include the status
        assert response.json()["status"] == "Out for Delivery"

    def test_start_delivery_returns_404_when_not_found(self, client, mock_actions_service):
        # GIVEN: the service returns None (execution ID doesn't exist in the DB)
        mock_actions_service.start_delivery.return_value = None

        # WHEN: we POST with a random ID
        response = client.post(f"/api/deliveries/{uuid4()}/start")

        # THEN: we should get a 404
        assert response.status_code == 404


# POST /api/deliveries/{id}/complete

class TestCompleteDeliveryRoute:

    def test_complete_delivery_returns_200(self, client, mock_actions_service):
        # GIVEN: the service returns a object
        fake_conf = MagicMock()
        fake_conf.received_by = "testuser"
        mock_actions_service.complete_delivery.return_value = fake_conf

        # WHEN: we POST with a received_by value
        response = client.post(
            f"/api/deliveries/{uuid4()}/complete",
            json={"received_by": "testuser"},
        )

        # THEN: should be 200
        assert response.status_code == 200

    def test_complete_delivery_without_received_by_returns_422(self, client, mock_actions_service):
        # GIVEN: we forget to include received_by in the request body
        # WHEN: we POST without required fields
        response = client.post(
            f"/api/deliveries/{uuid4()}/complete",
            json={},  # missing received_by
        )

        # THEN: FastAPI should reject it with a 422 Unprocessable Entity
        assert response.status_code == 422


# POST /api/deliveries/{id}/fail

class TestFailDeliveryRoute:

    def test_fail_delivery_returns_200(self, client, mock_actions_service):
        # GIVEN: the service logs the exception successfully
        fake_exc = MagicMock()
        fake_exc.exception_type = "NO_ACCESS"
        fake_exc.retry_allowed = False
        mock_actions_service.fail_delivery.return_value = fake_exc

        # WHEN: we POST with the required failure info
        response = client.post(
            f"/api/deliveries/{uuid4()}/fail",
            json={"exception_type": "NO_ACCESS", "description": "Gate locked"},
        )

        # THEN: should be 200
        assert response.status_code == 200

    def test_fail_delivery_response_includes_exception_type(self, client, mock_actions_service):
        # GIVEN: a failure with exception type "DAMAGED"
        fake_exc = MagicMock()
        fake_exc.exception_type = "DAMAGED"
        fake_exc.retry_allowed = True
        mock_actions_service.fail_delivery.return_value = fake_exc

        # WHEN: we fail the delivery
        response = client.post(
            f"/api/deliveries/{uuid4()}/fail",
            json={"exception_type": "DAMAGED", "description": "Box crushed", "retry_allowed": True},
        )

        # THEN: the response should tell us the exception type and retry status
        body = response.json()
        assert body["exception_type"] == "DAMAGED"
        assert body["retry_allowed"] is True