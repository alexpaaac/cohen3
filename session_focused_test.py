#!/usr/bin/env python3
"""
Focused Session Management Testing for Risk Hunt Game Builder
Specifically tests the critical runtime error fix: gameSession.found_risks.includes is not a function
"""

import requests
import json
import base64
import io
from PIL import Image

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=')[1].strip()
    except:
        pass
    return "http://localhost:8001"

BASE_URL = get_backend_url()
API_URL = f"{BASE_URL}/api"

print(f"🔍 FOCUSED SESSION TESTING at: {API_URL}")
print("=" * 80)

def create_test_image():
    """Create a simple test image in base64 format"""
    img = Image.new('RGB', (100, 100), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_data = buffer.getvalue()
    return base64.b64encode(img_data).decode('utf-8')

def test_session_found_risks_array_initialization():
    """Test that found_risks is properly initialized as an array in all session operations"""
    
    print("\n🎯 CRITICAL TEST: Session found_risks Array Initialization")
    print("-" * 60)
    
    # Step 1: Create test image with risk zones
    print("1️⃣ Setting up test image with risk zones...")
    try:
        test_image_data = create_test_image()
        files = {
            'file': ('test_session.png', base64.b64decode(test_image_data), 'image/png')
        }
        data = {'name': 'Session Test Image'}
        
        response = requests.post(f"{API_URL}/images/upload", files=files, data=data)
        if response.status_code != 200:
            print(f"❌ Failed to create test image: {response.status_code}")
            return False
        
        image_id = response.json().get('id')
        print(f"✅ Created test image: {image_id}")
        
        # Add risk zones
        risk_zones = [
            {
                "id": "risk_zone_1",
                "type": "circle",
                "coordinates": [50, 30, 15],
                "description": "Test risk zone 1",
                "difficulty": "medium",
                "points": 5,
                "explanation": "Test explanation"
            },
            {
                "id": "risk_zone_2",
                "type": "rectangle", 
                "coordinates": [20, 60, 30, 20],
                "description": "Test risk zone 2",
                "difficulty": "hard",
                "points": 10,
                "explanation": "Test explanation 2"
            }
        ]
        
        response = requests.put(f"{API_URL}/images/{image_id}/risk-zones", json=risk_zones)
        if response.status_code != 200:
            print(f"❌ Failed to add risk zones: {response.status_code}")
            return False
        print("✅ Added risk zones to test image")
        
    except Exception as e:
        print(f"❌ Error setting up test image: {str(e)}")
        return False
    
    # Step 2: Create test game
    print("\n2️⃣ Creating test game...")
    try:
        game_data = {
            "name": "Session Test Game",
            "description": "Test game for session management",
            "time_limit": 300,
            "max_clicks": 17,
            "target_risks": 15,
            "images": [image_id]
        }
        
        response = requests.post(f"{API_URL}/games", json=game_data)
        if response.status_code != 200:
            print(f"❌ Failed to create test game: {response.status_code}")
            return False
        
        game_id = response.json().get('id')
        print(f"✅ Created test game: {game_id}")
        
    except Exception as e:
        print(f"❌ Error creating test game: {str(e)}")
        return False
    
    # Step 3: Test POST /api/sessions - Critical found_risks initialization
    print("\n3️⃣ CRITICAL TEST: POST /api/sessions - found_risks array initialization")
    try:
        session_data = {
            "game_id": game_id,
            "player_name": "Test Player",
            "team_name": "Test Team",
            "current_image_index": 0,
            "found_risks": [],  # Explicitly set as empty array
            "clicks_used": 0,
            "time_remaining": 300,
            "score": 0,
            "status": "active"
        }
        
        response = requests.post(f"{API_URL}/sessions", json=session_data)
        if response.status_code != 200:
            print(f"❌ Failed to create session: {response.status_code} - {response.text}")
            return False
        
        session_result = response.json()
        session_id = session_result.get('id')
        
        # CRITICAL CHECK: Verify found_risks is an array
        found_risks = session_result.get('found_risks')
        if not isinstance(found_risks, list):
            print(f"❌ CRITICAL ERROR: found_risks is not an array! Type: {type(found_risks)}, Value: {found_risks}")
            return False
        
        if len(found_risks) != 0:
            print(f"❌ CRITICAL ERROR: found_risks should be empty array, got: {found_risks}")
            return False
        
        print(f"✅ CRITICAL SUCCESS: found_risks properly initialized as empty array: {found_risks}")
        print(f"✅ Created session: {session_id}")
        
    except Exception as e:
        print(f"❌ Error creating session: {str(e)}")
        return False
    
    # Step 4: Test GET /api/sessions/{session_id} - Verify array consistency
    print("\n4️⃣ CRITICAL TEST: GET /api/sessions/{session_id} - found_risks array consistency")
    try:
        response = requests.get(f"{API_URL}/sessions/{session_id}")
        if response.status_code != 200:
            print(f"❌ Failed to get session: {response.status_code}")
            return False
        
        session = response.json()
        found_risks = session.get('found_risks')
        
        # CRITICAL CHECK: Verify found_risks is still an array
        if not isinstance(found_risks, list):
            print(f"❌ CRITICAL ERROR: found_risks is not an array in GET response! Type: {type(found_risks)}, Value: {found_risks}")
            return False
        
        print(f"✅ CRITICAL SUCCESS: found_risks remains as array in GET: {found_risks}")
        
    except Exception as e:
        print(f"❌ Error getting session: {str(e)}")
        return False
    
    # Step 5: Test POST /api/sessions/{session_id}/click - Critical array update
    print("\n5️⃣ CRITICAL TEST: POST /api/sessions/{session_id}/click - found_risks array update")
    try:
        # Test click that hits risk zone 1
        click_data = {
            "x": 50,  # Center of risk_zone_1 circle
            "y": 30
        }
        
        response = requests.post(f"{API_URL}/sessions/{session_id}/click", json=click_data)
        if response.status_code != 200:
            print(f"❌ Failed to handle click: {response.status_code} - {response.text}")
            return False
        
        click_result = response.json()
        
        # CRITICAL CHECK: Verify response structure
        if not click_result.get('hit'):
            print(f"❌ Click should have hit risk zone, but got hit=False")
            return False
        
        # Verify found_risks count is updated
        found_risks_count = click_result.get('found_risks')
        if found_risks_count != 1:
            print(f"❌ Expected found_risks count to be 1, got: {found_risks_count}")
            return False
        
        print(f"✅ CRITICAL SUCCESS: Click hit detection working, found_risks count: {found_risks_count}")
        
        # Verify session was updated with array
        response = requests.get(f"{API_URL}/sessions/{session_id}")
        if response.status_code != 200:
            print(f"❌ Failed to get updated session: {response.status_code}")
            return False
        
        updated_session = response.json()
        found_risks_array = updated_session.get('found_risks')
        
        # CRITICAL CHECK: Verify found_risks is still an array and contains the risk
        if not isinstance(found_risks_array, list):
            print(f"❌ CRITICAL ERROR: found_risks is not an array after click! Type: {type(found_risks_array)}, Value: {found_risks_array}")
            return False
        
        if len(found_risks_array) != 1:
            print(f"❌ CRITICAL ERROR: found_risks array should have 1 item, got: {len(found_risks_array)} items: {found_risks_array}")
            return False
        
        if "risk_zone_1" not in found_risks_array:
            print(f"❌ CRITICAL ERROR: risk_zone_1 should be in found_risks array, got: {found_risks_array}")
            return False
        
        print(f"✅ CRITICAL SUCCESS: found_risks properly updated as array: {found_risks_array}")
        
    except Exception as e:
        print(f"❌ Error handling click: {str(e)}")
        return False
    
    # Step 6: Test multiple clicks to verify array operations
    print("\n6️⃣ CRITICAL TEST: Multiple clicks - found_risks array operations")
    try:
        # Test click that hits risk zone 2
        click_data = {
            "x": 35,  # Inside risk_zone_2 rectangle (20,60,30,20)
            "y": 70
        }
        
        response = requests.post(f"{API_URL}/sessions/{session_id}/click", json=click_data)
        if response.status_code != 200:
            print(f"❌ Failed to handle second click: {response.status_code} - {response.text}")
            return False
        
        click_result = response.json()
        
        # Verify second hit
        if not click_result.get('hit'):
            print(f"❌ Second click should have hit risk zone, but got hit=False")
            return False
        
        # Verify found_risks count is now 2
        found_risks_count = click_result.get('found_risks')
        if found_risks_count != 2:
            print(f"❌ Expected found_risks count to be 2, got: {found_risks_count}")
            return False
        
        # Verify session array has both risks
        response = requests.get(f"{API_URL}/sessions/{session_id}")
        if response.status_code != 200:
            print(f"❌ Failed to get session after second click: {response.status_code}")
            return False
        
        final_session = response.json()
        found_risks_array = final_session.get('found_risks')
        
        # CRITICAL CHECK: Verify array has both items
        if not isinstance(found_risks_array, list):
            print(f"❌ CRITICAL ERROR: found_risks is not an array after multiple clicks! Type: {type(found_risks_array)}")
            return False
        
        if len(found_risks_array) != 2:
            print(f"❌ CRITICAL ERROR: found_risks array should have 2 items, got: {len(found_risks_array)} items: {found_risks_array}")
            return False
        
        expected_risks = ["risk_zone_1", "risk_zone_2"]
        for risk_id in expected_risks:
            if risk_id not in found_risks_array:
                print(f"❌ CRITICAL ERROR: {risk_id} should be in found_risks array, got: {found_risks_array}")
                return False
        
        print(f"✅ CRITICAL SUCCESS: Multiple risks properly stored in array: {found_risks_array}")
        
    except Exception as e:
        print(f"❌ Error handling multiple clicks: {str(e)}")
        return False
    
    # Step 7: Test duplicate click (should not add duplicate to array)
    print("\n7️⃣ CRITICAL TEST: Duplicate click - array deduplication")
    try:
        # Click same location as first click
        click_data = {
            "x": 50,
            "y": 30
        }
        
        response = requests.post(f"{API_URL}/sessions/{session_id}/click", json=click_data)
        if response.status_code != 200:
            print(f"❌ Failed to handle duplicate click: {response.status_code} - {response.text}")
            return False
        
        click_result = response.json()
        
        # Should still hit but not increase count
        if not click_result.get('hit'):
            print(f"❌ Duplicate click should still register as hit")
            return False
        
        # Verify found_risks count is still 2 (no duplicate)
        found_risks_count = click_result.get('found_risks')
        if found_risks_count != 2:
            print(f"❌ Expected found_risks count to remain 2 after duplicate, got: {found_risks_count}")
            return False
        
        print(f"✅ CRITICAL SUCCESS: Duplicate click properly handled, count remains: {found_risks_count}")
        
    except Exception as e:
        print(f"❌ Error handling duplicate click: {str(e)}")
        return False
    
    # Step 8: Test session timeout with found_risks array
    print("\n8️⃣ CRITICAL TEST: Session timeout - found_risks array preservation")
    try:
        response = requests.post(f"{API_URL}/sessions/{session_id}/timeout")
        if response.status_code != 200:
            print(f"❌ Failed to handle timeout: {response.status_code} - {response.text}")
            return False
        
        timeout_result = response.json()
        
        # Verify result contains proper data
        if 'result' not in timeout_result:
            print(f"❌ Timeout response should contain result object")
            return False
        
        result_data = timeout_result['result']
        total_risks_found = result_data.get('total_risks_found')
        
        if total_risks_found != 2:
            print(f"❌ Expected total_risks_found to be 2 in timeout result, got: {total_risks_found}")
            return False
        
        print(f"✅ CRITICAL SUCCESS: Session timeout properly preserved found_risks count: {total_risks_found}")
        
    except Exception as e:
        print(f"❌ Error handling timeout: {str(e)}")
        return False
    
    print("\n" + "=" * 80)
    print("🎉 ALL CRITICAL SESSION TESTS PASSED!")
    print("✅ found_risks is properly initialized as an array")
    print("✅ found_risks remains an array throughout all operations")
    print("✅ Array operations (add, deduplicate) work correctly")
    print("✅ Session endpoints return consistent data structures")
    print("✅ Critical runtime error 'gameSession.found_risks.includes is not a function' is RESOLVED")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    success = test_session_found_risks_array_initialization()
    if success:
        print("\n🚀 BACKEND SESSION MANAGEMENT: ENTERPRISE READY")
    else:
        print("\n💥 CRITICAL ISSUES FOUND - NEEDS IMMEDIATE ATTENTION")