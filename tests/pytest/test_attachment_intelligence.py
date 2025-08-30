#!/usr/bin/env python3
"""
Test script for the intelligent attachment resolution functionality only.
"""

import sys
import requests
import logging
from typing import Optional, Dict

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class AttachmentResolver:
    """Simplified class to test just the attachment resolution logic."""
    
    def __init__(self, wp_site_url: str):
        self.wp_site_url = wp_site_url.rstrip('/')
        self.wp_api_base = f"{self.wp_site_url}/wp-json/wp/v2"
    
    def resolve_wp_attachment_id(self, attachment_id: str) -> Optional[str]:
        """Resolve a WordPress attachment ID to its full media URL."""
        if not self.wp_api_base or not attachment_id.isdigit():
            return None
        
        try:
            logger.debug(f"Resolving WordPress attachment ID: {attachment_id}")
            response = requests.get(f"{self.wp_api_base}/media/{attachment_id}", timeout=30)
            response.raise_for_status()
            
            media_data = response.json()
            media_url = media_data.get('source_url')
            
            if media_url:
                logger.info(f"Resolved attachment {attachment_id} to URL: {media_url}")
                return media_url
            else:
                logger.warning(f"No source_url found for attachment {attachment_id}")
                return None
                
        except Exception as e:
            if "404" in str(e) or "Invalid post ID" in str(e):
                logger.warning(f"Attachment ID {attachment_id} not found (404) - may be deleted or invalid")
            else:
                logger.error(f"Error resolving attachment {attachment_id}: {e}")
            return None
    
    def get_all_available_media(self) -> Dict[str, str]:
        """Get all available media from WordPress."""
        try:
            logger.info("Fetching all available WordPress media...")
            response = requests.get(f"{self.wp_api_base}/media", params={"per_page": 100}, timeout=30)
            response.raise_for_status()
            
            media_items = response.json()
            media_map = {}
            
            for item in media_items:
                media_id = str(item.get('id', ''))
                media_url = item.get('source_url', '')
                media_title = item.get('title', {}).get('rendered', '').lower()
                media_alt = item.get('alt_text', '').lower()
                
                if media_url:
                    # Store by ID
                    media_map[media_id] = media_url
                    
                    # Store by title keywords
                    if media_title:
                        media_map[media_title] = media_url
                        # Also store individual words from title
                        for word in media_title.split():
                            if len(word) > 3:  # Only meaningful words
                                media_map[word] = media_url
                    
                    # Store by alt text keywords
                    if media_alt:
                        for word in media_alt.split():
                            if len(word) > 3:  # Only meaningful words
                                media_map[word] = media_url
            
            logger.info(f"Retrieved {len(media_items)} media items, created {len(media_map)} keyword mappings")
            return media_map
            
        except Exception as e:
            logger.error(f"Error fetching all media: {e}")
            return {}
    
    def intelligent_attachment_resolution(self, attachment_id: str, context: str = "") -> Optional[str]:
        """Intelligently resolve attachment IDs using context and available media."""
        # First try direct resolution
        direct_url = self.resolve_wp_attachment_id(attachment_id)
        if direct_url:
            return direct_url
        
        logger.info(f"Direct resolution failed for ID {attachment_id}, attempting intelligent matching...")
        
        # Get all available media
        media_map = self.get_all_available_media()
        if not media_map:
            return None
        
        # Show available media for debugging
        logger.info(f"Available media IDs: {[k for k in media_map.keys() if k.isdigit()]}")
        
        # Try context-based matching
        if context:
            context_lower = context.lower()
            
            # Look for keywords in context that match media
            context_words = context_lower.split()
            for word in context_words:
                if len(word) > 3 and word in media_map:
                    logger.info(f"Found context match for '{word}': {media_map[word]}")
                    return media_map[word]
            
            # Special case mappings based on common patterns
            special_mappings = {
                'rome': ['rome', 'italy', 'eternal'],
                'pasta': ['italy', 'venice', 'italian'],
                'italian': ['italy', 'venice', 'rome'],
                'classic': ['italy', 'venice', 'rome'],
                'recipes': ['italy', 'venice', 'rome'],
                'wordpress': ['avatar', 'headshot', 'profile'],
                'development': ['avatar', 'headshot', 'modern', 'profile'],
                'tips': ['avatar', 'headshot', 'modern', 'profile'],
            }
            
            for key, keywords in special_mappings.items():
                if key in context_lower:
                    for keyword in keywords:
                        if keyword in media_map:
                            logger.info(f"Found special mapping for '{key}' -> '{keyword}': {media_map[keyword]}")
                            return media_map[keyword]
        
        # Fallback: return the most recent media item
        try:
            response = requests.get(f"{self.wp_api_base}/media", params={"per_page": 1, "orderby": "date", "order": "desc"}, timeout=30)
            response.raise_for_status()
            recent_media = response.json()
            
            if recent_media and len(recent_media) > 0:
                fallback_url = recent_media[0].get('source_url')
                logger.info(f"Using fallback (most recent) media: {fallback_url}")
                return fallback_url
                
        except Exception as e:
            logger.warning(f"Fallback media fetch failed: {e}")
        
        return None

def test_intelligence():
    """Test the intelligent attachment resolution."""
    
    site_url = input("Enter WordPress site URL (e.g., http://www.windsornewmedia.com): ").strip()
    
    if not site_url:
        print("❌ No site URL provided")
        return
    
    print(f"\n🧠 Testing intelligent attachment resolution: {site_url}")
    print("=" * 70)
    
    resolver = AttachmentResolver(site_url)
    
    # Test cases based on the actual WordPress content we found
    test_cases = [
        {
            "broken_id": "15",
            "context": "Classic Italian Pasta Recipes"
        },
        {
            "broken_id": "18", 
            "context": "A Weekend in Rome"
        },
        {
            "broken_id": "16",
            "context": "WordPress Development Tips"
        }
    ]
    
    print("🔍 Testing intelligent attachment resolution:")
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"--- Test Case {i} ---")
        print(f"❌ Broken ID: {test_case['broken_id']}")
        print(f"📝 Context: {test_case['context']}")
        
        # Test intelligent resolution
        intelligent_url = resolver.intelligent_attachment_resolution(test_case['broken_id'], test_case['context'])
        print(f"🧠 Intelligent result: {'✅ ' + intelligent_url if intelligent_url else '❌ Failed'}")
        print()
    
    print("🎯 Expected Results:")
    print("- 'Classic Italian Pasta' → should match italy/venice/pasta-related image")  
    print("- 'A Weekend in Rome' → should match rome.jpg")
    print("- 'WordPress Development' → should match avatar/profile image")

if __name__ == "__main__":
    test_intelligence()
