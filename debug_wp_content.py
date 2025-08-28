#!/usr/bin/env python3
"""
Debug script to inspect WordPress content and image extraction
"""
import requests
import re

def inspect_wordpress_content(site_url, post_id=None):
    """Inspect WordPress content to see what images are available"""
    
    print(f"🔍 Inspecting WordPress content from: {site_url}")
    print("=" * 60)
    
    api_base = f"{site_url.rstrip('/')}/wp-json/wp/v2"
    
    try:
        # Get posts
        print("📄 Fetching posts...")
        posts_response = requests.get(f"{api_base}/posts", params={"per_page": 3})
        posts_response.raise_for_status()
        posts = posts_response.json()
        
        print(f"✅ Found {len(posts)} posts")
        
        for i, post in enumerate(posts):
            print(f"\n--- Post {i+1}: {post['title']['rendered']} ---")
            content = post['content']['rendered']
            
            # Look for images in content
            img_tags = re.findall(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', content, re.IGNORECASE)
            md_images = re.findall(r'!\[[^\]]*\]\(([^)]+)\)', content)
            
            print(f"📸 IMG tags found: {len(img_tags)}")
            for img in img_tags[:3]:  # Show first 3
                print(f"   • {img}")
            
            print(f"📸 Markdown images found: {len(md_images)}")
            for img in md_images[:3]:  # Show first 3
                print(f"   • {img}")
            
            # Look for any URLs that might be images
            all_urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', content)
            image_urls = [url for url in all_urls if any(url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])]
            
            print(f"🔗 Image URLs found: {len(image_urls)}")
            for img in image_urls[:3]:  # Show first 3
                print(f"   • {img}")
            
            # Show content sample
            print(f"📝 Content sample (first 300 chars):")
            print(f"   {content[:300]}...")
            
            if i == 0:  # Show full content for first post
                print(f"\n📄 Full content of first post:")
                print("-" * 40)
                print(content)
                print("-" * 40)
        
        # Get pages
        print(f"\n📄 Fetching pages...")
        pages_response = requests.get(f"{api_base}/pages", params={"per_page": 2})
        pages_response.raise_for_status()
        pages = pages_response.json()
        
        print(f"✅ Found {len(pages)} pages")
        
        for i, page in enumerate(pages):
            print(f"\n--- Page {i+1}: {page['title']['rendered']} ---")
            content = page['content']['rendered']
            
            # Look for images
            img_tags = re.findall(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', content, re.IGNORECASE)
            
            print(f"📸 IMG tags found: {len(img_tags)}")
            for img in img_tags[:3]:
                print(f"   • {img}")
            
            # Show full page content for debugging
            print(f"📄 Full page content:")
            print("-" * 40)
            print(content)
            print("-" * 40)
        
    except Exception as e:
        print(f"❌ Error inspecting WordPress content: {e}")

if __name__ == "__main__":
    site_url = input("Enter WordPress site URL: ").strip()
    if not site_url:
        print("❌ No site URL provided")
        exit(1)
    
    inspect_wordpress_content(site_url)
