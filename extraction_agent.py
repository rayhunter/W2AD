import requests
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import logging
from datetime import datetime
from base_agent import BaseAgent, BaseResult, AgentStatus

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
    featured_image: Optional[str] = None

class WPPage(BaseModel):
    """Model for a WordPress page."""
    id: int
    title: str
    content: str
    date: str
    slug: str
    status: str
    featured_media: Optional[int] = None
    featured_image: Optional[str] = None

def get_featured_image_url(item_data: Dict[str, Any]) -> Optional[str]:
    """Get the featured image URL from a post/page fetched with _embed=wp:featuredmedia."""
    embedded = item_data.get("_embedded", {}).get("wp:featuredmedia") or []
    if embedded and isinstance(embedded[0], dict):
        return embedded[0].get("source_url")
    return None

class WPContentBundle(BaseModel):
    """Model for bundled WordPress content."""
    posts: List[WPPost]
    pages: List[WPPage]
    media: List[Dict[str, Any]] = []
    site_info: Dict[str, Any] = {}

class ExtractionAgent(BaseAgent):
    """Agent for extracting content from WordPress sites via REST API."""
    
    def __init__(self, site_url: str, username: str = None, password: str = None, **kwargs):
        """Initialize the extraction agent.
        
        Args:
            site_url: WordPress site URL
            username: Optional username for authentication
            password: Optional password for authentication
            **kwargs: Additional configuration passed to BaseAgent
        """
        # Initialize base agent first
        agent_name = kwargs.pop('name', 'ExtractionAgent')
        super().__init__(name=agent_name, site_url=site_url, username=username, **kwargs)
        
        # Set up WordPress-specific configuration
        self.site_url = site_url.rstrip('/')
        self.api_base = f"{self.site_url}/wp-json/wp/v2"
        self.auth = (username, password) if username and password else None
        
        # Validate configuration
        self.validate_configuration()
    
    def _unwrap(self, result) -> Any:
        """Return the data from a BaseResult, raising if the operation failed.

        _execute_with_metrics swallows exceptions into a failed BaseResult.
        For extraction that must not turn into an empty migration, so re-raise.
        """
        if not result.success:
            raise RuntimeError(result.error or result.message or "Extraction failed")
        return result.data

    def _fetch_all_pages(self, endpoint: str, per_page: int = 100) -> List[Dict[str, Any]]:
        """Fetch every item from a paginated WP REST endpoint.

        Follows the X-WP-TotalPages header so sites with more than `per_page`
        items are fully extracted.
        """
        items: List[Dict[str, Any]] = []
        page = 1
        total_pages = 1

        while page <= total_pages:
            response = requests.get(
                f"{self.api_base}/{endpoint}",
                params={"per_page": per_page, "status": "publish", "page": page, "_embed": "wp:featuredmedia"},
                auth=self.auth,
                timeout=30
            )
            response.raise_for_status()

            batch = response.json()
            if not isinstance(batch, list):
                raise RuntimeError(f"Unexpected response from {endpoint} (page {page}): {str(batch)[:200]}")
            items.extend(batch)

            try:
                total_pages = int(response.headers.get("X-WP-TotalPages", total_pages))
            except ValueError:
                total_pages = page

            self.logger.debug(f"Fetched {endpoint} page {page}/{total_pages} ({len(batch)} items)")

            if not batch:
                break
            page += 1

        return items

    def extract_posts(self, per_page: int = 100) -> List[WPPost]:
        """Extract blog posts from WordPress. Raises on API failure."""
        return self._unwrap(self._execute_with_metrics("extract_posts", self._extract_posts_impl, per_page))

    def _extract_posts_impl(self, per_page: int = 100) -> List[WPPost]:
        """Implementation of post extraction."""
        self.logger.info("Extracting WordPress posts...")

        posts_data = self._fetch_all_pages("posts", per_page)
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
                featured_media=post_data.get("featured_media"),
                featured_image=get_featured_image_url(post_data)
            )
            posts.append(post)
        
        self.logger.info(f"Extracted {len(posts)} posts")
        return posts
    
    def extract_pages(self, per_page: int = 100) -> List[WPPage]:
        """Extract pages from WordPress. Raises on API failure."""
        return self._unwrap(self._execute_with_metrics("extract_pages", self._extract_pages_impl, per_page))

    def _extract_pages_impl(self, per_page: int = 100) -> List[WPPage]:
        """Implementation of page extraction."""
        self.logger.info("Extracting WordPress pages...")

        pages_data = self._fetch_all_pages("pages", per_page)
        pages = []
        
        for page_data in pages_data:
            page = WPPage(
                id=page_data["id"],
                title=page_data["title"]["rendered"],
                content=page_data["content"]["rendered"],
                date=page_data["date"],
                slug=page_data["slug"],
                status=page_data["status"],
                featured_media=page_data.get("featured_media"),
                featured_image=get_featured_image_url(page_data)
            )
            pages.append(page)
        
        self.logger.info(f"Extracted {len(pages)} pages")
        return pages
    
    def extract_site_info(self) -> Dict[str, Any]:
        """Extract site information. Non-fatal: returns {} if unavailable."""
        result = self._execute_with_metrics("extract_site_info", self._extract_site_info_impl)
        if not result.success:
            self.logger.warning(f"Could not fetch site info, continuing without it: {result.error}")
            return {}
        return result.data or {}

    def _extract_site_info_impl(self) -> Dict[str, Any]:
        """Implementation of site info extraction."""
        response = requests.get(f"{self.site_url}/wp-json", auth=self.auth, timeout=30)
        response.raise_for_status()
        return response.json()

    def extract_all(self) -> WPContentBundle:
        """Extract all content from the WordPress site. Raises on API failure."""
        return self._unwrap(self._execute_with_metrics("extract_all", self._extract_all_impl))
    
    def _extract_all_impl(self) -> WPContentBundle:
        """Implementation of full content extraction."""
        self.logger.info("Starting full content extraction...")
        
        posts = self.extract_posts()
        pages = self.extract_pages()
        site_info = self.extract_site_info()
        
        bundle = WPContentBundle(
            posts=posts,
            pages=pages,
            site_info=site_info
        )
        
        self.logger.info(f"Extraction completed: {len(posts)} posts, {len(pages)} pages")
        return bundle
    
    def process(self, *args, **kwargs) -> BaseResult:
        """Main processing method - extracts all content from WordPress."""
        try:
            bundle = self.extract_all()
            return BaseResult(
                success=True,
                status=AgentStatus.SUCCESS,
                data=bundle,
                message=f"Successfully extracted {len(bundle.posts)} posts and {len(bundle.pages)} pages"
            )
        except Exception as e:
            return BaseResult(
                success=False,
                status=AgentStatus.ERROR,
                error=str(e),
                message="Failed to extract WordPress content"
            )
    
    def validate_configuration(self) -> bool:
        """Validate the agent's configuration."""
        if not self.site_url:
            raise ValueError("Site URL is required")
        
        if not self.site_url.startswith(('http://', 'https://')):
            raise ValueError("Site URL must start with http:// or https://")
        
        # Test connection to WordPress API (GET, not HEAD: many hosts reject HEAD)
        try:
            response = requests.get(f"{self.api_base}", auth=self.auth, timeout=10)
            if response.status_code >= 400:
                raise ValueError(
                    f"WordPress API not accessible at {self.api_base} (HTTP {response.status_code})"
                )
        except requests.RequestException as e:
            raise ValueError(f"Cannot connect to WordPress API: {str(e)}")
        
        return True

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
