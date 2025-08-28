#!/usr/bin/env python3
"""
Test script to debug WordPress attachment ID resolution
"""
import requests

def test_attachment_resolution(site_url, attachment_ids):
    """Test resolving WordPress attachment IDs to URLs"""
    
    print(f"🔍 Testing attachment resolution for: {site_url}")
    print("=" * 60)
    
    api_base = f"{site_url.rstrip('/')}/wp-json/wp/v2"
    
    for attachment_id in attachment_ids:
        print(f"\n📸 Testing attachment ID: {attachment_id}")
        try:
            url = f"{api_base}/media/{attachment_id}"
            print(f"   API URL: {url}")
            
            response = requests.get(url)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                media_data = response.json()
                source_url = media_data.get('source_url')
                title = media_data.get('title', {}).get('rendered', 'No title')
                
                print(f"   ✅ Success!")
                print(f"   Title: {title}")
                print(f"   Source URL: {source_url}")
                
                # Test if the image file is actually accessible
                if source_url:
                    try:
                        img_response = requests.head(source_url, timeout=10)
                        print(f"   Image accessible: {img_response.status_code == 200}")
                        if img_response.status_code == 200:
                            print(f"   Content-Type: {img_response.headers.get('content-type', 'unknown')}")
                            print(f"   Content-Length: {img_response.headers.get('content-length', 'unknown')} bytes")
                    except Exception as e:
                        print(f"   ❌ Image not accessible: {e}")
            else:
                print(f"   ❌ Failed: {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    site_url = "http://www.windsornewmedia.com"
    attachment_ids = ["15", "16", "18"]  # The IDs we found in the debug
    
    test_attachment_resolution(site_url, attachment_ids)
