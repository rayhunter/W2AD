import os
import re
import requests
import tempfile
import mimetypes
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from pydantic import BaseModel
import logging
from urllib.parse import urlparse, urljoin
from google.cloud import storage
import json
from base_agent import BaseAgent, BaseResult, AgentStatus

class MediaFile(BaseModel):
    """Model for a media file."""
    original_url: str
    filename: str
    local_path: str = ""
    gcs_url: str = ""
    content_type: str = ""
    size_bytes: int = 0
    # WordPress attachment IDs (e.g. "15" from <img src="15">) that resolved to original_url
    attachment_ids: List[str] = []

class MediaBundle(BaseModel):
    """Model for bundled media files."""
    files: List[MediaFile] = []
    total_files: int = 0
    total_size_bytes: int = 0
    successful_uploads: int = 0
    failed_uploads: int = 0

class UpdatedContentBundle(BaseModel):
    """Model for content with updated media links."""
    posts: List[Dict[str, Any]]
    pages: List[Dict[str, Any]]
    media_bundle: MediaBundle

class MediaAgent(BaseAgent):
    """Agent for downloading WordPress media and uploading to Google Cloud Storage."""
    
    def __init__(self, gcs_credentials_path: str, gcs_bucket_name: str, gcs_folder: str = "wp-migration", wp_site_url: str = None, **kwargs):
        """Initialize the media agent.
        
        Args:
            gcs_credentials_path: Path to Google Cloud Storage service account JSON
            gcs_bucket_name: Name of the GCS bucket
            gcs_folder: Folder prefix within the bucket for uploaded files
            wp_site_url: WordPress site URL for resolving attachment IDs
            **kwargs: Additional configuration passed to BaseAgent
        """
        # Initialize base agent first
        agent_name = kwargs.pop('name', 'MediaAgent')
        super().__init__(name=agent_name, 
                        gcs_credentials_path=gcs_credentials_path,
                        gcs_bucket_name=gcs_bucket_name,
                        gcs_folder=gcs_folder,
                        wp_site_url=wp_site_url,
                        **kwargs)
        
        # Set up media-specific configuration
        self.gcs_credentials_path = gcs_credentials_path
        self.gcs_bucket_name = gcs_bucket_name
        self.gcs_folder = gcs_folder.strip('/')
        self.wp_site_url = wp_site_url.rstrip('/') if wp_site_url else None
        self.wp_api_base = f"{self.wp_site_url}/wp-json/wp/v2" if wp_site_url else None
        # attachment ID -> resolved media URL, recorded by extract_media_urls so the
        # numeric src can be rewritten to the uploaded copy later
        self._attachment_urls: Dict[str, str] = {}

        # Initialize GCS client
        try:
            if gcs_credentials_path:
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = gcs_credentials_path
            self.storage_client = storage.Client()
            self.bucket = self.storage_client.bucket(gcs_bucket_name)
            self.logger.info(f"Initialized MediaAgent with GCS bucket: {gcs_bucket_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize GCS client: {e}")
            raise ValueError(f"GCS initialization failed: {e}")
        
        # Validate configuration
        self.validate_configuration()
    
    def resolve_wp_attachment_id(self, attachment_id: str) -> Optional[str]:
        """Resolve a WordPress attachment ID to its full media URL.
        
        Args:
            attachment_id: WordPress attachment ID (e.g., "15", "18")
            
        Returns:
            Full media URL or None if not found
        """
        if not self.wp_api_base or not attachment_id.isdigit():
            return None
        
        try:
            self.logger.debug(f"Resolving WordPress attachment ID: {attachment_id}")
            response = requests.get(f"{self.wp_api_base}/media/{attachment_id}", timeout=30)
            response.raise_for_status()
            
            media_data = response.json()
            media_url = media_data.get('source_url')
            
            if media_url:
                self.logger.info(f"Resolved attachment {attachment_id} to URL: {media_url}")
                return media_url
            else:
                self.logger.warning(f"No source_url found for attachment {attachment_id}")
                return None
                
        except Exception as e:
            if "404" in str(e) or "Invalid post ID" in str(e):
                self.logger.warning(f"Attachment ID {attachment_id} not found (404) - may be deleted or invalid")
            else:
                self.logger.error(f"Failed to resolve attachment ID {attachment_id}: {e}")
            return None
    
    def extract_media_urls(self, content: str, context: str = "") -> List[str]:
        """Extract all media URLs from content.

        Numeric <img src="15"> references are resolved through the WP media
        endpoint only. If an ID does not resolve it is left alone (and later
        turned into a text placeholder by the content sanitizer) rather than
        guessed, so a post never ends up with somebody else's image.

        Args:
            content: HTML or Markdown content
            context: Post/page title, used only for log messages

        Returns:
            List of unique media URLs
        """
        # Debug: Log a sample of the content
        self.logger.debug(f"Content sample (first 500 chars): {content[:500]}")
        
        media_urls = set()
        
        # Extract from img tags
        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
        img_matches = re.findall(img_pattern, content, re.IGNORECASE)
        self.logger.debug(f"Found {len(img_matches)} img tag matches: {img_matches}")
        
        # Resolve WordPress attachment IDs to URLs
        resolved_urls = []
        for img_src in img_matches:
            if img_src.isdigit():  # This is a WordPress attachment ID
                resolved_url = self.resolve_wp_attachment_id(img_src)
                if resolved_url:
                    resolved_urls.append(resolved_url)
                    self._attachment_urls[img_src] = resolved_url
                    self.logger.info(f"Resolved attachment ID {img_src} → {resolved_url}")
                else:
                    self.logger.warning(
                        f"Could not resolve attachment ID {img_src}"
                        f"{f' in {context!r}' if context else ''}; leaving as placeholder"
                    )
            else:
                resolved_urls.append(img_src)  # Already a URL
        
        media_urls.update(resolved_urls)
        
        # Extract from markdown images
        md_img_pattern = r'!\[[^\]]*\]\(([^)]+)\)'
        md_img_matches = re.findall(md_img_pattern, content)
        self.logger.debug(f"Found {len(md_img_matches)} markdown image matches: {md_img_matches}")
        media_urls.update(md_img_matches)
        
        # Extract from figure tags and other media elements
        figure_pattern = r'<figure[^>]*>.*?<img[^>]+src=["\']([^"\']+)["\'][^>]*>.*?</figure>'
        figure_matches = re.findall(figure_pattern, content, re.IGNORECASE | re.DOTALL)
        self.logger.debug(f"Found {len(figure_matches)} figure tag matches: {figure_matches}")
        media_urls.update(figure_matches)
        
        # Look for any URL patterns that might be media
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+\.(jpg|jpeg|png|gif|webp|svg|bmp|tiff|mp4|mp3|wav|pdf)'
        url_matches = re.findall(url_pattern, content, re.IGNORECASE)
        self.logger.debug(f"Found {len(url_matches)} direct URL matches: {url_matches}")
        media_urls.update([match[0] if isinstance(match, tuple) else match for match in url_matches])
        
        # Filter for actual media files
        media_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.tiff', 
                          '.mp4', '.mp3', '.wav', '.pdf', '.doc', '.docx'}
        
        filtered_urls = []
        skipped_urls = []
        
        for url in media_urls:
            # Skip empty, relative-only, or invalid URLs
            if not url or url.startswith('#') or url.startswith('data:'):
                skipped_urls.append(f"{url} (invalid/data URL)")
                continue
            
            # Check if it has a media extension or looks like a WordPress media URL
            url_lower = url.lower()
            has_media_ext = any(url_lower.endswith(ext) for ext in media_extensions)
            is_wp_media = '/wp-content/uploads/' in url or '/uploads/' in url
            
            if has_media_ext or is_wp_media:
                filtered_urls.append(url)
            else:
                skipped_urls.append(f"{url} (no media extension)")
        
        self.logger.info(f"Extracted {len(filtered_urls)} media URLs from content")
        if skipped_urls:
            self.logger.debug(f"Skipped URLs: {skipped_urls}")
        
        return list(filtered_urls)
    
    def download_media_file(self, url: str, temp_dir: Path) -> Optional[MediaFile]:
        """Download a media file from URL.
        
        Args:
            url: URL of the media file
            temp_dir: Temporary directory for downloads
            
        Returns:
            MediaFile object or None if download failed
        """
        try:
            # Parse URL and create filename
            parsed_url = urlparse(url)
            filename = Path(parsed_url.path).name
            
            # If no filename extension, try to get from URL or default
            if not filename or '.' not in filename:
                filename = f"media_{hash(url) % 10000}.jpg"
            
            # Clean filename for filesystem
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            
            # Download file
            self.logger.info(f"Downloading: {url}")
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Determine content type
            content_type = response.headers.get('content-type', '')
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                content_type = content_type or 'application/octet-stream'
            
            # Save to temporary file
            local_path = temp_dir / filename
            total_size = 0
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        total_size += len(chunk)
            
            media_file = MediaFile(
                original_url=url,
                filename=filename,
                local_path=str(local_path),
                content_type=content_type,
                size_bytes=total_size
            )
            
            self.logger.info(f"Downloaded {filename} ({total_size} bytes)")
            return media_file
            
        except Exception as e:
            self.logger.error(f"Failed to download {url}: {e}")
            return None
    
    def upload_to_gcs(self, media_file: MediaFile) -> bool:
        """Upload a media file to Google Cloud Storage.
        
        Args:
            media_file: MediaFile object with local file path
            
        Returns:
            True if upload successful, False otherwise
        """
        try:
            # Create GCS object name
            gcs_object_name = f"{self.gcs_folder}/{media_file.filename}" if self.gcs_folder else media_file.filename
            
            # Upload file
            blob = self.bucket.blob(gcs_object_name)
            blob.upload_from_filename(
                media_file.local_path,
                content_type=media_file.content_type
            )
            
            # Try to make the file publicly accessible, fall back to signed URL if blocked
            try:
                blob.make_public()
                media_file.gcs_url = blob.public_url
                self.logger.info(f"Using public URL for {media_file.filename}")
            except Exception as e:
                self.logger.warning(f"Cannot make {media_file.filename} public, using signed URL: {e}")
                # Generate a signed URL (valid for 1 year)
                from datetime import datetime, timedelta
                expiration = datetime.utcnow() + timedelta(days=365)
                media_file.gcs_url = blob.generate_signed_url(expiration=expiration)
                self.logger.info(f"Using signed URL for {media_file.filename}")
            
            self.logger.info(f"Uploaded {media_file.filename} to GCS: {media_file.gcs_url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to upload {media_file.filename} to GCS: {e}")
            return False
    
    def process_media_from_content(self, posts: List[Dict], pages: List[Dict]) -> MediaBundle:
        """Process and upload all media from posts and pages.
        
        Args:
            posts: List of post dictionaries with content
            pages: List of page dictionaries with content
            
        Returns:
            MediaBundle with processed media files
        """
        media_bundle = MediaBundle()
        all_urls = set()
        
        # Extract URLs from all content
        for post in posts:
            post_title = post.get('title', {})
            if isinstance(post_title, dict):
                title_context = post_title.get('rendered', '')
            else:
                title_context = str(post_title)
            urls = self.extract_media_urls(post.get('content', ''), context=title_context)
            all_urls.update(urls)
            if post.get('featured_image'):
                all_urls.add(post['featured_image'])

        for page in pages:
            page_title = page.get('title', {})
            if isinstance(page_title, dict):
                title_context = page_title.get('rendered', '')
            else:
                title_context = str(page_title)
            urls = self.extract_media_urls(page.get('content', ''), context=title_context)
            all_urls.update(urls)
            if page.get('featured_image'):
                all_urls.add(page['featured_image'])

        if not all_urls:
            self.logger.info("No media URLs found in content")
            return media_bundle
        
        self.logger.info(f"Processing {len(all_urls)} unique media URLs")
        
        # Create temporary directory for downloads
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            for url in all_urls:
                # Download file
                media_file = self.download_media_file(url, temp_path)
                if not media_file:
                    media_bundle.failed_uploads += 1
                    continue

                media_file.attachment_ids = sorted(
                    aid for aid, resolved in self._attachment_urls.items() if resolved == url
                )

                # Upload to GCS
                if self.upload_to_gcs(media_file):
                    media_bundle.files.append(media_file)
                    media_bundle.successful_uploads += 1
                    media_bundle.total_size_bytes += media_file.size_bytes
                else:
                    media_bundle.failed_uploads += 1
        
        media_bundle.total_files = len(all_urls)
        self.logger.info(f"Media processing complete: {media_bundle.successful_uploads} successful, {media_bundle.failed_uploads} failed")
        
        return media_bundle
    
    def update_content_links(self, content: str, media_bundle: MediaBundle) -> str:
        """Update content to use GCS URLs instead of original URLs.
        
        Args:
            content: Original content with old URLs
            media_bundle: MediaBundle with URL mappings
            
        Returns:
            Updated content with new URLs
        """
        updated_content = content
        
        # Create URL mapping
        url_mapping = {media.original_url: media.gcs_url for media in media_bundle.files}
        
        # Replace URLs in content
        for original_url, gcs_url in url_mapping.items():
            # Replace in img tags
            updated_content = updated_content.replace(f'src="{original_url}"', f'src="{gcs_url}"')
            updated_content = updated_content.replace(f"src='{original_url}'", f"src='{gcs_url}'")
            
            # Replace in markdown images
            updated_content = updated_content.replace(f']({original_url})', f']({gcs_url})')
            
            # Replace any other direct references
            updated_content = updated_content.replace(original_url, gcs_url)

        # Rewrite numeric attachment-ID sources (<img src="15">) that resolved to an uploaded file.
        # Only exact src attribute values are touched, so src="150" or plain text "15" are left alone.
        for media in media_bundle.files:
            if not media.gcs_url:
                continue
            for attachment_id in media.attachment_ids:
                updated_content = re.sub(
                    r'(\bsrc\s*=\s*)(["\'])' + re.escape(attachment_id) + r'\2',
                    lambda m, url=media.gcs_url: f"{m.group(1)}{m.group(2)}{url}{m.group(2)}",
                    updated_content,
                )

        return updated_content
    
    def process_content_bundle(self, posts: List[Dict], pages: List[Dict]) -> UpdatedContentBundle:
        """Process a complete content bundle with media migration.
        
        Args:
            posts: List of post dictionaries
            pages: List of page dictionaries
            
        Returns:
            UpdatedContentBundle with migrated media and updated links
        """
        self.logger.info("Starting media migration process...")
        
        # Process and upload media
        media_bundle = self.process_media_from_content(posts, pages)
        
        # Update content links
        updated_posts = []
        for post in posts:
            updated_post = post.copy()
            updated_post['content'] = self.update_content_links(post.get('content', ''), media_bundle)
            if post.get('featured_image'):
                updated_post['featured_image'] = self.update_content_links(post['featured_image'], media_bundle)
            updated_posts.append(updated_post)
        
        updated_pages = []
        for page in pages:
            updated_page = page.copy()
            updated_page['content'] = self.update_content_links(page.get('content', ''), media_bundle)
            if page.get('featured_image'):
                updated_page['featured_image'] = self.update_content_links(page['featured_image'], media_bundle)
            updated_pages.append(updated_page)
        
        bundle = UpdatedContentBundle(
            posts=updated_posts,
            pages=updated_pages,
            media_bundle=media_bundle
        )
        
        self.logger.info(f"Media migration completed: {media_bundle.successful_uploads} files uploaded to GCS")
        return bundle
    
    def process_media_from_content_with_metrics(self, posts: List[Dict], pages: List[Dict]) -> MediaBundle:
        """Process and upload all media from posts and pages with metrics tracking."""
        return self._execute_with_metrics("process_media_from_content", self.process_media_from_content, posts, pages).data
    
    def process(self, posts: List[Dict] = None, pages: List[Dict] = None, *args, **kwargs) -> BaseResult:
        """Main processing method - processes media migration from posts and pages.
        
        Args:
            posts: List of post dictionaries with content
            pages: List of page dictionaries with content
        """
        try:
            if posts is None:
                posts = []
            if pages is None:
                pages = []
                
            self.validate_input(posts, list)
            self.validate_input(pages, list)
            
            bundle = self.process_content_bundle(posts, pages)
            
            return BaseResult(
                success=True,
                status=AgentStatus.SUCCESS,
                data=bundle,
                message=f"Successfully processed {bundle.media_bundle.successful_uploads} media files"
            )
        except Exception as e:
            return BaseResult(
                success=False,
                status=AgentStatus.ERROR,
                error=str(e),
                message="Failed to process media migration"
            )
    
    def validate_configuration(self) -> bool:
        """Validate the agent's configuration."""
        if not self.gcs_credentials_path:
            raise ValueError("GCS credentials path is required")
        
        if not self.gcs_bucket_name:
            raise ValueError("GCS bucket name is required")
        
        # Test GCS connectivity
        try:
            # Try to list objects (with limit 1 to minimize impact)
            list(self.bucket.list_blobs(max_results=1))
        except Exception as e:
            raise ValueError(f"Cannot access GCS bucket '{self.gcs_bucket_name}': {str(e)}")
        
        return True

def process_media_migration(
    posts: List[Dict],
    pages: List[Dict],
    gcs_credentials_path: str,
    gcs_bucket_name: str,
    gcs_folder: str = "wp-migration",
    wp_site_url: str = None
) -> UpdatedContentBundle:
    """Main function to process media migration.
    
    Args:
        posts: List of post dictionaries
        pages: List of page dictionaries
        gcs_credentials_path: Path to GCS service account credentials
        gcs_bucket_name: GCS bucket name
        gcs_folder: Folder prefix in bucket
        wp_site_url: WordPress site URL for resolving attachment IDs
        
    Returns:
        UpdatedContentBundle with migrated media
    """
    agent = MediaAgent(gcs_credentials_path, gcs_bucket_name, gcs_folder, wp_site_url)
    return agent.process_content_bundle(posts, pages)
