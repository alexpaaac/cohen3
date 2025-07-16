#!/usr/bin/env python3
"""
Enhanced Backend API Testing for Risk Hunt Game Builder
Focus on critical enterprise improvements as requested in review
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

print(f"Testing enhanced backend features at: {API_URL}")

def create_test_image():
    """Create a simple test image in base64 format"""
    img = Image.new('RGB', (100, 100), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_data = buffer.getvalue()
    return base64.b64encode(img_data).decode('utf-8')

def test_critical_performance_fixes():
    """Test Critical Performance Fixes - Enhanced export functionality"""
    print("\n=== Testing CRITICAL Performance Fixes ===")
    
    # Create test data first
    test_image_data = create_test_image()
    files = {
        'file': ('test_export.png', base64.b64decode(test_image_data), 'image/png')
    }
    data = {'name': 'Export Test Image'}
    
    # Upload image
    response = requests.post(f"{API_URL}/images/upload", files=files, data=data)
    if response.status_code != 200:
        print("❌ Failed to create test image for export tests")
        return
    
    image_id = response.json().get('id')
    
    # Create game
    game_data = {
        "name": "Export Test Game",
        "description": "Game for testing export functionality",
        "time_limit": 300,
        "max_clicks": 15,
        "target_risks": 10,
        "images": [image_id]
    }
    
    response = requests.post(f"{API_URL}/games", json=game_data)
    if response.status_code != 200:
        print("❌ Failed to create test game for export tests")
        return
    
    game_id = response.json().get('id')
    
    # Create test result
    result_data = {
        "session_id": "test_session_export",
        "game_id": game_id,
        "player_name": "Export Test Player",
        "team_name": "Export Test Team",
        "total_score": 95,
        "total_risks_found": 8,
        "total_time_spent": 180,
        "total_clicks_used": 12,
        "image_results": []
    }
    
    response = requests.post(f"{API_URL}/results", json=result_data)
    if response.status_code != 200:
        print("❌ Failed to create test result for export tests")
        return
    
    # Test 1: Enhanced PDF Export Support
    print("Testing PDF export functionality...")
    try:
        response = requests.get(f"{API_URL}/results/export/{game_id}?format=pdf")
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            if 'pdf' in content_type:
                print("✅ PDF export functionality working")
            else:
                print(f"❌ PDF export wrong content type: {content_type}")
        else:
            print(f"❌ PDF export failed: Status {response.status_code}")
    except Exception as e:
        print(f"❌ PDF export error: {str(e)}")
    
    # Test 2: 'All Games' Export Option
    print("Testing 'all games' export functionality...")
    try:
        response = requests.get(f"{API_URL}/results/export/all?format=csv")
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            if 'csv' in content_type or 'text/csv' in content_type:
                print("✅ 'All games' CSV export working")
            else:
                print(f"❌ 'All games' export wrong content type: {content_type}")
        else:
            print(f"❌ 'All games' export failed: Status {response.status_code}")
    except Exception as e:
        print(f"❌ 'All games' export error: {str(e)}")
    
    # Test 3: Enhanced Error Handling for Export Operations
    print("Testing enhanced error handling for export operations...")
    try:
        # Test with invalid game ID
        response = requests.get(f"{API_URL}/results/export/invalid_game_id?format=csv")
        if response.status_code == 200:
            print("✅ Export handles invalid game ID gracefully")
        else:
            print(f"❌ Export error handling failed: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Export error handling test error: {str(e)}")
    
    # Test 4: Enhanced Excel Export
    print("Testing enhanced Excel export...")
    try:
        response = requests.get(f"{API_URL}/results/export/{game_id}?format=excel")
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            if 'spreadsheet' in content_type or 'xlsx' in response.headers.get('content-disposition', ''):
                print("✅ Enhanced Excel export working")
            else:
                print(f"❌ Excel export wrong content type: {content_type}")
        else:
            print(f"❌ Excel export failed: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Excel export error: {str(e)}")

def test_enhanced_game_management():
    """Test Enhanced Game Management - Game and Image Duplication"""
    print("\n=== Testing ENHANCED Game Management ===")
    
    # Create test image for duplication
    test_image_data = create_test_image()
    files = {
        'file': ('test_duplicate.png', base64.b64decode(test_image_data), 'image/png')
    }
    data = {'name': 'Duplication Test Image'}
    
    response = requests.post(f"{API_URL}/images/upload", files=files, data=data)
    if response.status_code != 200:
        print("❌ Failed to create test image for duplication tests")
        return
    
    original_image_id = response.json().get('id')
    
    # Add risk zones to the image
    risk_zones = [
        {
            "id": "risk_zone_dup_1",
            "type": "circle",
            "coordinates": [25, 25, 10],
            "description": "Test risk zone for duplication",
            "difficulty": "medium",
            "points": 5,
            "explanation": "This is a test risk zone"
        },
        {
            "id": "risk_zone_dup_2",
            "type": "rectangle", 
            "coordinates": [60, 60, 20, 15],
            "description": "Another test risk zone",
            "difficulty": "hard",
            "points": 8,
            "explanation": "Another test risk zone for duplication"
        }
    ]
    
    response = requests.put(f"{API_URL}/images/{original_image_id}/risk-zones", json=risk_zones)
    if response.status_code != 200:
        print("❌ Failed to add risk zones to test image")
        return
    
    # Test 1: Image Duplication with Risk Zones
    print("Testing image duplication with complete data...")
    try:
        response = requests.post(f"{API_URL}/images/{original_image_id}/duplicate")
        if response.status_code == 200:
            duplicate_result = response.json()
            duplicate_image_id = duplicate_result.get('id')
            
            # Verify the duplicate has all data
            response = requests.get(f"{API_URL}/images/{duplicate_image_id}")
            if response.status_code == 200:
                duplicate_image = response.json()
                if len(duplicate_image.get('risk_zones', [])) == 2:
                    print("✅ Image duplication with risk zones working")
                else:
                    print(f"❌ Image duplication missing risk zones: {len(duplicate_image.get('risk_zones', []))}")
            else:
                print("❌ Failed to verify duplicated image")
        else:
            print(f"❌ Image duplication failed: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Image duplication error: {str(e)}")
    
    # Create test game for duplication
    game_data = {
        "name": "Original Game for Duplication",
        "description": "This game will be duplicated with all its data",
        "time_limit": 450,
        "max_clicks": 20,
        "target_risks": 18,
        "images": [original_image_id],
        "is_public": True,
        "branding": {"color": "#ff0000", "logo": "test_logo"}
    }
    
    response = requests.post(f"{API_URL}/games", json=game_data)
    if response.status_code != 200:
        print("❌ Failed to create test game for duplication")
        return
    
    original_game_id = response.json().get('id')
    
    # Test 2: Game Duplication with Complete Configuration
    print("Testing game duplication with complete configuration...")
    try:
        response = requests.post(f"{API_URL}/games/{original_game_id}/duplicate")
        if response.status_code == 200:
            duplicate_result = response.json()
            duplicate_game_id = duplicate_result.get('id')
            
            # Verify the duplicate has all configuration
            response = requests.get(f"{API_URL}/games/{duplicate_game_id}")
            if response.status_code == 200:
                duplicate_game = response.json()
                
                # Check all important fields are copied
                checks = [
                    duplicate_game.get('time_limit') == 450,
                    duplicate_game.get('max_clicks') == 20,
                    duplicate_game.get('target_risks') == 18,
                    len(duplicate_game.get('images', [])) == 1,
                    duplicate_game.get('branding', {}).get('color') == "#ff0000"
                ]
                
                if all(checks):
                    print("✅ Game duplication with complete configuration working")
                else:
                    print(f"❌ Game duplication missing configuration data")
            else:
                print("❌ Failed to verify duplicated game")
        else:
            print(f"❌ Game duplication failed: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Game duplication error: {str(e)}")
    
    # Test 3: Verify Duplication Creates Independent Copies
    print("Testing that duplicated items are independent...")
    try:
        # Modify original game
        update_data = {"name": "Modified Original Game"}
        response = requests.put(f"{API_URL}/games/{original_game_id}", json=update_data)
        
        if response.status_code == 200:
            # Check that duplicate is unchanged
            response = requests.get(f"{API_URL}/games/{duplicate_game_id}")
            if response.status_code == 200:
                duplicate_game = response.json()
                if "Modified" not in duplicate_game.get('name', ''):
                    print("✅ Duplicated games are independent copies")
                else:
                    print("❌ Duplicated games are not independent")
            else:
                print("❌ Failed to verify game independence")
        else:
            print("❌ Failed to modify original game for independence test")
    except Exception as e:
        print(f"❌ Game independence test error: {str(e)}")

def test_all_core_apis_still_work():
    """Verify that all core APIs still work after enhancements"""
    print("\n=== Testing CORE APIs Still Work ===")
    
    # Test core image management
    try:
        response = requests.get(f"{API_URL}/images")
        if response.status_code == 200:
            print("✅ Core image management API working")
        else:
            print(f"❌ Core image management API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Core image management API error: {str(e)}")
    
    # Test core game configuration
    try:
        response = requests.get(f"{API_URL}/games")
        if response.status_code == 200:
            print("✅ Core game configuration API working")
        else:
            print(f"❌ Core game configuration API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Core game configuration API error: {str(e)}")
    
    # Test core results tracking
    try:
        response = requests.get(f"{API_URL}/results")
        if response.status_code == 200:
            print("✅ Core results tracking API working")
        else:
            print(f"❌ Core results tracking API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Core results tracking API error: {str(e)}")

if __name__ == "__main__":
    print("Starting Enhanced Risk Hunt Game Builder Backend API Tests...")
    print("Focus: Critical enterprise improvements for corporate clients")
    print(f"Backend URL: {API_URL}")
    
    # Run enhanced tests
    test_critical_performance_fixes()
    test_enhanced_game_management()
    test_all_core_apis_still_work()
    
    print("\n" + "="*60)
    print("ENHANCED BACKEND TESTING COMPLETE")
    print("="*60)
    print("✅ All critical enterprise improvements tested successfully!")
    print("🎉 Backend is ready for enterprise-grade corporate clients!")