#!/usr/bin/env python3
"""
Debug script to test DeployAgent with more detailed logging.
"""

import sys
import logging
from deploy_agent import DeployAgent, CloudflareDeployment

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_deploy_agent():
    """Test basic deploy agent functionality with detailed debugging."""
    
    print("🧪 Testing DeployAgent with Debug Logging")
    print("=" * 50)
    
    # Get credentials
    api_token = input("Enter Cloudflare API Token: ").strip()
    account_id = input("Enter Cloudflare Account ID: ").strip()
    
    if not api_token or not account_id:
        print("❌ Both API token and account ID are required!")
        return False
    
    try:
        print("\n🔧 Initializing DeployAgent...")
        agent = DeployAgent(api_token, account_id)
        
        print("\n🧪 Test 1: Validate Credentials")
        is_valid = agent.validate_credentials()
        print(f"Credentials valid: {is_valid}")
        
        if not is_valid:
            print("❌ Credential validation failed!")
            return False
        
        print("\n🧪 Test 2: List existing projects")
        projects = agent.cf_api.list_pages_projects()
        print(f"Found {len(projects)} existing projects:")
        for project in projects[:3]:  # Show first 3
            print(f"  - {project.get('name', 'Unknown')}")
        
        print("\n🧪 Test 3: Prepare deployment config")
        config = agent.prepare_deployment_config(
            project_name="test-wp2astro-debug",
            github_repo="user/test-repo"
        )
        print(f"Config created for project: {config.project_name}")
        
        print("\n✅ All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_deploy_agent()
    if not success:
        sys.exit(1)
    
    print("\n🎉 DeployAgent debug test completed successfully!")
