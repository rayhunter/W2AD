#!/usr/bin/env python3
"""
Content Collection Schemas for WP2ASTRO Migration Tool

This module defines Pydantic models for type-safe handling of WordPress content
during migration to Astro. It provides validation, serialization, and transformation
utilities for various content types.

Author: AI Assistant
Date: 2025-08-28
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Literal
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, model_validator
import re
from urllib.parse import urlparse


class ContentStatus(str, Enum):
    """Content status enumeration."""
    PUBLISH = "publish"
    DRAFT = "draft"
    PRIVATE = "private"
    TRASH = "trash"
    INHERIT = "inherit"


class ContentType(str, Enum):
    """Content type enumeration."""
    POST = "post"
    PAGE = "page"
    ATTACHMENT = "attachment"
    REVISION = "revision"
    NAV_MENU_ITEM = "nav_menu_item"
    CUSTOM_CSS = "custom_css"
    CUSTOMIZE_CHANGESET = "customize_changeset"


class MediaType(str, Enum):
    """Media type enumeration."""
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    ARCHIVE = "archive"
    OTHER = "other"


class BaseContent(BaseModel):
    """
    Base content model that all content types inherit from.
    Contains common fields shared across all WordPress content.
    """
    id: int = Field(..., description="WordPress content ID")
    title: str = Field("", description="Content title")
    slug: str = Field("", description="URL slug")
    content: str = Field("", description="Main content body")
    excerpt: str = Field("", description="Content excerpt")
    status: ContentStatus = Field(ContentStatus.PUBLISH, description="Content status")
    type: ContentType = Field(..., description="Content type")
    author_id: int = Field(0, description="Author user ID")
    author_name: str = Field("", description="Author display name")
    date_created: Optional[datetime] = Field(None, description="Creation date")
    date_modified: Optional[datetime] = Field(None, description="Last modification date")
    parent_id: int = Field(0, description="Parent content ID")
    menu_order: int = Field(0, description="Menu order for sorting")
    comment_status: str = Field("closed", description="Comment status")
    ping_status: str = Field("closed", description="Ping status")
    guid: str = Field("", description="Global unique identifier")
    post_name: str = Field("", description="Post name (slug)")
    meta_data: Dict[str, Any] = Field(default_factory=dict, description="Meta data")
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
        extra = "allow"  # Allow extra fields for extensibility
    
    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v, info):
        """Generate slug from title if not provided."""
        if not v and info.data and 'title' in info.data:
            # Create slug from title
            slug = re.sub(r'[^\w\s-]', '', info.data['title'].lower())
            slug = re.sub(r'[-\s]+', '-', slug).strip('-')
            return slug[:50]  # Limit length
        return v
    
    @field_validator('date_created', 'date_modified', mode='before')
    @classmethod
    def parse_dates(cls, v):
        """Parse date strings to datetime objects."""
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                return None
        return v
    
    def to_frontmatter(self) -> Dict[str, Any]:
        """Convert to Astro frontmatter format."""
        frontmatter = {
            'title': self.title,
            'slug': self.slug,
            'draft': self.status != ContentStatus.PUBLISH,
            'pubDate': self.date_created.isoformat() if self.date_created else None,
            'modDate': self.date_modified.isoformat() if self.date_modified else None,
            'author': self.author_name,
        }
        
        # Add excerpt if present
        if self.excerpt:
            frontmatter['description'] = self.excerpt
        
        # Filter out None values
        return {k: v for k, v in frontmatter.items() if v is not None}


class WordPressPost(BaseContent):
    """
    WordPress post model with blog-specific fields.
    """
    type: Literal[ContentType.POST] = Field(ContentType.POST)
    categories: List[str] = Field(default_factory=list, description="Post categories")
    tags: List[str] = Field(default_factory=list, description="Post tags")
    featured_image: Optional[str] = Field(None, description="Featured image URL")
    format: str = Field("standard", description="Post format (standard, aside, gallery, etc.)")
    sticky: bool = Field(False, description="Whether post is sticky")
    
    def to_frontmatter(self) -> Dict[str, Any]:
        """Convert to Astro frontmatter format with post-specific fields."""
        frontmatter = super().to_frontmatter()
        
        # Add post-specific fields
        if self.categories:
            frontmatter['categories'] = self.categories
        if self.tags:
            frontmatter['tags'] = self.tags
        if self.featured_image:
            frontmatter['heroImage'] = self.featured_image
        if self.format != "standard":
            frontmatter['format'] = self.format
        if self.sticky:
            frontmatter['featured'] = True
            
        return frontmatter


class WordPressPage(BaseContent):
    """
    WordPress page model with page-specific fields.
    """
    type: Literal[ContentType.PAGE] = Field(ContentType.PAGE)
    template: str = Field("", description="Page template")
    is_front_page: bool = Field(False, description="Whether this is the front page")
    is_posts_page: bool = Field(False, description="Whether this is the posts page")
    
    def to_frontmatter(self) -> Dict[str, Any]:
        """Convert to Astro frontmatter format with page-specific fields."""
        frontmatter = super().to_frontmatter()
        
        # Add page-specific fields
        if self.template:
            frontmatter['layout'] = self.template
        if self.is_front_page:
            frontmatter['isHome'] = True
        if self.is_posts_page:
            frontmatter['isBlog'] = True
            
        return frontmatter


class MediaAttachment(BaseContent):
    """
    WordPress media attachment model.
    """
    type: Literal[ContentType.ATTACHMENT] = Field(ContentType.ATTACHMENT)
    file_path: str = Field("", description="Original file path")
    file_url: str = Field("", description="File URL")
    file_name: str = Field("", description="File name")
    file_size: int = Field(0, description="File size in bytes")
    mime_type: str = Field("", description="MIME type")
    media_type: MediaType = Field(MediaType.OTHER, description="Media type category")
    alt_text: str = Field("", description="Alternative text")
    caption: str = Field("", description="Media caption")
    description: str = Field("", description="Media description")
    width: Optional[int] = Field(None, description="Image/video width")
    height: Optional[int] = Field(None, description="Image/video height")
    
    @field_validator('media_type')
    @classmethod
    def determine_media_type(cls, v, info):
        """Determine media type from MIME type."""
        if info.data and 'mime_type' in info.data:
            mime = info.data['mime_type'].lower()
            if mime.startswith('image/'):
                return MediaType.IMAGE
            elif mime.startswith('video/'):
                return MediaType.VIDEO
            elif mime.startswith('audio/'):
                return MediaType.AUDIO
            elif mime in ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument']:
                return MediaType.DOCUMENT
            elif mime in ['application/zip', 'application/x-rar-compressed', 'application/x-tar']:
                return MediaType.ARCHIVE
        return MediaType.OTHER
    
    @field_validator('file_name')
    @classmethod
    def extract_file_name(cls, v, info):
        """Extract file name from URL or path."""
        if not v and info.data and 'file_url' in info.data:
            url_path = urlparse(info.data['file_url']).path
            return Path(url_path).name
        return v
    
    def to_frontmatter(self) -> Dict[str, Any]:
        """Convert to Astro frontmatter format for media."""
        frontmatter = {
            'title': self.title or self.file_name,
            'alt': self.alt_text,
            'caption': self.caption,
            'description': self.description,
            'src': self.file_url,
            'type': self.media_type.value,
            'mimeType': self.mime_type,
            'fileSize': self.file_size,
        }
        
        # Add dimensions for images/videos
        if self.width and self.height:
            frontmatter['width'] = self.width
            frontmatter['height'] = self.height
        
        # Filter out empty values
        return {k: v for k, v in frontmatter.items() if v}


class ContentTaxonomy(BaseModel):
    """
    WordPress taxonomy (category/tag) model.
    """
    term_id: int = Field(..., description="Term ID")
    name: str = Field(..., description="Term name")
    slug: str = Field("", description="Term slug")
    description: str = Field("", description="Term description")
    parent_id: int = Field(0, description="Parent term ID")
    count: int = Field(0, description="Number of posts with this term")
    taxonomy: str = Field(..., description="Taxonomy name (category, post_tag, etc.)")
    
    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v, info):
        """Generate slug from name if not provided."""
        if not v and info.data and 'name' in info.data:
            slug = re.sub(r'[^\w\s-]', '', info.data['name'].lower())
            slug = re.sub(r'[-\s]+', '-', slug).strip('-')
            return slug
        return v


class ContentComment(BaseModel):
    """
    WordPress comment model.
    """
    comment_id: int = Field(..., description="Comment ID")
    post_id: int = Field(..., description="Associated post ID")
    author_name: str = Field("", description="Comment author name")
    author_email: str = Field("", description="Comment author email")
    author_url: str = Field("", description="Comment author URL")
    author_ip: str = Field("", description="Comment author IP")
    date: Optional[datetime] = Field(None, description="Comment date")
    content: str = Field("", description="Comment content")
    karma: int = Field(0, description="Comment karma")
    approved: bool = Field(True, description="Whether comment is approved")
    agent: str = Field("", description="User agent string")
    type: str = Field("", description="Comment type")
    parent_id: int = Field(0, description="Parent comment ID")
    user_id: int = Field(0, description="User ID if registered user")
    
    @field_validator('date', mode='before')
    @classmethod
    def parse_date(cls, v):
        """Parse date string to datetime object."""
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                return None
        return v


class ContentCollection(BaseModel):
    """
    A collection of WordPress content with validation and transformation utilities.
    """
    posts: List[WordPressPost] = Field(default_factory=list)
    pages: List[WordPressPage] = Field(default_factory=list)
    media: List[MediaAttachment] = Field(default_factory=list)
    categories: List[ContentTaxonomy] = Field(default_factory=list)
    tags: List[ContentTaxonomy] = Field(default_factory=list)
    comments: List[ContentComment] = Field(default_factory=list)
    
    @property
    def total_content_items(self) -> int:
        """Get total number of content items."""
        return len(self.posts) + len(self.pages) + len(self.media)
    
    @property
    def published_posts(self) -> List[WordPressPost]:
        """Get only published posts."""
        return [post for post in self.posts if post.status == ContentStatus.PUBLISH]
    
    @property
    def published_pages(self) -> List[WordPressPage]:
        """Get only published pages."""
        return [page for page in self.pages if page.status == ContentStatus.PUBLISH]
    
    def get_posts_by_category(self, category: str) -> List[WordPressPost]:
        """Get posts by category."""
        return [post for post in self.posts if category in post.categories]
    
    def get_posts_by_tag(self, tag: str) -> List[WordPressPost]:
        """Get posts by tag."""
        return [post for post in self.posts if tag in post.tags]
    
    def get_media_by_type(self, media_type: MediaType) -> List[MediaAttachment]:
        """Get media by type."""
        return [media for media in self.media if media.media_type == media_type]
    
    def validate_content_references(self) -> Dict[str, List[str]]:
        """
        Validate that content references (like featured images, parent pages) exist.
        Returns a dict of validation errors.
        """
        errors = {"missing_media": [], "missing_parents": [], "orphaned_comments": []}
        
        # Get all media URLs and IDs
        media_urls = {media.file_url for media in self.media}
        media_ids = {media.id for media in self.media}
        
        # Get all content IDs
        content_ids = {post.id for post in self.posts} | {page.id for page in self.pages}
        
        # Check featured images exist
        for post in self.posts:
            if post.featured_image and post.featured_image not in media_urls:
                errors["missing_media"].append(f"Post '{post.title}' references missing featured image: {post.featured_image}")
        
        # Check parent references exist
        for content in self.posts + self.pages:
            if content.parent_id > 0 and content.parent_id not in content_ids:
                errors["missing_parents"].append(f"Content '{content.title}' references missing parent ID: {content.parent_id}")
        
        # Check comment post references exist
        for comment in self.comments:
            if comment.post_id not in content_ids:
                errors["orphaned_comments"].append(f"Comment {comment.comment_id} references missing post ID: {comment.post_id}")
        
        # Remove empty error lists
        return {k: v for k, v in errors.items() if v}
    
    def get_content_statistics(self) -> Dict[str, Any]:
        """Get comprehensive content statistics."""
        return {
            "total_posts": len(self.posts),
            "published_posts": len(self.published_posts),
            "draft_posts": len([p for p in self.posts if p.status == ContentStatus.DRAFT]),
            "total_pages": len(self.pages),
            "published_pages": len(self.published_pages),
            "total_media": len(self.media),
            "images": len(self.get_media_by_type(MediaType.IMAGE)),
            "videos": len(self.get_media_by_type(MediaType.VIDEO)),
            "documents": len(self.get_media_by_type(MediaType.DOCUMENT)),
            "categories": len(self.categories),
            "tags": len(self.tags),
            "comments": len(self.comments),
            "total_content_size": sum(media.file_size for media in self.media),
        }


# Utility functions for schema validation and transformation

def validate_wordpress_export(data: Dict[str, Any]) -> ContentCollection:
    """
    Validate and transform WordPress export data into a ContentCollection.
    
    Args:
        data: Raw WordPress export data
        
    Returns:
        ContentCollection: Validated content collection
        
    Raises:
        ValidationError: If data doesn't match expected schema
    """
    try:
        # Transform raw data into structured content
        collection = ContentCollection()
        
        # Process posts
        if 'posts' in data:
            for post_data in data['posts']:
                if post_data.get('post_type') == 'post':
                    post = WordPressPost(**post_data)
                    collection.posts.append(post)
                elif post_data.get('post_type') == 'page':
                    page = WordPressPage(**post_data)
                    collection.pages.append(page)
                elif post_data.get('post_type') == 'attachment':
                    media = MediaAttachment(**post_data)
                    collection.media.append(media)
        
        # Process taxonomies
        if 'categories' in data:
            collection.categories = [ContentTaxonomy(**cat) for cat in data['categories']]
        if 'tags' in data:
            collection.tags = [ContentTaxonomy(**tag) for tag in data['tags']]
        
        # Process comments
        if 'comments' in data:
            collection.comments = [ContentComment(**comment) for comment in data['comments']]
        
        return collection
        
    except Exception as e:
        raise ValueError(f"Failed to validate WordPress export data: {str(e)}")


def create_content_schema_mapping() -> Dict[str, type]:
    """
    Create a mapping of content types to their schema classes.
    
    Returns:
        Dict mapping content type strings to Pydantic model classes
    """
    return {
        'post': WordPressPost,
        'page': WordPressPage,
        'attachment': MediaAttachment,
        'category': ContentTaxonomy,
        'tag': ContentTaxonomy,
        'comment': ContentComment,
    }


# Export all schemas and utilities
__all__ = [
    'ContentStatus',
    'ContentType', 
    'MediaType',
    'BaseContent',
    'WordPressPost',
    'WordPressPage',
    'MediaAttachment',
    'ContentTaxonomy',
    'ContentComment',
    'ContentCollection',
    'validate_wordpress_export',
    'create_content_schema_mapping',
]
