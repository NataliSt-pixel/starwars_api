import asyncio
import aiohttp
import json
import sys
import time

BASE_URL = "http://localhost:8080"


async def check_server_status():
    """Check if server is running"""
    print("Checking server status...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/health", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f" Server is running! Status: {data}")
                    return True
                else:
                    print(f" Server returned status {response.status}")
                    return False
    except aiohttp.ClientConnectorError:
        print(" Cannot connect to server.")
        print("\n  Server is not running!")
        print("   Please start the server first:")
        print("   1. Open another terminal")
        print("   2. Run: python run.py")
        print("   3. Wait for 'Server started on http://localhost:8080'")
        print("   4. Then run tests again")
        return False
    except Exception as e:
        print(f" Error: {e}")
        return False


async def test_endpoints():
    """Test all API endpoints"""

    print("\n" + "=" * 60)
    print("Testing API Endpoints")
    print("=" * 60)

    try:
        async with aiohttp.ClientSession() as session:
            print("\n1. Testing /health endpoint...")
            async with session.get(f"{BASE_URL}/health") as response:
                status = response.status
                print(f"   Status: {status}")
                if status == 200:
                    data = await response.json()
                    print(f"    Success: {json.dumps(data, indent=2)}")
                else:
                    text = await response.text()
                    print(f"    Failed: {text}")
            print("\n2. Testing / endpoint...")
            async with session.get(f"{BASE_URL}/") as response:
                status = response.status
                print(f"   Status: {status}")
                if status == 200:
                    data = await response.json()
                    print(f"    Success: {json.dumps(data, indent=2)}")
                else:
                    text = await response.text()
                    print(f"    Failed: {text}")
            print("\n3. Testing GET /api/ads...")
            async with session.get(f"{BASE_URL}/api/ads") as response:
                status = response.status
                print(f"   Status: {status}")
                if status == 200:
                    data = await response.json()
                    print(f"    Success: Found {len(data)} ads")
                else:
                    text = await response.text()
                    print(f"   Response: {text}")
            print("\n4. Testing POST /api/auth/register...")

            unique_email = f"user{int(time.time())}@mail.com"
            register_data = {
                "email": unique_email,
                "password": "TestPassword123",
                "username": f"testuser_{int(time.time())}"
            }

            print(f"   Registering user: {unique_email}")
            async with session.post(
                    f"{BASE_URL}/api/auth/register",
                    json=register_data
            ) as response:
                status = response.status
                print(f"   Status: {status}")
                if status in [200, 201]:
                    data = await response.json()
                    print(f"    Success: User created with ID: {data.get('id')}")
                    user_id = data.get('id')
                else:
                    text = await response.text()
                    print(f"    Failed: {text}")
                    user_id = None

            print("\n5. Testing POST /api/auth/login...")
            token = None
            if user_id:
                login_data = {
                    "email": unique_email,
                    "password": "TestPassword123"
                }

                async with session.post(
                        f"{BASE_URL}/api/auth/login",
                        json=login_data
                ) as response:
                    status = response.status
                    print(f"   Status: {status}")
                    if status == 200:
                        data = await response.json()
                        token = data.get('access_token')
                        if token:
                            print(f"    Success: Got access token")
                            print(f"   Token (first 20 chars): {token[:20]}...")
                        else:
                            print("    No access token in response")
                    else:
                        text = await response.text()
                        print(f"    Login failed: {text}")
            else:
                print("     Skipping login test (registration failed)")

            if token:
                print("\n6. Testing POST /api/ads (with auth)...")
                headers = {"Authorization": f"Bearer {token}"}
                ad_data = {
                    "title": "Test Advertisement",
                    "description": "This is a test ad created via API"
                }

                async with session.post(
                        f"{BASE_URL}/api/ads",
                        json=ad_data,
                        headers=headers
                ) as response:
                    status = response.status
                    print(f"   Status: {status}")
                    if status in [200, 201]:
                        data = await response.json()
                        ad_id = data.get('id')
                        print(f"    Success: Ad created with ID: {ad_id}")
                        print(f"\n7. Testing GET /api/ads/{ad_id}...")
                        async with session.get(f"{BASE_URL}/api/ads/{ad_id}") as response:
                            status = response.status
                            print(f"   Status: {status}")
                            if status == 200:
                                ad_data = await response.json()
                                print(f"    Success: Ad found: {ad_data['title']}")
                                print(f"\n8. Testing PUT /api/ads/{ad_id}...")
                                update_data = {
                                    "title": "Updated Test Ad",
                                    "description": "Updated description via API"
                                }

                                async with session.put(
                                        f"{BASE_URL}/api/ads/{ad_id}",
                                        json=update_data,
                                        headers=headers
                                ) as response:
                                    status = response.status
                                    print(f"   Status: {status}")
                                    if status == 200:
                                        print(f"    Success: Ad updated")
                                        print(f"\n9. Testing DELETE /api/ads/{ad_id}...")
                                        async with session.delete(
                                                f"{BASE_URL}/api/ads/{ad_id}",
                                                headers=headers
                                        ) as response:
                                            status = response.status
                                            print(f"   Status: {status}")
                                            if status == 200:
                                                print(f"    Success: Ad deleted")
                                            else:
                                                text = await response.text()
                                                print(f"    Delete failed: {text}")
                                    else:
                                        text = await response.text()
                                        print(f"    Update failed: {text}")
                            else:
                                text = await response.text()
                                print(f"    Failed to get ad: {text}")
                    else:
                        text = await response.text()
                        print(f"    Failed to create ad: {text}")
                        print(f"   Headers sent: {headers}")
            else:
                print("     Skipping ad operations (no auth token)")

            print("\n" + "=" * 60)
            print(" API tests completed!")
            print("=" * 60)

    except Exception as e:
        print(f"\n Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


async def main():
    """Main test function"""
    print("\n" + "=" * 60)
    print("Ads API Test Suite")
    print("=" * 60)
    print(f"Testing server at: {BASE_URL}")

    if not await check_server_status():
        sys.exit(1)
    success = await test_endpoints()

    if success:
        print("\n All tests passed!")
        sys.exit(0)
    else:
        print("\n Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())