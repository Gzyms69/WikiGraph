from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_search():
    # Test valid search on PL (Warszawa was confirmed in FTS)
    response = client.get("/api/v1/search/pl?q=Warszawa")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # Check if ORP_Warszawa is there (it was the first match in CLI test)
    found = any(item['title'] == 'ORP_Warszawa' for item in data)
    assert found

    print("✅ Search 'Warszawa' on PL passed.")

if __name__ == "__main__":
    test_search()
