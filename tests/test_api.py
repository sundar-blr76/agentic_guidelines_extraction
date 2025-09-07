import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
import os

# Add the project root to the Python path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from guidelines_agent.mcp_server.main import app

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_query_agent_success(client: AsyncClient):
    response = await client.post("/agent/query", json={"input": "test query"})
    assert response.status_code == 200
    assert "output" in response.json()

@pytest.mark.asyncio
async def test_query_agent_invalid(client: AsyncClient):
    response = await client.post("/agent/query", json={"invalid_key": "test query"})
    assert response.status_code == 422  # Unprocessable Entity

@pytest.mark.asyncio
async def test_ingest_agent_success(client: AsyncClient):
    # Create a dummy PDF file
    with open("dummy.pdf", "wb") as f:
        f.write(b"%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 3 3]>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000053 00000 n\n0000000102 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n123\n%%EOF")
    
    with open("dummy.pdf", "rb") as f:
        response = await client.post("/agent/ingest", files={"file": ("dummy.pdf", f, "application/pdf")})
    
    os.remove("dummy.pdf")
    
    assert response.status_code == 200
    assert "output" in response.json()

@pytest.mark.asyncio
async def test_ingest_agent_invalid_file_type(client: AsyncClient):
    with open("dummy.txt", "w") as f:
        f.write("This is not a PDF.")
        
    with open("dummy.txt", "rb") as f:
        response = await client.post("/agent/ingest", files={"file": ("dummy.txt", f, "text/plain")})
        
    os.remove("dummy.txt")
    
    assert response.status_code == 200
    assert "Invalid file type" in response.json()["output"]


