from unittest.mock import patch
import importlib

import pytest
from fastapi.testclient import TestClient


class DummyTemplate:
    def render(self, **context):
        name = context["name"]
        tech_stack = context.get("tech_stack", [])
        return f"pipeline for {name} with {', '.join(tech_stack)}"


@pytest.fixture
def client():
    with patch("jinja2.Environment.get_template", return_value=DummyTemplate()):
        import main
        importlib.reload(main)
        with TestClient(main.app) as client:
            yield client
        main.pipelines.clear()


def test_generate_pipeline(client):
    response = client.post(
        "/generate",
        json={"name": "Example", "requirements": "Uses Docker"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "pipeline_id" in data
    assert data["jenkinsfile"] == "pipeline for Example with docker"


def test_list_pipelines(client):
    create = client.post(
        "/generate",
        json={"name": "Example", "requirements": "Uses Docker"},
    )
    pipeline_id = create.json()["pipeline_id"]
    list_response = client.get("/list")
    assert list_response.status_code == 200
    pipelines = list_response.json()
    assert any(p["id"] == pipeline_id and p["name"] == "Example" for p in pipelines)


def test_export_pipeline(client):
    create = client.post(
        "/generate",
        json={"name": "Example", "requirements": "Uses Docker"},
    )
    pipeline_id = create.json()["pipeline_id"]
    export_response = client.get(f"/export/{pipeline_id}")
    assert export_response.status_code == 200
    assert export_response.text == "pipeline for Example with docker"
    assert (
        export_response.headers["Content-Disposition"]
        == "attachment; filename=Example.jenkinsfile"
    )
