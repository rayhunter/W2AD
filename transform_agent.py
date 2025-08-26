import html2text
import re
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

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

class TransformAgent:
    """Agent for transforming WordPress content to Astro-compatible format."""
    
    def __init__(self):
        """Initialize the transform agent."""
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        self.html_converter.body_width = 0
        logger.info("Initialized TransformAgent")
    
    def clean_html_content(self, html_content: str) -> str:
        """Clean and prepare HTML content for conversion."""
        # Remove WordPress-specific shortcodes
        content = re.sub(r'\[.*?\]', '', html_content)
        
        # Clean up extra whitespace
        content = re.sub(r'\n\s*\n', '\n\n', content)
        
        return content.strip()
    
    def html_to_markdown(self, html_content: str) -> str:
        """Convert HTML content to Markdown."""
        cleaned_html = self.clean_html_content(html_content)
        markdown = self.html_converter.handle(cleaned_html)
        
        # Clean up the markdown
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
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
        logger.info("Transforming WordPress content to markdown...")
        
        posts = [self.transform_post(post) for post in wp_bundle.posts]
        pages = [self.transform_page(page) for page in wp_bundle.pages]
        
        bundle = StaticContentBundle(posts=posts, pages=pages)
        logger.info(f"Transformed {len(posts)} posts and {len(pages)} pages")
        
        return bundle

def transform_bundle(wp_bundle) -> StaticContentBundle:
    """Transform WordPress content bundle to static content.
    
    Args:
        wp_bundle: WordPress content bundle
        
    Returns:
        StaticContentBundle with transformed content
    """
    agent = TransformAgent()
    return agent.transform_bundle(wp_bundle)
