#!/usr/bin/env python3
"""
Pytest tests for MediaAgent - WordPress media migration to Google Cloud Storage functionality.
"""

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
import tempfile
import json
from media_agent import MediaAgent, MediaFile, MediaBundle, UpdatedContentBundle, process_media_migration


class TestMediaAgent:
    """Test suite for MediaAgent class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.gcs_credentials_path = "/fake/path/to/credentials.json"
        self.gcs_bucket_name = "test-bucket"
        self.gcs_folder = "media"
        self.wp_site_url = "https://example.com"
        
        # Mock GCS client initialization
        with patch('media_agent.storage.Client'):
            self.agent = MediaAgent(
                gcs_credentials_path=self.gcs_credentials_path,
                gcs_bucket_name=self.gcs_bucket_name,
                gcs_folder=self.gcs_folder,
                wp_site_url=self.wp_site_url
            )
    
    def test_initialization(self):
        """Test agent initialization with GCS credentials."""
        with patch('media_agent.storage.Client') as mock_client:
            agent = MediaAgent(
                gcs_credentials_path=self.gcs_credentials_path,
                gcs_bucket_name=self.gcs_bucket_name,
                gcs_folder=self.gcs_folder,
                wp_site_url=self.wp_site_url
            )
            
            assert agent.gcs_bucket_name == self.gcs_bucket_name
            assert agent.gcs_folder == self.gcs_folder
            assert agent.wp_site_url == self.wp_site_url
            mock_client.from_service_account_json.assert_called_once_with(self.gcs_credentials_path)
    
    @patch('media_agent.requests.get')
    def test_resolve_wp_attachment_id_success(self, mock_get):
        """Test successful WordPress attachment ID resolution."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "source_url": "https://example.com/wp-content/uploads/2024/image.jpg"
        }
        mock_get.return_value = mock_response
        
        url = self.agent.resolve_wp_attachment_id("123")
        
        assert url == "https://example.com/wp-content/uploads/2024/image.jpg"
        mock_get.assert_called_once_with(
            "https://example.com/wp-json/wp/v2/media/123",
            timeout=30
        )
    
    @patch('media_agent.requests.get')
    def test_resolve_wp_attachment_id_not_found(self, mock_get):
        """Test WordPress attachment ID resolution with 404."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            "code": "rest_post_invalid_id",
            "message": "Invalid post ID."
        }
        mock_get.return_value = mock_response
        
        url = self.agent.resolve_wp_attachment_id("999")
        
        assert url is None
    
    @patch('media_agent.requests.get')
    def test_resolve_wp_attachment_id_network_error(self, mock_get):
        """Test WordPress attachment ID resolution with network error."""
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        
        url = self.agent.resolve_wp_attachment_id("123")
        
        assert url is None
    
    def test_extract_media_urls_img_tags(self):
        """Test extraction of media URLs from img tags."""
        content = '''
        <p>Here's an image: <img src="https://example.com/image1.jpg" alt="Test Image" /></p>
        <img src="/uploads/image2.png" alt="Another Image">
        '''
        
        urls = self.agent.extract_media_urls(content)
        
        assert "https://example.com/image1.jpg" in urls
        assert "/uploads/image2.png" in urls
    
    def test_extract_media_urls_markdown_images(self):
        """Test extraction of media URLs from Markdown images."""
        content = '''
        # Blog Post
        
        ![Image 1](https://example.com/markdown1.jpg)
        ![Image 2](/assets/markdown2.png)
        '''
        
        urls = self.agent.extract_media_urls(content)
        
        assert "https://example.com/markdown1.jpg" in urls
        assert "/assets/markdown2.png" in urls
    
    def test_extract_media_urls_figure_tags(self):
        """Test extraction of media URLs from figure tags."""
        content = '''
        <figure>
            <img src="https://example.com/figure1.jpg" alt="Figure Image" />
            <figcaption>Image caption</figcaption>
        </figure>
        '''
        
        urls = self.agent.extract_media_urls(content)
        
        assert "https://example.com/figure1.jpg" in urls
    
    @patch.object(MediaAgent, 'resolve_wp_attachment_id')
    def test_extract_media_urls_with_attachment_ids(self, mock_resolve):
        """Test extraction of media URLs with WordPress attachment ID resolution."""
        mock_resolve.side_effect = lambda id: f"https://example.com/resolved-{id}.jpg" if id == "123" else None
        
        content = '''
        <img src="123" alt="WordPress Attachment" />
        <img src="999" alt="Invalid Attachment" />
        ![Markdown](456)
        '''
        
        urls = self.agent.extract_media_urls(content)
        
        # Should resolve valid attachment ID
        assert "https://example.com/resolved-123.jpg" in urls
        
        # Should call resolve for numeric IDs
        mock_resolve.assert_any_call("123")
        mock_resolve.assert_any_call("999")
        mock_resolve.assert_any_call("456")
    
    def test_extract_media_urls_mixed_content(self):
        """Test extraction from content with mixed media types."""
        content = '''
        <h1>Blog Post</h1>
        <p>Introduction with <img src="https://example.com/intro.jpg" alt="Intro" />.</p>
        
        ![Markdown Image](https://example.com/markdown.png)
        
        <figure>
            <img src="/uploads/figure.gif" alt="Figure" />
        </figure>
        '''
        
        urls = self.agent.extract_media_urls(content)
        
        assert len(urls) == 3
        assert "https://example.com/intro.jpg" in urls
        assert "https://example.com/markdown.png" in urls
        assert "/uploads/figure.gif" in urls
    
    @patch('media_agent.requests.get')
    def test_download_media_file_success(self, mock_get):
        """Test successful media file download."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'image/jpeg'}
        mock_response.content = b'fake image data'
        mock_get.return_value = mock_response
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            media_file = self.agent.download_media_file(
                "https://example.com/test.jpg",
                temp_path
            )
            
            assert media_file is not None
            assert media_file.original_url == "https://example.com/test.jpg"
            assert media_file.filename == "test.jpg"
            assert media_file.content_type == "image/jpeg"
            assert media_file.local_path.exists()
    
    @patch('media_agent.requests.get')
    def test_download_media_file_failure(self, mock_get):
        """Test media file download failure."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            media_file = self.agent.download_media_file(
                "https://example.com/not-found.jpg",
                temp_path
            )
            
            assert media_file is None
    
    @patch('media_agent.requests.get')
    def test_download_media_file_network_error(self, mock_get):
        """Test media file download with network error."""
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            media_file = self.agent.download_media_file(
                "https://example.com/test.jpg",
                temp_path
            )
            
            assert media_file is None
    
    def test_upload_to_gcs_success_public(self):
        """Test successful GCS upload with public access."""
        # Create a mock media file
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(b'test content')
            temp_file.flush()
            
            media_file = MediaFile(
                original_url="https://example.com/test.jpg",
                filename="test.jpg",
                local_path=Path(temp_file.name),
                content_type="image/jpeg",
                gcs_url=None
            )
            
            # Mock GCS operations
            mock_blob = Mock()
            mock_blob.public_url = "https://storage.googleapis.com/test-bucket/media/test.jpg"
            self.agent.bucket.blob.return_value = mock_blob
            
            # Test successful upload with public access
            success = self.agent.upload_to_gcs(media_file)
            
            assert success is True
            assert media_file.gcs_url == "https://storage.googleapis.com/test-bucket/media/test.jpg"
            mock_blob.upload_from_filename.assert_called_once()
            mock_blob.make_public.assert_called_once()
    
    def test_upload_to_gcs_success_signed_url(self):
        """Test successful GCS upload with signed URL fallback."""
        # Create a mock media file
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_file.write(b'test content')
            temp_file.flush()
            
            media_file = MediaFile(
                original_url="https://example.com/test.jpg",
                filename="test.jpg",
                local_path=Path(temp_file.name),
                content_type="image/jpeg",
                gcs_url=None
            )
            
            # Mock GCS operations with public access failure
            mock_blob = Mock()
            mock_blob.make_public.side_effect = Exception("Public access prevention enforced")
            mock_blob.generate_signed_url.return_value = "https://storage.googleapis.com/signed-url"
            self.agent.bucket.blob.return_value = mock_blob
            
            # Test upload with signed URL fallback
            success = self.agent.upload_to_gcs(media_file)
            
            assert success is True
            assert media_file.gcs_url == "https://storage.googleapis.com/signed-url"
            mock_blob.upload_from_filename.assert_called_once()
            mock_blob.make_public.assert_called_once()
            mock_blob.generate_signed_url.assert_called_once()
    
    def test_upload_to_gcs_failure(self):
        """Test GCS upload failure."""
        # Create a mock media file
        with tempfile.NamedTemporaryFile() as temp_file:
            media_file = MediaFile(
                original_url="https://example.com/test.jpg",
                filename="test.jpg",
                local_path=Path(temp_file.name),
                content_type="image/jpeg",
                gcs_url=None
            )
            
            # Mock GCS operations with upload failure
            mock_blob = Mock()
            mock_blob.upload_from_filename.side_effect = Exception("Upload failed")
            self.agent.bucket.blob.return_value = mock_blob
            
            # Test upload failure
            success = self.agent.upload_to_gcs(media_file)
            
            assert success is False
            assert media_file.gcs_url is None
    
    def test_update_content_links_img_tags(self):
        """Test updating image links in HTML img tags."""
        content = '''
        <p>Here's an image: <img src="https://example.com/old.jpg" alt="Test" /></p>
        <img src="/uploads/old.png" alt="Another">
        '''
        
        media_bundle = MediaBundle(
            media_files=[
                MediaFile(
                    original_url="https://example.com/old.jpg",
                    filename="old.jpg",
                    local_path=Path("/tmp/old.jpg"),
                    content_type="image/jpeg",
                    gcs_url="https://storage.googleapis.com/bucket/new.jpg"
                ),
                MediaFile(
                    original_url="/uploads/old.png",
                    filename="old.png",
                    local_path=Path("/tmp/old.png"),
                    content_type="image/png",
                    gcs_url="https://storage.googleapis.com/bucket/new.png"
                )
            ]
        )
        
        updated_content = self.agent.update_content_links(content, media_bundle)
        
        assert "https://storage.googleapis.com/bucket/new.jpg" in updated_content
        assert "https://storage.googleapis.com/bucket/new.png" in updated_content
        assert "https://example.com/old.jpg" not in updated_content
        assert "/uploads/old.png" not in updated_content
    
    def test_update_content_links_markdown(self):
        """Test updating image links in Markdown format."""
        content = '''
        # Blog Post
        
        ![Image 1](https://example.com/old1.jpg)
        ![Image 2](/assets/old2.png)
        '''
        
        media_bundle = MediaBundle(
            media_files=[
                MediaFile(
                    original_url="https://example.com/old1.jpg",
                    filename="old1.jpg",
                    local_path=Path("/tmp/old1.jpg"),
                    content_type="image/jpeg",
                    gcs_url="https://storage.googleapis.com/bucket/new1.jpg"
                ),
                MediaFile(
                    original_url="/assets/old2.png",
                    filename="old2.png",
                    local_path=Path("/tmp/old2.png"),
                    content_type="image/png",
                    gcs_url="https://storage.googleapis.com/bucket/new2.png"
                )
            ]
        )
        
        updated_content = self.agent.update_content_links(content, media_bundle)
        
        assert "![Image 1](https://storage.googleapis.com/bucket/new1.jpg)" in updated_content
        assert "![Image 2](https://storage.googleapis.com/bucket/new2.png)" in updated_content
    
    def test_update_content_links_no_matches(self):
        """Test content update when no URLs match."""
        content = '<p>No images in this content.</p>'
        media_bundle = MediaBundle(media_files=[])
        
        updated_content = self.agent.update_content_links(content, media_bundle)
        
        assert updated_content == content
    
    @patch.object(MediaAgent, 'extract_media_urls')
    @patch.object(MediaAgent, 'download_media_file')
    @patch.object(MediaAgent, 'upload_to_gcs')
    @patch.object(MediaAgent, 'update_content_links')
    def test_process_content_bundle_success(self, mock_update, mock_upload, 
                                          mock_download, mock_extract):
        """Test complete content bundle processing."""
        # Setup mocks
        mock_extract.return_value = ["https://example.com/image.jpg"]
        
        mock_media_file = MediaFile(
            original_url="https://example.com/image.jpg",
            filename="image.jpg",
            local_path=Path("/tmp/image.jpg"),
            content_type="image/jpeg",
            gcs_url="https://storage.googleapis.com/bucket/image.jpg"
        )
        mock_download.return_value = mock_media_file
        mock_upload.return_value = True
        mock_update.side_effect = lambda content, bundle: content.replace(
            "https://example.com/image.jpg",
            "https://storage.googleapis.com/bucket/image.jpg"
        )
        
        # Test data
        posts = [{"content": '<img src="https://example.com/image.jpg" />'}]
        pages = [{"content": 'No images here'}]
        
        result = self.agent.process_content_bundle(posts, pages)
        
        assert isinstance(result, UpdatedContentBundle)
        assert len(result.media_bundle.media_files) == 1
        assert result.updated_posts[0]["content"] == '<img src="https://storage.googleapis.com/bucket/image.jpg" />'
        assert result.updated_pages[0]["content"] == 'No images here'
    
    @patch.object(MediaAgent, 'extract_media_urls')
    def test_process_content_bundle_no_media(self, mock_extract):
        """Test content bundle processing with no media."""
        mock_extract.return_value = []
        
        posts = [{"content": "Text only content"}]
        pages = [{"content": "More text content"}]
        
        result = self.agent.process_content_bundle(posts, pages)
        
        assert isinstance(result, UpdatedContentBundle)
        assert len(result.media_bundle.media_files) == 0
        assert result.updated_posts == posts
        assert result.updated_pages == pages
    
    @patch.object(MediaAgent, 'extract_media_urls')
    @patch.object(MediaAgent, 'download_media_file')
    def test_process_content_bundle_download_failures(self, mock_download, mock_extract):
        """Test content bundle processing with download failures."""
        mock_extract.return_value = ["https://example.com/missing.jpg"]
        mock_download.return_value = None  # Download failure
        
        posts = [{"content": '<img src="https://example.com/missing.jpg" />'}]
        pages = []
        
        result = self.agent.process_content_bundle(posts, pages)
        
        assert isinstance(result, UpdatedContentBundle)
        assert len(result.media_bundle.media_files) == 0
        # Content should remain unchanged if download fails
        assert result.updated_posts == posts


class TestMediaFileModel:
    """Test MediaFile model validation."""
    
    def test_media_file_creation(self):
        """Test MediaFile model creation and validation."""
        with tempfile.NamedTemporaryFile() as temp_file:
            media_file = MediaFile(
                original_url="https://example.com/test.jpg",
                filename="test.jpg",
                local_path=Path(temp_file.name),
                content_type="image/jpeg",
                gcs_url="https://storage.googleapis.com/bucket/test.jpg"
            )
            
            assert media_file.original_url == "https://example.com/test.jpg"
            assert media_file.filename == "test.jpg"
            assert media_file.content_type == "image/jpeg"
            assert media_file.gcs_url == "https://storage.googleapis.com/bucket/test.jpg"
            assert isinstance(media_file.local_path, Path)
    
    def test_media_file_without_gcs_url(self):
        """Test MediaFile creation without GCS URL."""
        with tempfile.NamedTemporaryFile() as temp_file:
            media_file = MediaFile(
                original_url="https://example.com/test.jpg",
                filename="test.jpg",
                local_path=Path(temp_file.name),
                content_type="image/jpeg"
            )
            
            assert media_file.gcs_url is None


class TestMediaBundleModel:
    """Test MediaBundle model validation."""
    
    def test_media_bundle_creation(self):
        """Test MediaBundle model creation."""
        with tempfile.NamedTemporaryFile() as temp_file:
            media_files = [
                MediaFile(
                    original_url="https://example.com/test1.jpg",
                    filename="test1.jpg",
                    local_path=Path(temp_file.name),
                    content_type="image/jpeg"
                ),
                MediaFile(
                    original_url="https://example.com/test2.png",
                    filename="test2.png",
                    local_path=Path(temp_file.name),
                    content_type="image/png"
                )
            ]
            
            bundle = MediaBundle(media_files=media_files)
            
            assert len(bundle.media_files) == 2
            assert all(isinstance(f, MediaFile) for f in bundle.media_files)


class TestUpdatedContentBundleModel:
    """Test UpdatedContentBundle model validation."""
    
    def test_updated_content_bundle_creation(self):
        """Test UpdatedContentBundle model creation."""
        posts = [{"content": "Updated post content"}]
        pages = [{"content": "Updated page content"}]
        media_bundle = MediaBundle(media_files=[])
        
        bundle = UpdatedContentBundle(
            updated_posts=posts,
            updated_pages=pages,
            media_bundle=media_bundle
        )
        
        assert bundle.updated_posts == posts
        assert bundle.updated_pages == pages
        assert isinstance(bundle.media_bundle, MediaBundle)


class TestConvenienceFunction:
    """Test the convenience function for media migration."""
    
    @patch.object(MediaAgent, 'process_content_bundle')
    def test_process_media_migration_convenience_function(self, mock_process):
        """Test the convenience process_media_migration function."""
        mock_result = UpdatedContentBundle(
            updated_posts=[],
            updated_pages=[],
            media_bundle=MediaBundle(media_files=[])
        )
        mock_process.return_value = mock_result
        
        with patch('media_agent.MediaAgent') as mock_agent_class:
            mock_agent_class.return_value.process_content_bundle = mock_process
            
            result = process_media_migration(
                posts=[],
                pages=[],
                gcs_credentials_path="/fake/path",
                gcs_bucket_name="test-bucket",
                gcs_folder="media",
                site_url="https://example.com"
            )
            
            assert isinstance(result, UpdatedContentBundle)
            mock_agent_class.assert_called_once()


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_invalid_gcs_credentials_path(self):
        """Test handling of invalid GCS credentials path."""
        with patch('media_agent.storage.Client') as mock_client:
            mock_client.from_service_account_json.side_effect = FileNotFoundError("Credentials not found")
            
            with pytest.raises(FileNotFoundError):
                MediaAgent(
                    gcs_credentials_path="/invalid/path",
                    gcs_bucket_name="test-bucket",
                    gcs_folder="media"
                )
    
    def test_invalid_bucket_name(self):
        """Test handling of invalid bucket name."""
        with patch('media_agent.storage.Client') as mock_client:
            mock_agent = MediaAgent(
                gcs_credentials_path="/fake/path",
                gcs_bucket_name="invalid-bucket",
                gcs_folder="media"
            )
            
            # Simulate bucket access error
            mock_agent.bucket.blob.side_effect = Exception("Bucket not found")
            
            with tempfile.NamedTemporaryFile() as temp_file:
                media_file = MediaFile(
                    original_url="https://example.com/test.jpg",
                    filename="test.jpg",
                    local_path=Path(temp_file.name),
                    content_type="image/jpeg"
                )
                
                success = mock_agent.upload_to_gcs(media_file)
                assert success is False
    
    def test_malformed_content(self):
        """Test handling of malformed HTML content."""
        with patch('media_agent.storage.Client'):
            agent = MediaAgent(
                gcs_credentials_path="/fake/path",
                gcs_bucket_name="test-bucket",
                gcs_folder="media"
            )
            
            # Test with severely malformed HTML
            malformed_content = "<img src='unclosed.jpg' <p>broken html"
            
            # Should not raise an exception
            urls = agent.extract_media_urls(malformed_content)
            assert isinstance(urls, list)


class TestRealWorldScenarios:
    """Integration-style tests with realistic scenarios."""
    
    def test_wordpress_attachment_migration(self):
        """Test migration of WordPress attachments with various formats."""
        content = '''
        <div class="wp-block-image">
            <figure class="aligncenter size-large">
                <img src="https://example.com/wp-content/uploads/2024/01/image-1024x768.jpg" 
                     alt="Sample Image" class="wp-image-123" />
                <figcaption>Image caption</figcaption>
            </figure>
        </div>
        
        <p>Another image: <img src="456" alt="WordPress Attachment" /></p>
        '''
        
        with patch('media_agent.storage.Client'):
            agent = MediaAgent(
                gcs_credentials_path="/fake/path",
                gcs_bucket_name="test-bucket",
                gcs_folder="media",
                wp_site_url="https://example.com"
            )
            
            with patch.object(agent, 'resolve_wp_attachment_id') as mock_resolve:
                mock_resolve.return_value = "https://example.com/wp-content/uploads/2024/resolved.jpg"
                
                urls = agent.extract_media_urls(content)
                
                assert "https://example.com/wp-content/uploads/2024/01/image-1024x768.jpg" in urls
                assert "https://example.com/wp-content/uploads/2024/resolved.jpg" in urls
                mock_resolve.assert_called_with("456")
    
    def test_mixed_media_types(self):
        """Test handling of various media file types."""
        content = '''
        <img src="https://example.com/image.jpg" alt="JPEG Image" />
        <img src="https://example.com/image.png" alt="PNG Image" />
        <img src="https://example.com/image.gif" alt="GIF Image" />
        <img src="https://example.com/image.webp" alt="WebP Image" />
        <img src="https://example.com/document.pdf" alt="PDF Document" />
        '''
        
        with patch('media_agent.storage.Client'):
            agent = MediaAgent(
                gcs_credentials_path="/fake/path",
                gcs_bucket_name="test-bucket",
                gcs_folder="media"
            )
            
            urls = agent.extract_media_urls(content)
            
            assert len(urls) == 5
            assert any("jpg" in url for url in urls)
            assert any("png" in url for url in urls)
            assert any("gif" in url for url in urls)
            assert any("webp" in url for url in urls)
            assert any("pdf" in url for url in urls)
    
    def test_relative_url_handling(self):
        """Test handling of relative URLs."""
        content = '''
        <img src="/uploads/image.jpg" alt="Root Relative" />
        <img src="../images/image.png" alt="Parent Relative" />
        <img src="./assets/image.gif" alt="Current Relative" />
        '''
        
        with patch('media_agent.storage.Client'):
            agent = MediaAgent(
                gcs_credentials_path="/fake/path",
                gcs_bucket_name="test-bucket",
                gcs_folder="media"
            )
            
            urls = agent.extract_media_urls(content)
            
            # Should extract relative URLs as-is
            assert "/uploads/image.jpg" in urls
            assert "../images/image.png" in urls
            assert "./assets/image.gif" in urls


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
