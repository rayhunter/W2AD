import requests
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class WPPost(BaseModel):
    """Model for a WordPress post."""
    id: int
    title: str
    content: str
    excerpt: str
    date: str
    slug: str
    status: str
    categories: List[str] = []
    tags: List[str] = []
    featured_media: Optional[int] = None

class WPPage(BaseModel):
    """Model for a WordPress page."""
    id: int
    title: str
    content: str
    date: str
    slug: str
    status: str
    featured_media: Optional[int] = None

class WPContentBundle(BaseModel):
    """Model for bundled WordPress content."""
    posts: List[WPPost]
    pages: List[WPPage]
    media: List[Dict[str, Any]] = []
    site_info: Dict[str, Any] = {}

class ExtractionAgent:
    """Agent for extracting content from WordPress sites via REST API."""
    
    def __init__(self, site_url: str, username: str = None, password: str = None):
        """Initialize the extraction agent.
        
        Args:
            site_url: WordPress site URL
            username: Optional username for authentication
            password: Optional password for authentication
        """
        self.site_url = site_url.rstrip('/')
        self.api_base = f"{self.site_url}/wp-json/wp/v2"
        self.auth = (username, password) if username and password else None
        logger.info(f"Initialized ExtractionAgent for {site_url}")
    
    def extract_posts(self, per_page: int = 100) -> List[WPPost]:
        """Extract blog posts from WordPress."""
        logger.info("Extracting WordPress posts...")
        
        try:
            response = requests.get(
                f"{self.api_base}/posts",
                params={"per_page": per_page, "status": "publish"},
                auth=self.auth
            )
            response.raise_for_status()
            
            posts_data = response.json()
            posts = []
            
            for post_data in posts_data:
                post = WPPost(
                    id=post_data["id"],
                    title=post_data["title"]["rendered"],
                    content=post_data["content"]["rendered"],
                    excerpt=post_data["excerpt"]["rendered"],
                    date=post_data["date"],
                    slug=post_data["slug"],
                    status=post_data["status"],
                    categories=[],  # Would need additional API calls to populate
                    tags=[],        # Would need additional API calls to populate
                    featured_media=post_data.get("featured_media")
                )
                posts.append(post)
            
            logger.info(f"Extracted {len(posts)} posts")
            return posts
            
        except Exception as e:
            logger.error(f"Failed to extract posts: {str(e)}")
            return []
    
    def extract_pages(self, per_page: int = 100) -> List[WPPage]:
        """Extract pages from WordPress."""
        logger.info("Extracting WordPress pages...")
        
        try:
            response = requests.get(
                f"{self.api_base}/pages",
                params={"per_page": per_page, "status": "publish"},
                auth=self.auth
            )
            response.raise_for_status()
            
            pages_data = response.json()
            pages = []
            
            for page_data in pages_data:
                page = WPPage(
                    id=page_data["id"],
                    title=page_data["title"]["rendered"],
                    content=page_data["content"]["rendered"],
                    date=page_data["date"],
                    slug=page_data["slug"],
                    status=page_data["status"],
                    featured_media=page_data.get("featured_media")
                )
                pages.append(page)
            
            logger.info(f"Extracted {len(pages)} pages")
            return pages
            
        except Exception as e:
            logger.error(f"Failed to extract pages: {str(e)}")
            return []
    
    def extract_site_info(self) -> Dict[str, Any]:
        """Extract site information."""
        try:
            response = requests.get(f"{self.site_url}/wp-json")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to extract site info: {str(e)}")
            return {}
    
    def extract_all(self) -> WPContentBundle:
        """Extract all content from the WordPress site."""
        logger.info("Starting full content extraction...")
        
        posts = self.extract_posts()
        pages = self.extract_pages()
        site_info = self.extract_site_info()
        
        bundle = WPContentBundle(
            posts=posts,
            pages=pages,
            site_info=site_info
        )
        
        logger.info(f"Extraction completed: {len(posts)} posts, {len(pages)} pages")
        return bundle

def extract_from_wordpress(site_url: str, username: str = None, password: str = None) -> WPContentBundle:
    """Extract content from a WordPress site.
    
    Args:
        site_url: WordPress site URL
        username: Optional username for authentication
        password: Optional password for authentication
        
    Returns:
        WPContentBundle containing all extracted content
    """
    agent = ExtractionAgent(site_url, username, password)
    return agent.extract_all()
