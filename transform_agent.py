import html2text
import re
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import logging
from datetime import datetime
from base_agent import BaseAgent, BaseResult, AgentStatus
from content_sanitizer import ContentSanitizer

_sanitizer = ContentSanitizer()

class MarkdownPost(BaseModel):
    """Model for a transformed markdown post."""
    title: str
    content: str
    date: str
    slug: str
    categories: List[str] = []
    tags: List[str] = []
    image: Optional[str] = None

class MarkdownPage(BaseModel):
    """Model for a transformed markdown page."""
    title: str
    content: str
    date: str
    slug: str
    image: Optional[str] = None

class StaticContentBundle(BaseModel):
    """Model for bundled static content."""
    posts: List[MarkdownPost]
    pages: List[MarkdownPage]

class TransformAgent(BaseAgent):
    """Agent for transforming WordPress content to Astro-compatible format."""
    
    def __init__(self, **kwargs):
        """Initialize the transform agent.
        
        Args:
            **kwargs: Additional configuration passed to BaseAgent
        """
        # Initialize base agent first
        agent_name = kwargs.pop('name', 'TransformAgent')
        super().__init__(name=agent_name, **kwargs)
        
        # Set up HTML converter
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        self.html_converter.body_width = 0
        
        # Validate configuration
        self.validate_configuration()
    
    def clean_html_content(self, html_content: str) -> str:
        """Clean and prepare HTML content for conversion."""
        # Remove WordPress-specific shortcodes
        content = re.sub(r'\[.*?\]', '', html_content)
        
        # Clean up extra whitespace
        content = re.sub(r'\n\s*\n', '\n\n', content)
        
        return content.strip()
    
    def sanitize_markdown_content(self, markdown_content: str) -> str:
        """Sanitize markdown content to prevent module import errors.
        
        This function fixes common issues that can cause Astro build errors,
        particularly with image references that might be interpreted as module imports.
        Delegates to the shared ContentSanitizer image rules.
        """
        return _sanitizer.sanitize_image_references(markdown_content)
    
    def html_to_markdown(self, html_content: str) -> str:
        """Convert HTML content to Markdown."""
        cleaned_html = self.clean_html_content(html_content)
        markdown = self.html_converter.handle(cleaned_html)
        
        # Clean up the markdown
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        
        # Sanitize markdown content to prevent module import errors
        markdown = self.sanitize_markdown_content(markdown)
        
        return markdown.strip()
    
    def create_frontmatter(self, title: str, date: str, **kwargs) -> str:
        """Create YAML frontmatter for the markdown file."""
        frontmatter = ["---"]
        # Escape single quotes in title for YAML
        safe_title = title.replace("'", "\\'")
        frontmatter.append(f"title: '{safe_title}'")
        frontmatter.append(f"date: '{date}'")
        frontmatter.append(f"slug: {kwargs.get('slug', '')}")
        
        if kwargs.get('categories'):
            categories = kwargs['categories']
            if categories:
                frontmatter.append("categories:")
                for cat in categories:
                    frontmatter.append(f"- {cat}")
        
        if kwargs.get('tags'):
            tags = kwargs['tags']
            if tags:
                frontmatter.append("tags:")
                for tag in tags:
                    frontmatter.append(f"- {tag}")
        
        if kwargs.get('image'):
            frontmatter.append(f"image: {kwargs['image']}")
        
        frontmatter.append("---")
        return "\n".join(frontmatter)
    
    def transform_post(self, wp_post) -> MarkdownPost:
        """Transform a WordPress post to markdown format."""
        markdown_content = self.html_to_markdown(wp_post.content)
        
        return MarkdownPost(
            title=wp_post.title,
            content=markdown_content,
            date=wp_post.date,
            slug=wp_post.slug,
            categories=wp_post.categories,
            tags=wp_post.tags,
            image=None  # Would need media processing for this
        )
    
    def transform_page(self, wp_page) -> MarkdownPage:
        """Transform a WordPress page to markdown format."""
        markdown_content = self.html_to_markdown(wp_page.content)
        
        return MarkdownPage(
            title=wp_page.title,
            content=markdown_content,
            date=wp_page.date,
            slug=wp_page.slug,
            image=None  # Would need media processing for this
        )
    
    def create_content_files(self, bundle: StaticContentBundle) -> Dict[str, List[Dict[str, str]]]:
        """Create content files structure for the scaffold agent."""
        content_files = {
            "posts": [],
            "pages": []
        }
        
        # Transform posts
        for post in bundle.posts:
            frontmatter = self.create_frontmatter(
                title=post.title,
                date=post.date,
                slug=post.slug,
                categories=post.categories,
                tags=post.tags,
                image=post.image
            )
            
            file_content = f"{frontmatter}\n\n{post.content}"
            content_files["posts"].append({
                "path": f"src/content/blog/{post.slug}.md",
                "content": file_content
            })
        
        # Transform pages
        for page in bundle.pages:
            frontmatter = self.create_frontmatter(
                title=page.title,
                date=page.date,
                slug=page.slug,
                image=page.image
            )
            
            file_content = f"{frontmatter}\n\n{page.content}"
            content_files["pages"].append({
                "path": f"src/content/pages/{page.slug}.md",
                "content": file_content
            })
        
        return content_files
    
    def transform_bundle(self, wp_bundle) -> StaticContentBundle:
        """Transform a complete WordPress content bundle."""
        return self._execute_with_metrics("transform_bundle", self._transform_bundle_impl, wp_bundle).data
    
    def _transform_bundle_impl(self, wp_bundle) -> StaticContentBundle:
        """Implementation of bundle transformation."""
        self.logger.info("Transforming WordPress content to markdown...")
        
        posts = [self.transform_post(post) for post in wp_bundle.posts]
        pages = [self.transform_page(page) for page in wp_bundle.pages]
        
        bundle = StaticContentBundle(posts=posts, pages=pages)
        self.logger.info(f"Transformed {len(posts)} posts and {len(pages)} pages")
        
        return bundle
    
    def process(self, wp_bundle, *args, **kwargs) -> BaseResult:
        """Main processing method - transforms WordPress content to markdown."""
        try:
            self.validate_input(wp_bundle)
            bundle = self.transform_bundle(wp_bundle)
            
            return BaseResult(
                success=True,
                status=AgentStatus.SUCCESS,
                data=bundle,
                message=f"Successfully transformed {len(bundle.posts)} posts and {len(bundle.pages)} pages"
            )
        except Exception as e:
            return BaseResult(
                success=False,
                status=AgentStatus.ERROR,
                error=str(e),
                message="Failed to transform WordPress content"
            )
    
    def validate_configuration(self) -> bool:
        """Validate the agent's configuration."""
        # TransformAgent doesn't require external dependencies, so basic validation
        if not hasattr(self, 'html_converter'):
            raise ValueError("HTML converter not initialized")
        
        return True

def transform_bundle(wp_bundle) -> StaticContentBundle:
    """Transform WordPress content bundle to static content.
    
    Args:
        wp_bundle: WordPress content bundle
        
    Returns:
        StaticContentBundle with transformed content
    """
    agent = TransformAgent()
    return agent.transform_bundle(wp_bundle)
