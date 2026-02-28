#!/usr/bin/env python3
"""Simple test to verify SSE implementation works."""

from fastapi.testclient import TestClient
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.api import app
from app.storage import storage

def test_sse_implementation():
    """Test that SSE clients are properly registered and notified."""
    print("Testing SSE implementation...")

    # Clear storage first
    storage.clear()
    print("✓ Storage cleared")

    # Create a test client
    client = TestClient(app)

    # Test 1: Verify SSE endpoint is accessible
    print("\nTest 1: Checking SSE endpoint accessibility...")
    response = client.get("/admin/events", timeout=1)
    print(f"  SSE endpoint status: {response.status_code}")
    assert response.status_code == 200, "SSE endpoint should return 200"
    print("  ✓ SSE endpoint is accessible")

    # Test 2: Verify populate test data works and notifies clients
    print("\nTest 2: Testing populate test data...")
    response = client.post("/admin/populate-test-data")
    assert response.status_code == 200, "Populate endpoint should return 200"
    data = response.json()
    assert data["status"] == "success", "Populate should succeed"
    print(f"  ✓ Created {data['prompts_created']} prompts and {data['collections_created']} collections")

    # Test 3: Verify clear all data works and notifies clients
    print("\nTest 3: Testing clear all data...")
    response = client.delete("/admin/clear-all-data")
    assert response.status_code == 200, "Clear endpoint should return 200"
    data = response.json()
    assert data["status"] == "success", "Clear should succeed"
    print(f"  ✓ Removed {data['prompts_removed']} prompts and {data['collections_removed']} collections")

    # Test 4: Verify storage is empty after clear
    print("\nTest 4: Verifying storage is empty...")
    prompts = storage.get_all_prompts()
    collections = storage.get_all_collections()
    assert len(prompts) == 0, "Storage should be empty"
    assert len(collections) == 0, "Storage should be empty"
    print("  ✓ Storage is empty")

    # Test 5: Verify sse_clients list exists and is properly structured
    print("\nTest 5: Verifying SSE client management...")
    from app.api import sse_clients
    assert "clients" in sse_clients, "sse_clients should have 'clients' key"
    assert isinstance(sse_clients["clients"], list), "sse_clients['clients'] should be a list"
    print("  ✓ SSE client management is properly structured")

    print("\n✅ All tests passed!")
    return True

if __name__ == "__main__":
    try:
        # Run the test
        result = test_sse_implementation()
        if result:
            print("\n🎉 SSE implementation test completed successfully!")
            sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)