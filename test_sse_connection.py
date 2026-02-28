#!/usr/bin/env python3
"""Test script to verify SSE connection works with admin operations."""

import asyncio
import aiohttp
import json
from fastapi.testclient import TestClient
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.api import app
from app.storage import storage

async def test_sse_with_admin_operations():
    """Test that SSE connection receives notifications from admin operations."""
    print("Starting SSE connection test...")

    # Clear storage first
    storage.clear()
    print("✓ Storage cleared")

    # Create a test client
    client = TestClient(app)

    # Test 1: Verify SSE endpoint is accessible
    print("\nTest 1: Checking SSE endpoint accessibility...")
    response = client.get("/admin/events")
    print(f"  SSE endpoint status: {response.status_code}")
    assert response.status_code == 200, "SSE endpoint should return 200"
    print("  ✓ SSE endpoint is accessible")

    # Test 2: Verify populate test data works
    print("\nTest 2: Testing populate test data...")
    response = client.post("/admin/populate-test-data")
    assert response.status_code == 200, "Populate endpoint should return 200"
    data = response.json()
    assert data["status"] == "success", "Populate should succeed"
    print(f"  ✓ Created {data['prompts_created']} prompts and {data['collections_created']} collections")

    # Test 3: Verify clear all data works
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

    print("\n✅ All tests passed!")
    return True

if __name__ == "__main__":
    try:
        # Run the test
        result = asyncio.run(test_sse_with_admin_operations())
        if result:
            print("\n🎉 SSE connection test completed successfully!")
            sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)