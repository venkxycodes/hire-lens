import pytest
from django.test import Client


@pytest.fixture
def client() -> Client:
    return Client()


def test_rest_health(client: Client) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_rest_echo(client: Client) -> None:
    response = client.post(
        "/api/v1/echo",
        data={"message": "hello"},
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json() == {"message": "hello"}


def test_graphql_health_query(client: Client) -> None:
    response = client.post(
        "/graphql/",
        data={"query": "{ health version }"},
        content_type="application/json",
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["health"] == "ok"
    assert payload["data"]["version"] == "0.1.0"


def test_graphql_echo_mutation(client: Client) -> None:
    response = client.post(
        "/graphql/",
        data={
            "query": 'mutation { echo(message: "hello") { message } }',
        },
        content_type="application/json",
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["echo"]["message"] == "hello"
