#!/usr/bin/env python3
"""
Pytest tests for ExtractionAgent - WordPress content extraction functionality.
"""

import pytest
import requests
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from extraction_agent import ExtractionAgent, WPPost, WPPage, WPContentBundle, extract_from_wordpress


class TestExtractionAgent:
    """Test suite for ExtractionAgent class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = ExtractionAgent("https://example.com")
        self.sample_post_data = {
            "id": 123,
            "title": {"rendered": "Test Post Title"},
            "content": {"rendered": "<p>Test post content</p>"},
            "excerpt": {"rendered": "<p>Test excerpt</p>"},
            "date": "2024-01-15T10:00:00",
            "slug": "test-post-title",
            "categories": [1, 2],
            "tags": [3, 4],
            "featured_media": 567,
            "link": "https://example.com/test-post-title"
        }
        self.sample_page_data = {
            "id": 456,
            "title": {"rendered": "Test Page Title"},
            "content": {"rendered": "<p>Test page content</p>"},
            "excerpt": {"rendered": "<p>Test page excerpt</p>"},
            "date": "2024-01-16T11:00:00",
            "slug": "test-page-title",
            "link": "https://example.com/test-page-title"
        }
    
    def test_initialization(self):
        """Test agent initialization with different configurations."""
        # Basic initialization
        agent = ExtractionAgent("https://example.com")
        assert agent.site_url == "https://example.com"
        assert agent.username is None
        assert agent.password is None
        
        # With authentication
        agent_auth = ExtractionAgent("https://example.com", "user", "pass")
        assert agent_auth.username == "user"
        assert agent_auth.password == "pass"
    
    def test_get_headers_no_auth(self):
        """Test header generation without authentication."""
        headers = self.agent.get_headers()
        expected = {
            'User-Agent': 'WordPress-to-Astro Migration Tool',
            'Accept': 'application/json'
        }
        assert headers == expected
    
    def test_get_headers_with_auth(self):
        """Test header generation with authentication."""
        agent = ExtractionAgent("https://example.com", "user", "pass")
        headers = agent.get_headers()
        
        assert 'Authorization' in headers
        assert headers['User-Agent'] == 'WordPress-to-Astro Migration Tool'
        assert headers['Accept'] == 'application/json'
    
    @patch('extraction_agent.requests.get')
    def test_fetch_posts_success(self, mock_get):
        """Test successful post fetching."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [self.sample_post_data]
        mock_response.headers = {'X-WP-TotalPages': '1'}
        mock_get.return_value = mock_response
        
        posts = self.agent.fetch_posts()
        
        assert len(posts) == 1
        assert isinstance(posts[0], WPPost)
        assert posts[0].title == "Test Post Title"
        assert posts[0].slug == "test-post-title"
        assert posts[0].wp_id == 123
    
    @patch('extraction_agent.requests.get')
    def test_fetch_posts_with_pagination(self, mock_get):
        """Test post fetching with multiple pages."""
        # Mock responses for pagination
        response1 = Mock()
        response1.status_code = 200
        response1.json.return_value = [self.sample_post_data]
        response1.headers = {'X-WP-TotalPages': '2'}
        
        response2 = Mock()
        response2.status_code = 200
        response2.json.return_value = [{**self.sample_post_data, "id": 124, "slug": "second-post"}]
        response2.headers = {'X-WP-TotalPages': '2'}
        
        mock_get.side_effect = [response1, response2]
        
        posts = self.agent.fetch_posts()
        
        assert len(posts) == 2
        assert posts[0].wp_id == 123
        assert posts[1].wp_id == 124
        assert mock_get.call_count == 2
    
    @patch('extraction_agent.requests.get')
    def test_fetch_posts_api_error(self, mock_get):
        """Test handling of API errors during post fetching."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response
        
        with pytest.raises(Exception) as exc_info:
            self.agent.fetch_posts()
        
        assert "Error fetching posts" in str(exc_info.value)
        assert "404" in str(exc_info.value)
    
    @patch('extraction_agent.requests.get')
    def test_fetch_pages_success(self, mock_get):
        """Test successful page fetching."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [self.sample_page_data]
        mock_response.headers = {'X-WP-TotalPages': '1'}
        mock_get.return_value = mock_response
        
        pages = self.agent.fetch_pages()
        
        assert len(pages) == 1
        assert isinstance(pages[0], WPPage)
        assert pages[0].title == "Test Page Title"
        assert pages[0].slug == "test-page-title"
        assert pages[0].wp_id == 456
    
    @patch('extraction_agent.requests.get')
    def test_fetch_categories_success(self, mock_get):
        """Test successful category fetching."""
        mock_categories = [
            {"id": 1, "name": "Technology", "slug": "technology"},
            {"id": 2, "name": "Travel", "slug": "travel"}
        ]
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_categories
        mock_get.return_value = mock_response
        
        categories = self.agent.fetch_categories()
        
        assert len(categories) == 2
        assert categories[1] == "Technology"
        assert categories[2] == "Travel"
    
    @patch('extraction_agent.requests.get')
    def test_fetch_tags_success(self, mock_get):
        """Test successful tag fetching."""
        mock_tags = [
            {"id": 3, "name": "Python", "slug": "python"},
            {"id": 4, "name": "Tutorial", "slug": "tutorial"}
        ]
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_tags
        mock_get.return_value = mock_response
        
        tags = self.agent.fetch_tags()
        
        assert len(tags) == 2
        assert tags[3] == "Python"
        assert tags[4] == "Tutorial"
    
    @patch('extraction_agent.requests.get')
    def test_fetch_site_info_success(self, mock_get):
        """Test successful site info fetching."""
        mock_site_info = {
            "name": "Test Site",
            "description": "A test WordPress site",
            "url": "https://example.com",
            "home": "https://example.com"
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_site_info
        mock_get.return_value = mock_response
        
        site_info = self.agent.fetch_site_info()
        
        assert site_info["name"] == "Test Site"
        assert site_info["description"] == "A test WordPress site"
        assert site_info["url"] == "https://example.com"
    
    @patch.object(ExtractionAgent, 'fetch_posts')
    @patch.object(ExtractionAgent, 'fetch_pages')
    @patch.object(ExtractionAgent, 'fetch_categories')
    @patch.object(ExtractionAgent, 'fetch_tags')
    @patch.object(ExtractionAgent, 'fetch_site_info')
    def test_extract_all_content_success(self, mock_site_info, mock_tags, 
                                       mock_categories, mock_pages, mock_posts):
        """Test complete content extraction."""
        # Setup mocks
        mock_posts.return_value = [WPPost(**{
            "wp_id": 123,
            "title": "Test Post",
            "content": "<p>Content</p>",
            "excerpt": "<p>Excerpt</p>",
            "date": datetime(2024, 1, 15),
            "slug": "test-post",
            "categories": [1],
            "tags": [3],
            "featured_media": 567,
            "link": "https://example.com/test-post"
        })]
        
        mock_pages.return_value = [WPPage(**{
            "wp_id": 456,
            "title": "Test Page",
            "content": "<p>Page content</p>",
            "excerpt": "<p>Page excerpt</p>",
            "date": datetime(2024, 1, 16),
            "slug": "test-page",
            "link": "https://example.com/test-page"
        })]
        
        mock_categories.return_value = {1: "Technology"}
        mock_tags.return_value = {3: "Python"}
        mock_site_info.return_value = {"name": "Test Site"}
        
        bundle = self.agent.extract_all_content()
        
        assert isinstance(bundle, WPContentBundle)
        assert len(bundle.posts) == 1
        assert len(bundle.pages) == 1
        assert bundle.categories == {1: "Technology"}
        assert bundle.tags == {3: "Python"}
        assert bundle.site_info["name"] == "Test Site"
    
    def test_wp_post_model_validation(self):
        """Test WPPost model validation and creation."""
        post_data = {
            "wp_id": 123,
            "title": "Test Post",
            "content": "<p>Content</p>",
            "excerpt": "<p>Excerpt</p>",
            "date": datetime(2024, 1, 15),
            "slug": "test-post",
            "categories": [1, 2],
            "tags": [3, 4],
            "featured_media": 567,
            "link": "https://example.com/test-post"
        }
        
        post = WPPost(**post_data)
        
        assert post.wp_id == 123
        assert post.title == "Test Post"
        assert post.categories == [1, 2]
        assert post.tags == [3, 4]
        assert isinstance(post.date, datetime)
    
    def test_wp_page_model_validation(self):
        """Test WPPage model validation and creation."""
        page_data = {
            "wp_id": 456,
            "title": "Test Page",
            "content": "<p>Page content</p>",
            "excerpt": "<p>Page excerpt</p>",
            "date": datetime(2024, 1, 16),
            "slug": "test-page",
            "link": "https://example.com/test-page"
        }
        
        page = WPPage(**page_data)
        
        assert page.wp_id == 456
        assert page.title == "Test Page"
        assert isinstance(page.date, datetime)
    
    def test_wp_content_bundle_model(self):
        """Test WPContentBundle model validation."""
        bundle_data = {
            "posts": [],
            "pages": [],
            "categories": {1: "Technology"},
            "tags": {3: "Python"},
            "site_info": {"name": "Test Site"}
        }
        
        bundle = WPContentBundle(**bundle_data)
        
        assert isinstance(bundle.posts, list)
        assert isinstance(bundle.pages, list)
        assert bundle.categories[1] == "Technology"
        assert bundle.tags[3] == "Python"


class TestConvenienceFunction:
    """Test the convenience function for extraction."""
    
    @patch.object(ExtractionAgent, 'extract_all_content')
    def test_extract_from_wordpress_no_auth(self, mock_extract):
        """Test convenience function without authentication."""
        mock_bundle = WPContentBundle(
            posts=[], pages=[], categories={}, tags={}, site_info={}
        )
        mock_extract.return_value = mock_bundle
        
        result = extract_from_wordpress("https://example.com")
        
        assert isinstance(result, WPContentBundle)
        mock_extract.assert_called_once()
    
    @patch.object(ExtractionAgent, 'extract_all_content')
    def test_extract_from_wordpress_with_auth(self, mock_extract):
        """Test convenience function with authentication."""
        mock_bundle = WPContentBundle(
            posts=[], pages=[], categories={}, tags={}, site_info={}
        )
        mock_extract.return_value = mock_bundle
        
        result = extract_from_wordpress(
            "https://example.com", 
            username="user", 
            password="pass"
        )
        
        assert isinstance(result, WPContentBundle)
        mock_extract.assert_called_once()


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_invalid_site_url(self):
        """Test handling of invalid site URLs."""
        with pytest.raises(ValueError):
            ExtractionAgent("")
        
        with pytest.raises(ValueError):
            ExtractionAgent("not-a-url")
    
    @patch('extraction_agent.requests.get')
    def test_network_timeout(self, mock_get):
        """Test handling of network timeouts."""
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        agent = ExtractionAgent("https://example.com")
        
        with pytest.raises(Exception) as exc_info:
            agent.fetch_posts()
        
        assert "timeout" in str(exc_info.value).lower()
    
    @patch('extraction_agent.requests.get')
    def test_connection_error(self, mock_get):
        """Test handling of connection errors."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        agent = ExtractionAgent("https://example.com")
        
        with pytest.raises(Exception) as exc_info:
            agent.fetch_posts()
        
        assert "connection" in str(exc_info.value).lower()
    
    @patch('extraction_agent.requests.get')
    def test_malformed_json_response(self, mock_get):
        """Test handling of malformed JSON responses."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_get.return_value = mock_response
        
        agent = ExtractionAgent("https://example.com")
        
        with pytest.raises(Exception) as exc_info:
            agent.fetch_posts()
        
        assert "json" in str(exc_info.value).lower()


class TestRealWorldScenarios:
    """Integration-style tests with realistic data."""
    
    def test_wordpress_com_api_structure(self):
        """Test handling of WordPress.com API structure differences."""
        # WordPress.com sometimes has different response structures
        wp_com_post = {
            "ID": 123,  # Note: uppercase ID instead of lowercase
            "title": "Test Post",  # Sometimes not wrapped in 'rendered'
            "content": "<p>Content</p>",
            "excerpt": "<p>Excerpt</p>",
            "date": "2024-01-15T10:00:00+00:00",  # Different date format
            "slug": "test-post",
            "categories": {"Technology": {"ID": 1, "name": "Technology"}},
            "tags": {"Python": {"ID": 3, "name": "Python"}},
            "featured_image": "https://example.com/image.jpg",
            "URL": "https://example.com/test-post"
        }
        
        # This test documents the need for flexible parsing
        # Real implementation might need to handle these variations
    
    def test_large_content_extraction(self):
        """Test extraction of large amounts of content."""
        agent = ExtractionAgent("https://example.com")
        
        # Simulate large content with many posts/pages
        large_content_scenario = {
            "posts_count": 500,
            "pages_count": 50,
            "categories_count": 20,
            "tags_count": 100
        }
        
        # This test documents performance considerations
        # Real implementation should handle pagination efficiently


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
