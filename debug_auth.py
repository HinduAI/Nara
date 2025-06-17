#!/usr/bin/env python3
"""
Debug script to test Supabase authentication
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_environment_variables():
    """Test if all required environment variables are set"""
    print("=== Environment Variables Check ===")
    
    required_vars = {
        'SUPABASE_URL': 'Backend Supabase URL',
        'SUPABASE_SERVICE_KEY': 'Backend Supabase Service Key',
        'REACT_APP_SUPABASE_URL': 'Frontend Supabase URL', 
        'REACT_APP_SUPABASE_ANON_KEY': 'Frontend Supabase Anon Key'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {description}: {'*' * 10} (length: {len(value)})")
        else:
            print(f"❌ {description}: MISSING")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing environment variables: {missing_vars}")
        return False
    else:
        print("\n✅ All environment variables are set")
        return True

def test_api_health():
    """Test if the API is running"""
    print("\n=== API Health Check ===")
    
    backend_url = os.getenv('REACT_APP_API_URL', 'http://localhost:8000')
    
    try:
        response = requests.get(f"{backend_url}/api/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ API is running at {backend_url}")
            return True
        else:
            print(f"❌ API returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to API at {backend_url}: {e}")
        return False

def test_supabase_connection():
    """Test Supabase connection"""
    print("\n=== Supabase Connection Test ===")
    
    supabase_url = os.getenv('SUPABASE_URL')
    if not supabase_url:
        print("❌ SUPABASE_URL not set")
        return False
    
    try:
        # Test basic connection to Supabase
        response = requests.get(f"{supabase_url}/rest/v1/", timeout=10)
        if response.status_code in [200, 401, 403]:  # These are expected responses
            print(f"✅ Supabase is accessible at {supabase_url}")
            return True
        else:
            print(f"❌ Unexpected response from Supabase: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to Supabase: {e}")
        return False

def main():
    print("🔍 HinduAI Authentication Debug Tool\n")
    
    # Test environment variables
    env_ok = test_environment_variables()
    
    # Test API health
    api_ok = test_api_health()
    
    # Test Supabase connection
    supabase_ok = test_supabase_connection()
    
    print("\n=== Summary ===")
    if env_ok and api_ok and supabase_ok:
        print("✅ All basic checks passed")
        print("\nNext steps:")
        print("1. Make sure you're logged in to the frontend")
        print("2. Check browser console for authentication errors")
        print("3. Test the /api/auth-test endpoint with your token")
    else:
        print("❌ Some checks failed")
        print("\nFix the issues above before testing authentication")

if __name__ == "__main__":
    main() 