import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_search_endpoint_not_implemented():
    # Should be 404 until implemented
    response = client.get("/api/v1/search/en?q=test")
    assert response.status_code == 404

def test_compare_endpoint_not_implemented():
    # Should be 404 until implemented
    response = client.get("/api/v1/compare/Q42")
    assert response.status_code == 404

def test_rag_context_endpoint_not_implemented():
    # Should be 404 until implemented
    response = client.post("/api/v1/rag/context", json={"query": "test", "lang": "en"})
    assert response.status_code == 404
