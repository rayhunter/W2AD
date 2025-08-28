#!/usr/bin/env python3
"""
Pytest tests for TransformAgent - WordPress to Astro content transformation functionality.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from transform_agent import TransformAgent, MarkdownPost, MarkdownPage, StaticContentBundle, transform_bundle
from extraction_agent import WPPost, WPPage, WPContentBundle


class TestTransformAgent:
    """Test suite for TransformAgent class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = TransformAgent()
        
        self.sample_wp_post = WPPost(
            wp_id=123,
            title="Test Post Title",
            content="<p>This is <strong>HTML</strong> content with <a href='https://example.com'>links</a>.</p>",
            excerpt="<p>Test excerpt</p>",
            date=datetime(2024, 1, 15, 10, 0),
            slug="test-post-title",
            categories=[1, 2],
            tags=[3, 4],
            featured_media=567,
            link="https://example.com/test-post-title"
        )
        
        self.sample_wp_page = WPPage(
            wp_id=456,
            title="Test Page Title",
            content="<h1>Page Header</h1><p>Page content with <em>formatting</em>.</p>",
            excerpt="<p>Page excerpt</p>",
            date=datetime(2024, 1, 16, 11, 0),
            slug="test-page-title",
            link="https://example.com/test-page-title"
        )
    
    def test_initialization(self):
        """Test agent initialization."""
        agent = TransformAgent()
        assert agent is not None
    
    def test_html_to_markdown_conversion(self):
        """Test HTML to Markdown conversion."""
        html_content = "<p>This is <strong>bold</strong> and <em>italic</em> text.</p>"
        markdown = self.agent.html_to_markdown(html_content)
        
        # Check that HTML tags are converted
        assert "<p>" not in markdown
        assert "<strong>" not in markdown
        assert "<em>" not in markdown
        
        # Check that Markdown formatting is present
        assert "**bold**" in markdown or "_bold_" in markdown
        assert "*italic*" in markdown or "_italic_" in markdown
    
    def test_html_to_markdown_with_links(self):
        """Test HTML to Markdown conversion with links."""
        html_content = '<p>Check out <a href="https://example.com">this link</a>.</p>'
        markdown = self.agent.html_to_markdown(html_content)
        
        # Should convert to Markdown link format
        assert "[this link](https://example.com)" in markdown
        assert "<a href=" not in markdown
    
    def test_html_to_markdown_with_images(self):
        """Test HTML to Markdown conversion with images."""
        html_content = '<p>Here is an image: <img src="image.jpg" alt="Test Image" /></p>'
        markdown = self.agent.html_to_markdown(html_content)
        
        # Should convert to Markdown image format
        assert "![Test Image](image.jpg)" in markdown
        assert "<img" not in markdown
    
    def test_html_to_markdown_with_lists(self):
        """Test HTML to Markdown conversion with lists."""
        html_content = """
        <ul>
            <li>First item</li>
            <li>Second item</li>
        </ul>
        """
        markdown = self.agent.html_to_markdown(html_content)
        
        # Should convert to Markdown list format
        assert "- First item" in markdown or "* First item" in markdown
        assert "- Second item" in markdown or "* Second item" in markdown
        assert "<ul>" not in markdown
        assert "<li>" not in markdown
    
    def test_create_frontmatter_basic(self):
        """Test basic frontmatter creation."""
        frontmatter = self.agent.create_frontmatter(
            title="Test Title",
            date=datetime(2024, 1, 15, 10, 0),
            slug="test-title"
        )
        
        assert "---" in frontmatter
        assert "title: 'Test Title'" in frontmatter
        assert "date: '2024-01-15T10:00:00'" in frontmatter
        assert "slug: test-title" in frontmatter
    
    def test_create_frontmatter_with_categories_and_tags(self):
        """Test frontmatter creation with categories and tags."""
        frontmatter = self.agent.create_frontmatter(
            title="Test Title",
            date=datetime(2024, 1, 15, 10, 0),
            slug="test-title",
            categories=["Technology", "Web Development"],
            tags=["Python", "Tutorial"]
        )
        
        assert "categories:" in frontmatter
        assert "- Technology" in frontmatter
        assert "- Web Development" in frontmatter
        assert "tags:" in frontmatter
        assert "- Python" in frontmatter
        assert "- Tutorial" in frontmatter
    
    def test_create_frontmatter_with_image(self):
        """Test frontmatter creation with featured image."""
        frontmatter = self.agent.create_frontmatter(
            title="Test Title",
            date=datetime(2024, 1, 15, 10, 0),
            slug="test-title",
            image="https://example.com/image.jpg"
        )
        
        assert "image: https://example.com/image.jpg" in frontmatter
    
    def test_transform_post_basic(self):
        """Test basic post transformation."""
        markdown_post = self.agent.transform_post(self.sample_wp_post)
        
        assert isinstance(markdown_post, MarkdownPost)
        assert markdown_post.title == "Test Post Title"
        assert markdown_post.slug == "test-post-title"
        assert markdown_post.date == self.sample_wp_post.date
        
        # Check that HTML is converted to Markdown
        assert "<p>" not in markdown_post.content
        assert "**HTML**" in markdown_post.content or "_HTML_" in markdown_post.content
    
    def test_transform_post_with_categories_and_tags(self):
        """Test post transformation with category and tag resolution."""
        # Mock category and tag lookup
        with patch.object(self.agent, 'get_category_names') as mock_categories, \
             patch.object(self.agent, 'get_tag_names') as mock_tags:
            
            mock_categories.return_value = ["Technology", "Web Development"]
            mock_tags.return_value = ["Python", "Tutorial"]
            
            markdown_post = self.agent.transform_post(self.sample_wp_post)
            
            assert markdown_post.categories == ["Technology", "Web Development"]
            assert markdown_post.tags == ["Python", "Tutorial"]
    
    def test_transform_page_basic(self):
        """Test basic page transformation."""
        markdown_page = self.agent.transform_page(self.sample_wp_page)
        
        assert isinstance(markdown_page, MarkdownPage)
        assert markdown_page.title == "Test Page Title"
        assert markdown_page.slug == "test-page-title"
        assert markdown_page.date == self.sample_wp_page.date
        
        # Check that HTML is converted to Markdown
        assert "<h1>" not in markdown_page.content
        assert "<p>" not in markdown_page.content
        assert "# Page Header" in markdown_page.content
    
    @patch('transform_agent.sanitize_content')
    def test_content_sanitization_integration(self, mock_sanitize):
        """Test that content sanitization is applied during transformation."""
        mock_sanitize.return_value = "Sanitized content"
        
        markdown_post = self.agent.transform_post(self.sample_wp_post)
        
        # Verify sanitization was called
        mock_sanitize.assert_called()
        assert markdown_post.content == "Sanitized content"
    
    def test_create_content_files_structure(self):
        """Test creation of content files structure for scaffold agent."""
        posts = [
            MarkdownPost(
                title="Post 1",
                content="Content 1",
                date=datetime(2024, 1, 15),
                slug="post-1",
                categories=["Tech"],
                tags=["Python"],
                image=None
            ),
            MarkdownPost(
                title="Post 2",
                content="Content 2",
                date=datetime(2024, 1, 16),
                slug="post-2",
                categories=["Travel"],
                tags=["Adventure"],
                image=None
            )
        ]
        
        pages = [
            MarkdownPage(
                title="About",
                content="About content",
                date=datetime(2024, 1, 15),
                slug="about",
                image=None
            )
        ]
        
        bundle = StaticContentBundle(posts=posts, pages=pages)
        content_files = self.agent.create_content_files(bundle)
        
        assert "posts" in content_files
        assert "pages" in content_files
        assert len(content_files["posts"]) == 2
        assert len(content_files["pages"]) == 1
        
        # Check file structure
        post_file = content_files["posts"][0]
        assert post_file["path"] == "src/content/blog/post-1.md"
        assert "title: 'Post 1'" in post_file["content"]
        assert "Content 1" in post_file["content"]
        
        page_file = content_files["pages"][0]
        assert page_file["path"] == "src/content/pages/about.md"
        assert "title: 'About'" in page_file["content"]
        assert "About content" in page_file["content"]
    
    def test_transform_bundle_complete(self):
        """Test complete bundle transformation."""
        wp_bundle = WPContentBundle(
            posts=[self.sample_wp_post],
            pages=[self.sample_wp_page],
            categories={1: "Technology", 2: "Web Development"},
            tags={3: "Python", 4: "Tutorial"},
            site_info={"name": "Test Site"}
        )
        
        with patch.object(self.agent, 'get_category_names') as mock_categories, \
             patch.object(self.agent, 'get_tag_names') as mock_tags:
            
            mock_categories.return_value = ["Technology", "Web Development"]
            mock_tags.return_value = ["Python", "Tutorial"]
            
            static_bundle = self.agent.transform_bundle(wp_bundle)
            
            assert isinstance(static_bundle, StaticContentBundle)
            assert len(static_bundle.posts) == 1
            assert len(static_bundle.pages) == 1
            
            # Check post transformation
            post = static_bundle.posts[0]
            assert post.title == "Test Post Title"
            assert post.categories == ["Technology", "Web Development"]
            assert post.tags == ["Python", "Tutorial"]
            
            # Check page transformation
            page = static_bundle.pages[0]
            assert page.title == "Test Page Title"


class TestMarkdownPostModel:
    """Test MarkdownPost model validation."""
    
    def test_markdown_post_creation(self):
        """Test MarkdownPost model creation and validation."""
        post_data = {
            "title": "Test Post",
            "content": "# Test Content\n\nThis is markdown content.",
            "date": datetime(2024, 1, 15, 10, 0),
            "slug": "test-post",
            "categories": ["Technology"],
            "tags": ["Python"],
            "image": "https://example.com/image.jpg"
        }
        
        post = MarkdownPost(**post_data)
        
        assert post.title == "Test Post"
        assert post.slug == "test-post"
        assert post.categories == ["Technology"]
        assert post.tags == ["Python"]
        assert post.image == "https://example.com/image.jpg"
        assert isinstance(post.date, datetime)
    
    def test_markdown_post_optional_fields(self):
        """Test MarkdownPost with optional fields."""
        minimal_data = {
            "title": "Minimal Post",
            "content": "Content",
            "date": datetime(2024, 1, 15),
            "slug": "minimal-post"
        }
        
        post = MarkdownPost(**minimal_data)
        
        assert post.categories == []
        assert post.tags == []
        assert post.image is None


class TestMarkdownPageModel:
    """Test MarkdownPage model validation."""
    
    def test_markdown_page_creation(self):
        """Test MarkdownPage model creation and validation."""
        page_data = {
            "title": "Test Page",
            "content": "# Test Page\n\nThis is page content.",
            "date": datetime(2024, 1, 15, 10, 0),
            "slug": "test-page",
            "image": "https://example.com/page-image.jpg"
        }
        
        page = MarkdownPage(**page_data)
        
        assert page.title == "Test Page"
        assert page.slug == "test-page"
        assert page.image == "https://example.com/page-image.jpg"
        assert isinstance(page.date, datetime)
    
    def test_markdown_page_minimal(self):
        """Test MarkdownPage with minimal required fields."""
        minimal_data = {
            "title": "Minimal Page",
            "content": "Content",
            "date": datetime(2024, 1, 15),
            "slug": "minimal-page"
        }
        
        page = MarkdownPage(**minimal_data)
        
        assert page.image is None


class TestStaticContentBundleModel:
    """Test StaticContentBundle model validation."""
    
    def test_static_content_bundle_creation(self):
        """Test StaticContentBundle model creation."""
        posts = [
            MarkdownPost(
                title="Post 1",
                content="Content 1",
                date=datetime(2024, 1, 15),
                slug="post-1"
            )
        ]
        
        pages = [
            MarkdownPage(
                title="Page 1",
                content="Page Content 1",
                date=datetime(2024, 1, 15),
                slug="page-1"
            )
        ]
        
        bundle = StaticContentBundle(posts=posts, pages=pages)
        
        assert len(bundle.posts) == 1
        assert len(bundle.pages) == 1
        assert isinstance(bundle.posts[0], MarkdownPost)
        assert isinstance(bundle.pages[0], MarkdownPage)


class TestConvenienceFunction:
    """Test the convenience function for transformation."""
    
    @patch.object(TransformAgent, 'transform_bundle')
    def test_transform_bundle_convenience_function(self, mock_transform):
        """Test the convenience transform_bundle function."""
        wp_bundle = WPContentBundle(
            posts=[], pages=[], categories={}, tags={}, site_info={}
        )
        
        mock_static_bundle = StaticContentBundle(posts=[], pages=[])
        mock_transform.return_value = mock_static_bundle
        
        result = transform_bundle(wp_bundle)
        
        assert isinstance(result, StaticContentBundle)
        mock_transform.assert_called_once_with(wp_bundle)


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_invalid_html_content(self):
        """Test handling of malformed HTML content."""
        agent = TransformAgent()
        
        # Test with severely malformed HTML
        malformed_html = "<p>Unclosed paragraph<div>Nested without closing<span>More nesting"
        
        # Should not raise an exception, html2text is generally robust
        markdown = agent.html_to_markdown(malformed_html)
        assert isinstance(markdown, str)
    
    def test_empty_content(self):
        """Test handling of empty content."""
        agent = TransformAgent()
        
        empty_post = WPPost(
            wp_id=123,
            title="Empty Post",
            content="",
            excerpt="",
            date=datetime(2024, 1, 15),
            slug="empty-post",
            categories=[],
            tags=[],
            featured_media=0,
            link="https://example.com/empty-post"
        )
        
        markdown_post = agent.transform_post(empty_post)
        
        assert markdown_post.title == "Empty Post"
        assert markdown_post.content == ""
    
    def test_unicode_content(self):
        """Test handling of Unicode content."""
        agent = TransformAgent()
        
        unicode_content = "<p>Content with émojis 🚀 and spéciál characters ñáéíóú</p>"
        markdown = agent.html_to_markdown(unicode_content)
        
        # Should preserve Unicode characters
        assert "🚀" in markdown
        assert "émojis" in markdown
        assert "spéciál" in markdown
        assert "ñáéíóú" in markdown


class TestRealWorldScenarios:
    """Integration-style tests with realistic content."""
    
    def test_wordpress_shortcodes_handling(self):
        """Test handling of WordPress shortcodes."""
        agent = TransformAgent()
        
        content_with_shortcodes = """
        <p>This is content with shortcodes:</p>
        [gallery ids="1,2,3"]
        [caption id="attachment_123" align="aligncenter" width="300"]Image caption[/caption]
        [youtube https://www.youtube.com/watch?v=abc123]
        """
        
        markdown = agent.html_to_markdown(content_with_shortcodes)
        
        # Shortcodes should be preserved or converted appropriately
        # This test documents the expected behavior
        assert isinstance(markdown, str)
    
    def test_complex_nested_html(self):
        """Test transformation of complex nested HTML structures."""
        agent = TransformAgent()
        
        complex_html = """
        <div class="content-wrapper">
            <h2>Section Title</h2>
            <p>Introduction paragraph with <strong>bold text</strong>.</p>
            <ul>
                <li>First item with <a href="https://example.com">link</a></li>
                <li>Second item with <em>italic text</em></li>
            </ul>
            <blockquote>
                <p>This is a quote with <code>inline code</code>.</p>
            </blockquote>
            <pre><code>
            def example_function():
                return "Hello, World!"
            </code></pre>
        </div>
        """
        
        markdown = agent.html_to_markdown(complex_html)
        
        # Check that structure is preserved
        assert "## Section Title" in markdown
        assert "**bold text**" in markdown or "_bold text_" in markdown
        assert "[link](https://example.com)" in markdown
        assert "*italic text*" in markdown or "_italic text_" in markdown
        assert "> This is a quote" in markdown
    
    def test_large_content_transformation(self):
        """Test transformation of large content pieces."""
        agent = TransformAgent()
        
        # Simulate a large blog post
        large_content = "<p>" + "Very long content. " * 1000 + "</p>"
        
        markdown = agent.html_to_markdown(large_content)
        
        # Should handle large content without issues
        assert len(markdown) > 0
        assert "Very long content." in markdown


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
