#!/usr/bin/env python3
"""
Test script for the enhanced MediaAgent with intelligent attachment resolution.
"""

import sys
from media_agent import MediaAgent
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_intelligent_resolution():
    """Test the intelligent attachment resolution with real WordPress content."""
    
    site_url = input("Enter WordPress site URL (e.g., http://www.windsornewmedia.com): ").strip()
    
    if not site_url:
        print("❌ No site URL provided")
        return
    
    print(f"\n🧠 Testing intelligent MediaAgent with: {site_url}")
    print("=" * 60)
    
    try:
        # Initialize MediaAgent (using dummy GCS credentials for testing URL resolution only)
        agent = MediaAgent(
            gcs_credentials_path=None,  # We won't upload, just test resolution
            gcs_bucket_name="test-bucket",
            gcs_folder="test-folder",
            wp_site_url=site_url
        )
        
        # Test cases based on the actual WordPress content we found
        test_cases = [
            {
                "content": '<img src="15" alt="Delicious pasta dish" class="wp-image-15">',
                "context": "Classic Italian Pasta Recipes",
                "broken_id": "15"
            },
            {
                "content": '<img src="18" alt="Beautiful Rome scenery" class="wp-image-18">',
                "context": "A Weekend in Rome",
                "broken_id": "18"
            },
            {
                "content": '<img src="16" alt="WordPress development screenshot" class="wp-image-16">',
                "context": "WordPress Development Tips",
                "broken_id": "16"
            }
        ]
        
        print("🔍 Testing intelligent attachment resolution:")
        print()
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"--- Test Case {i} ---")
            print(f"Broken ID: {test_case['broken_id']}")
            print(f"Context: {test_case['context']}")
            print(f"Content: {test_case['content'][:100]}...")
            
            # Test direct resolution (should fail)
            direct_url = agent.resolve_wp_attachment_id(test_case['broken_id'])
            print(f"Direct resolution: {'✅ ' + direct_url if direct_url else '❌ Failed (expected)'}")
            
            # Test intelligent resolution (should succeed)
            intelligent_url = agent.intelligent_attachment_resolution(test_case['broken_id'], test_case['context'])
            print(f"Intelligent resolution: {'✅ ' + intelligent_url if intelligent_url else '❌ Failed'}")
            
            # Test URL extraction with context
            urls = agent.extract_media_urls(test_case['content'], test_case['context'])
            print(f"Extracted URLs: {urls}")
            print()
        
        print("🎯 Summary:")
        print("- The intelligent resolution should successfully map broken IDs to valid media")
        print("- Context from post titles should help match the right images")
        print("- 'rome' context → rome.jpg, 'pasta'/'italian' → italy/venice images, etc.")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_intelligent_resolution()
