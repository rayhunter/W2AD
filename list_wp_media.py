#!/usr/bin/env python3
"""
List all WordPress media attachments to see what's actually available
"""
import requests

def list_wordpress_media(site_url):
    """List all WordPress media attachments"""
    
    print(f"🔍 Listing WordPress media from: {site_url}")
    print("=" * 60)
    
    api_base = f"{site_url.rstrip('/')}/wp-json/wp/v2"
    
    try:
        # Get all media attachments
        print("📸 Fetching media attachments...")
        response = requests.get(f"{api_base}/media", params={"per_page": 20})
        response.raise_for_status()
        
        media_items = response.json()
        print(f"✅ Found {len(media_items)} media attachments")
        
        if not media_items:
            print("❌ No media attachments found in WordPress")
            return
        
        for i, media in enumerate(media_items):
            print(f"\n--- Media {i+1} ---")
            print(f"ID: {media['id']}")
            print(f"Title: {media.get('title', {}).get('rendered', 'No title')}")
            print(f"Source URL: {media.get('source_url', 'No URL')}")
            print(f"MIME Type: {media.get('mime_type', 'Unknown')}")
            print(f"Upload Date: {media.get('date', 'Unknown')}")
            
            # Show media details
            media_details = media.get('media_details', {})
            if media_details:
                print(f"File: {media_details.get('file', 'Unknown')}")
                if 'sizes' in media_details:
                    sizes = media_details['sizes']
                    print(f"Available sizes: {list(sizes.keys())}")
    
    except Exception as e:
        print(f"❌ Error listing media: {e}")

if __name__ == "__main__":
    site_url = "http://www.windsornewmedia.com"
    list_wordpress_media(site_url)
