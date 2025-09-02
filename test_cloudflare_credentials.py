#!/usr/bin/env python3
"""
Debug script to test Cloudflare API credentials and permissions.
"""

import requests
import json
import sys

def test_cloudflare_credentials(api_token: str, account_id: str = None):
    """Test Cloudflare API credentials with detailed error reporting."""
    
    print("🔧 Testing Cloudflare API Credentials...")
    print(f"Token (first 10 chars): {api_token[:10]}...")
    if account_id:
        print(f"Account ID: {account_id}")
    print("-" * 50)
    
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    })
    
    # Test 1: Verify token is valid
    print("🧪 Test 1: Token Verification")
    try:
        response = session.get("https://api.cloudflare.com/client/v4/user/tokens/verify")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Token is valid!")
            print(f"Token Status: {data.get('result', {}).get('status', 'Unknown')}")
        else:
            print("❌ Token verification failed!")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Token verification error: {e}")
        return False
    
    # Test 2: List user's accounts
    print("\n🧪 Test 2: Account Access")
    try:
        response = session.get("https://api.cloudflare.com/client/v4/accounts")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            accounts = data.get('result', [])
            print(f"✅ Found {len(accounts)} accounts")
            
            for acc in accounts:
                acc_id = acc.get('id', 'Unknown')
                acc_name = acc.get('name', 'Unknown')
                print(f"  - Account: {acc_name} (ID: {acc_id})")
                
                # If account_id provided, check if it matches
                if account_id and acc_id == account_id:
                    print(f"  ✅ Provided account ID {account_id} found!")
                    
        else:
            print("❌ Account access failed!")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Account access error: {e}")
        return False
    
    # Test 3: Specific account access (if account_id provided)
    if account_id:
        print(f"\n🧪 Test 3: Specific Account Access ({account_id})")
        try:
            response = session.get(f"https://api.cloudflare.com/client/v4/accounts/{account_id}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                account_name = data.get('result', {}).get('name', 'Unknown')
                print(f"✅ Account access successful: {account_name}")
            else:
                print("❌ Specific account access failed!")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Specific account access error: {e}")
            return False
    
    # Test 4: Pages API access
    if account_id:
        print(f"\n🧪 Test 4: Cloudflare Pages API Access")
        try:
            response = session.get(f"https://api.cloudflare.com/client/v4/accounts/{account_id}/pages/projects")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                projects = data.get('result', [])
                print(f"✅ Pages API access successful! Found {len(projects)} projects")
                
                for project in projects[:3]:  # Show first 3 projects
                    project_name = project.get('name', 'Unknown')
                    print(f"  - Project: {project_name}")
                    
            else:
                print("❌ Pages API access failed!")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Pages API access error: {e}")
            return False
    
    print("\n🎉 All tests passed! Credentials are valid and have proper permissions.")
    return True

def main():
    """Main function to run credential tests."""
    print("Cloudflare API Credential Tester")
    print("=" * 50)
    
    # Get credentials from user input
    api_token = input("Enter your Cloudflare API Token: ").strip()
    if not api_token:
        print("❌ API Token is required!")
        sys.exit(1)
    
    account_id = input("Enter your Cloudflare Account ID (optional): ").strip()
    if not account_id:
        account_id = None
    
    print()
    success = test_cloudflare_credentials(api_token, account_id)
    
    if not success:
        print("\n❌ Credential test failed!")
        print("\n💡 Common issues:")
        print("1. Invalid API token - Check token is correct and not expired")
        print("2. Wrong account ID - Use account ID from Cloudflare dashboard")
        print("3. Insufficient permissions - Token needs 'Cloudflare Pages:Edit' permission")
        print("4. Account access - Make sure token has access to the specified account")
        sys.exit(1)
    else:
        print("\n✅ Credentials are working correctly!")

if __name__ == "__main__":
    main()
