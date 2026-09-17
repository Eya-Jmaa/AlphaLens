"""Main Application Tests"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "AlphaLens"


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert data["project"] == "AlphaLens"


def test_company_info():
    """Test company info endpoint"""
    response = client.get("/api/v1/companies/AAPL")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "AAPL"