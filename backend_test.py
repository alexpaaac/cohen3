#!/usr/bin/env python3
"""
Backend API Testing for Risk Hunt Game Builder
Tests all core API endpoints with realistic data
"""

import requests
import json
import base64
import io
from PIL import Image
import os
from datetime import datetime

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

print(f"Testing backend at: {API_URL}")

# Test results storage
test_results = {
    "image_management": {"passed": 0, "failed": 0, "errors": []},
    "enhanced_image_management": {"passed": 0, "failed": 0, "errors": []},
    "risk_zone_annotation": {"passed": 0, "failed": 0, "errors": []},
    "game_configuration": {"passed": 0, "failed": 0, "errors": []},
    "enhanced_game_management": {"passed": 0, "failed": 0, "errors": []},
    "game_session_management": {"passed": 0, "failed": 0, "errors": []},
    "enhanced_session_management": {"passed": 0, "failed": 0, "errors": []},
    "results_tracking": {"passed": 0, "failed": 0, "errors": []},
    "results_analytics": {"passed": 0, "failed": 0, "errors": []},
    "sample_data_setup": {"passed": 0, "failed": 0, "errors": []}
}

def log_test(category, test_name, success, error_msg=None):
    """Log test results"""
    if success:
        test_results[category]["passed"] += 1
        print(f"✅ {test_name}")
    else:
        test_results[category]["failed"] += 1
        test_results[category]["errors"].append(f"{test_name}: {error_msg}")
        print(f"❌ {test_name}: {error_msg}")

def create_test_image():
    """Create a simple test image in base64 format"""
    # Create a simple 100x100 red image
    img = Image.new('RGB', (100, 100), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_data = buffer.getvalue()
    return base64.b64encode(img_data).decode('utf-8')

# Global variables to store created IDs for testing
created_image_id = None
created_game_id = None
created_session_id = None
duplicate_image_id = None
duplicate_game_id = None
public_game_link = None

def test_image_management():
    """Test Image Management API endpoints"""
    global created_image_id
    
    print("\n=== Testing Image Management API ===")
    
    # Test 1: Upload image
    try:
        test_image_data = create_test_image()
        files = {
            'file': ('test_workplace.png', base64.b64decode(test_image_data), 'image/png')
        }
        data = {'name': 'Industrial Workplace Safety Scene'}
        
        response = requests.post(f"{API_URL}/images/upload", files=files, data=data)
        if response.status_code == 200:
            result = response.json()
            created_image_id = result.get('id')
            log_test("image_management", "Upload image", True)
        else:
            log_test("image_management", "Upload image", False, f"Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        log_test("image_management", "Upload image", False, str(e))
    
    # Test 2: Get all images
    try:
        response = requests.get(f"{API_URL}/images")
        if response.status_code == 200:
            images = response.json()
            log_test("image_management", "Get all images", True)
        else:
            log_test("image_management", "Get all images", False, f"Status: {response.status_code}")
    except Exception as e:
        log_test("image_management", "Get all images", False, str(e))
    
    # Test 3: Get specific image
    if created_image_id:
        try:
            response = requests.get(f"{API_URL}/images/{created_image_id}")
            if response.status_code == 200:
                image = response.json()
                log_test("image_management", "Get specific image", True)
            else:
                log_test("image_management", "Get specific image", False, f"Status: {response.status_code}")
        except Exception as e:
            log_test("image_management", "Get specific image", False, str(e))

def test_risk_zone_annotation():
    """Test Risk Zone Annotation API"""
    global created_image_id
    
    print("\n=== Testing Risk Zone Annotation API ===")
    
    if not created_image_id:
        log_test("risk_zone_annotation", "Update risk zones", False, "No image ID available")
        return
    
    # Test: Update risk zones for an image
    try:
        risk_zones = [
            {
                "id": "risk_zone_1",
                "type": "circle",
                "coordinates": [50, 30, 15],  # x, y, radius
                "description": "Exposed electrical panel",
                "difficulty": "medium",
                "points": 5,
                "explanation": "Electrical panels should be properly covered to prevent accidental contact"
            },
            {
                "id": "risk_zone_2", 
                "type": "rectangle",
                "coordinates": [20, 60, 30, 20],  # x, y, width, height
                "description": "Unguarded machinery",
                "difficulty": "hard",
                "points": 10,
                "explanation": "Moving machinery parts must have proper safety guards"
            }
        ]
        
        response = requests.put(f"{API_URL}/images/{created_image_id}/risk-zones", 
                              json=risk_zones)
        if response.status_code == 200:
            log_test("risk_zone_annotation", "Update risk zones", True)
        else:
            log_test("risk_zone_annotation", "Update risk zones", False, f"Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        log_test("risk_zone_annotation", "Update risk zones", False, str(e))

def test_game_configuration():
    """Test Game Configuration API"""
    global created_game_id, created_image_id
    
    print("\n=== Testing Game Configuration API ===")
    
    # Test 1: Create game
    try:
        game_data = {
            "name": "Workplace Safety Challenge",
            "description": "Identify safety hazards in industrial workplace environments",
            "time_limit": 300,
            "max_clicks": 17,
            "target_risks": 15,
            "images": [created_image_id] if created_image_id else []
        }
        
        response = requests.post(f"{API_URL}/games", json=game_data)
        if response.status_code == 200:
            result = response.json()
            created_game_id = result.get('id')
            log_test("game_configuration", "Create game", True)
        else:
            log_test("game_configuration", "Create game", False, f"Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        log_test("game_configuration", "Create game", False, str(e))
    
    # Test 2: Get all games
    try:
        response = requests.get(f"{API_URL}/games")
        if response.status_code == 200:
            games = response.json()
            log_test("game_configuration", "Get all games", True)
        else:
            log_test("game_configuration", "Get all games", False, f"Status: {response.status_code}")
    except Exception as e:
        log_test("game_configuration", "Get all games", False, str(e))
    
    # Test 3: Get specific game
    if created_game_id:
        try:
            response = requests.get(f"{API_URL}/games/{created_game_id}")
            if response.status_code == 200:
                game = response.json()
                log_test("game_configuration", "Get specific game", True)
            else:
                log_test("game_configuration", "Get specific game", False, f"Status: {response.status_code}")
        except Exception as e:
            log_test("game_configuration", "Get specific game", False, str(e))

def test_game_session_management():
    """Test Game Session Management API"""
    global created_session_id, created_game_id
    
    print("\n=== Testing Game Session Management API ===")
    
    # Test 1: Create session
    try:
        session_data = {
            "game_id": created_game_id if created_game_id else "test_game_id",
            "player_name": "Sarah Johnson",
            "team_name": "Safety Champions",
            "current_image_index": 0,
            "found_risks": [],
            "clicks_used": 0,
            "time_remaining": 300,
            "score": 0,
            "status": "active"
        }
        
        response = requests.post(f"{API_URL}/sessions", json=session_data)
        if response.status_code == 200:
            result = response.json()
            created_session_id = result.get('id')
            log_test("game_session_management", "Create session", True)
        else:
            log_test("game_session_management", "Create session", False, f"Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        log_test("game_session_management", "Create session", False, str(e))
    
    # Test 2: Get session
    if created_session_id:
        try:
            response = requests.get(f"{API_URL}/sessions/{created_session_id}")
            if response.status_code == 200:
                session = response.json()
                log_test("game_session_management", "Get session", True)
            else:
                log_test("game_session_management", "Get session", False, f"Status: {response.status_code}")
        except Exception as e:
            log_test("game_session_management", "Get session", False, str(e))
    
    # Test 3: Update session
    if created_session_id:
        try:
            update_data = {
                "time_remaining": 250,
                "clicks_used": 3
            }
            
            response = requests.put(f"{API_URL}/sessions/{created_session_id}", json=update_data)
            if response.status_code == 200:
                log_test("game_session_management", "Update session", True)
            else:
                log_test("game_session_management", "Update session", False, f"Status: {response.status_code}")
        except Exception as e:
            log_test("game_session_management", "Update session", False, str(e))
    
    # Test 4: Handle click (this requires proper game setup with risk zones)
    if created_session_id and created_game_id and created_image_id:
        try:
            click_data = {
                "x": 50,
                "y": 30
            }
            
            response = requests.post(f"{API_URL}/sessions/{created_session_id}/click", json=click_data)
            if response.status_code == 200:
                result = response.json()
                log_test("game_session_management", "Handle click", True)
            else:
                log_test("game_session_management", "Handle click", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            log_test("game_session_management", "Handle click", False, str(e))

def test_results_tracking():
    """Test Results Tracking API"""
    global created_session_id, created_game_id
    
    print("\n=== Testing Results Tracking API ===")
    
    # Test 1: Save result
    try:
        result_data = {
            "session_id": created_session_id if created_session_id else "test_session_id",
            "game_id": created_game_id if created_game_id else "test_game_id",
            "player_name": "Sarah Johnson",
            "team_name": "Safety Champions",
            "total_score": 85,
            "total_risks_found": 12,
            "total_time_spent": 240,
            "image_results": [
                {
                    "image_id": created_image_id if created_image_id else "test_image_id",
                    "risks_found": 12,
                    "time_spent": 240,
                    "clicks_used": 15
                }
            ]
        }
        
        response = requests.post(f"{API_URL}/results", json=result_data)
        if response.status_code == 200:
            log_test("results_tracking", "Save result", True)
        else:
            log_test("results_tracking", "Save result", False, f"Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        log_test("results_tracking", "Save result", False, str(e))
    
    # Test 2: Get all results
    try:
        response = requests.get(f"{API_URL}/results")
        if response.status_code == 200:
            results = response.json()
            log_test("results_tracking", "Get all results", True)
        else:
            log_test("results_tracking", "Get all results", False, f"Status: {response.status_code}")
    except Exception as e:
        log_test("results_tracking", "Get all results", False, str(e))
    
    # Test 3: Get game results
    if created_game_id:
        try:
            response = requests.get(f"{API_URL}/results/game/{created_game_id}")
            if response.status_code == 200:
                game_results = response.json()
                log_test("results_tracking", "Get game results", True)
            else:
                log_test("results_tracking", "Get game results", False, f"Status: {response.status_code}")
        except Exception as e:
            log_test("results_tracking", "Get game results", False, str(e))

def test_enhanced_image_management():
    """Test Enhanced Image Management API endpoints"""
    global created_image_id, duplicate_image_id
    
    print("\n=== Testing Enhanced Image Management API ===")
    
    if not created_image_id:
        log_test("enhanced_image_management", "Update image details", False, "No image ID available")
        log_test("enhanced_image_management", "Delete image", False, "No image ID available")
        log_test("enhanced_image_management", "Duplicate image", False, "No image ID available")
        return
    
    # Test 1: Update image details
    try:
        update_data = {
            "name": "Updated Industrial Workplace Safety Scene",
            "description": "Updated description for safety training"
        }
        
        response = requests.put(f"{API_URL}/images/{created_image_id}", json=update_data)
        if response.status_code == 200:
            log_test("enhanced_image_management", "Update image details", True)
        else:
            log_test("enhanced_image_management", "Update image details", False, f"Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        log_test("enhanced_image_management", "Update image details", False, str(e))
    
    # Test 2: Duplicate image
    try:
        response = requests.post(f"{API_URL}/images/{created_image_id}/duplicate")
        if response.status_code == 200:
            result = response.json()
            duplicate_image_id = result.get('id')
            log_test("enhanced_image_management", "Duplicate image", True)
        else:
            log_test("enhanced_image_management", "Duplicate image", False, f"Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        log_test("enhanced_image_management", "Duplicate image", False, str(e))
    
    # Test 3: Delete image (delete the duplicate to avoid affecting other tests)
    if duplicate_image_id:
        try:
            response = requests.delete(f"{API_URL}/images/{duplicate_image_id}")
            if response.status_code == 200:
                log_test("enhanced_image_management", "Delete image", True)
            else:
                log_test("enhanced_image_management", "Delete image", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            log_test("enhanced_image_management", "Delete image", False, str(e))

def test_enhanced_game_management():
    """Test Enhanced Game Management API endpoints"""
    global created_game_id, duplicate_game_id, public_game_link
    
    print("\n=== Testing Enhanced Game Management API ===")
    
    if not created_game_id:
        log_test("enhanced_game_management", "Update game configuration", False, "No game ID available")
        log_test("enhanced_game_management", "Delete game", False, "No game ID available")
        log_test("enhanced_game_management", "Duplicate game", False, "No game ID available")
        log_test("enhanced_game_management", "Get public game by link", False, "No game ID available")
        return
    
    # Test 1: Update game configuration
    try:
        update_data = {
            "name": "Updated Workplace Safety Challenge",
            "description": "Updated comprehensive safety hazard identification game",
            "time_limit": 450,
            "max_clicks": 20,
            "target_risks": 18,
            "is_public": True
        }
        
        response = requests.put(f"{API_URL}/games/{created_game_id}", json=update_data)
        if response.status_code == 200:
            log_test("enhanced_game_management", "Update game configuration", True)
        else:
            log_test("enhanced_game_management", "Update game configuration", False, f"Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        log_test("enhanced_game_management", "Update game configuration", False, str(e))
    
    # Test 2: Duplicate game
    try:
        response = requests.post(f"{API_URL}/games/{created_game_id}/duplicate")
        if response.status_code == 200:
            result = response.json()
            duplicate_game_id = result.get('id')
            log_test("enhanced_game_management", "Duplicate game", True)
        else:
            log_test("enhanced_game_management", "Duplicate game", False, f"Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        log_test("enhanced_game_management", "Duplicate game", False, str(e))
    
    # Test 3: Get public game by link (first get the updated game to check public link)
    try:
        # Get the updated game to see if it has a public link
        response = requests.get(f"{API_URL}/games/{created_game_id}")
        if response.status_code == 200:
            game = response.json()
            public_game_link = game.get('public_link')
            
            if public_game_link:
                # Test getting public game by link
                response = requests.get(f"{API_URL}/public/games/{public_game_link}")
                if response.status_code == 200:
                    public_game = response.json()
                    log_test("enhanced_game_management", "Get public game by link", True)
                else:
                    log_test("enhanced_game_management", "Get public game by link", False, f"Status: {response.status_code}, Response: {response.text}")
            else:
                log_test("enhanced_game_management", "Get public game by link", False, "No public link generated")
        else:
            log_test("enhanced_game_management", "Get public game by link", False, f"Could not get game details: {response.status_code}")
    except Exception as e:
        log_test("enhanced_game_management", "Get public game by link", False, str(e))
    
    # Test 4: Delete game (delete the duplicate to avoid affecting other tests)
    if duplicate_game_id:
        try:
            response = requests.delete(f"{API_URL}/games/{duplicate_game_id}")
            if response.status_code == 200:
                log_test("enhanced_game_management", "Delete game", True)
            else:
                log_test("enhanced_game_management", "Delete game", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            log_test("enhanced_game_management", "Delete game", False, str(e))

def test_enhanced_session_management():
    """Test Enhanced Session Management API endpoints"""
    global created_session_id, created_game_id
    
    print("\n=== Testing Enhanced Session Management API ===")
    
    if not created_session_id:
        log_test("enhanced_session_management", "Handle game timeout", False, "No session ID available")
        return
    
    # Create a new session for timeout testing (to avoid affecting the main session)
    timeout_session_id = None
    try:
        session_data = {
            "game_id": created_game_id if created_game_id else "test_game_id",
            "player_name": "Mike Wilson",
            "team_name": "Safety Testers",
            "current_image_index": 0,
            "found_risks": [],
            "clicks_used": 5,
            "time_remaining": 0,  # Set to 0 to simulate timeout
            "score": 25,
            "status": "active"
        }
        
        response = requests.post(f"{API_URL}/sessions", json=session_data)
        if response.status_code == 200:
            result = response.json()
            timeout_session_id = result.get('id')
        
    except Exception as e:
        log_test("enhanced_session_management", "Handle game timeout", False, f"Could not create timeout session: {str(e)}")
        return
    
    # Test: Handle game timeout
    if timeout_session_id:
        try:
            response = requests.post(f"{API_URL}/sessions/{timeout_session_id}/timeout")
            if response.status_code == 200:
                result = response.json()
                log_test("enhanced_session_management", "Handle game timeout", True)
            else:
                log_test("enhanced_session_management", "Handle game timeout", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            log_test("enhanced_session_management", "Handle game timeout", False, str(e))

def test_results_analytics():
    """Test Results & Analytics API endpoints"""
    global created_game_id
    
    print("\n=== Testing Results & Analytics API ===")
    
    if not created_game_id:
        log_test("results_analytics", "Get game analytics", False, "No game ID available")
        log_test("results_analytics", "Export results CSV", False, "No game ID available")
        log_test("results_analytics", "Export results Excel", False, "No game ID available")
        return
    
    # Test 1: Get game analytics
    try:
        response = requests.get(f"{API_URL}/results/analytics/{created_game_id}")
        if response.status_code == 200:
            analytics = response.json()
            # Verify analytics structure
            expected_keys = ["total_players", "average_score", "average_time", "total_clicks", "total_risks_found", "results"]
            if all(key in analytics for key in expected_keys):
                log_test("results_analytics", "Get game analytics", True)
            else:
                log_test("results_analytics", "Get game analytics", False, f"Missing expected keys in analytics response")
        else:
            log_test("results_analytics", "Get game analytics", False, f"Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        log_test("results_analytics", "Get game analytics", False, str(e))
    
    # Test 2: Export results as CSV
    try:
        response = requests.get(f"{API_URL}/results/export/{created_game_id}?format=csv")
        if response.status_code == 200:
            # Check if response is CSV format
            content_type = response.headers.get('content-type', '')
            if 'text/csv' in content_type or 'csv' in response.headers.get('content-disposition', ''):
                log_test("results_analytics", "Export results CSV", True)
            else:
                log_test("results_analytics", "Export results CSV", False, f"Unexpected content type: {content_type}")
        else:
            log_test("results_analytics", "Export results CSV", False, f"Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        log_test("results_analytics", "Export results CSV", False, str(e))
    
    # Test 3: Export results as Excel
    try:
        response = requests.get(f"{API_URL}/results/export/{created_game_id}?format=excel")
        if response.status_code == 200:
            # Check if response is Excel format
            content_type = response.headers.get('content-type', '')
            if 'spreadsheet' in content_type or 'xlsx' in response.headers.get('content-disposition', ''):
                log_test("results_analytics", "Export results Excel", True)
            else:
                log_test("results_analytics", "Export results Excel", False, f"Unexpected content type: {content_type}")
        else:
            log_test("results_analytics", "Export results Excel", False, f"Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        log_test("results_analytics", "Export results Excel", False, str(e))

def test_sample_data_setup():
    """Test Sample Data Setup API"""
    print("\n=== Testing Sample Data Setup API ===")
    
    # Test: Create sample images
    try:
        response = requests.post(f"{API_URL}/setup/sample-images")
        if response.status_code == 200:
            result = response.json()
            log_test("sample_data_setup", "Create sample images", True)
        else:
            log_test("sample_data_setup", "Create sample images", False, f"Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        log_test("sample_data_setup", "Create sample images", False, str(e))

def print_summary():
    """Print test summary"""
    print("\n" + "="*60)
    print("BACKEND API TEST SUMMARY")
    print("="*60)
    
    total_passed = 0
    total_failed = 0
    
    for category, results in test_results.items():
        passed = results["passed"]
        failed = results["failed"]
        total_passed += passed
        total_failed += failed
        
        status = "✅ PASS" if failed == 0 else "❌ FAIL"
        print(f"{category.replace('_', ' ').title()}: {status} ({passed} passed, {failed} failed)")
        
        if results["errors"]:
            for error in results["errors"]:
                print(f"  - {error}")
    
    print(f"\nOVERALL: {total_passed} passed, {total_failed} failed")
    
    if total_failed == 0:
        print("🎉 All backend API tests passed!")
    else:
        print(f"⚠️  {total_failed} tests failed - see details above")

if __name__ == "__main__":
    print("Starting Risk Hunt Game Builder Backend API Tests...")
    print(f"Backend URL: {API_URL}")
    
    # Run all tests in sequence
    test_sample_data_setup()
    test_image_management()
    test_enhanced_image_management()
    test_risk_zone_annotation()
    test_game_configuration()
    test_enhanced_game_management()
    test_game_session_management()
    test_enhanced_session_management()
    test_results_tracking()
    test_results_analytics()
    
    # Print final summary
    print_summary()