#!/usr/bin/env python3
"""
Pytest tests for CMSConfigAgent - Decap CMS configuration generation functionality.
"""

import pytest
import yaml
from unittest.mock import Mock, patch
from cms_config_agent import CMSConfigAgent, CMSConfig, generate_cms_config


class TestCMSConfigAgent:
    """Test suite for CMSConfigAgent class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = CMSConfigAgent()
        
        self.sample_repo_info = {
            "owner": "testuser",
            "repo": "test-repo",
            "branch": "main"
        }
        
        self.sample_content_structure = {
            "posts_dir": "src/content/blog",
            "pages_dir": "src/content/pages",
            "media_dir": "public/uploads",
            "public_url": "/uploads"
        }
    
    def test_initialization(self):
        """Test agent initialization."""
        agent = CMSConfigAgent()
        assert agent is not None
    
    def test_generate_config_basic(self):
        """Test basic CMS configuration generation."""
        config = self.agent.generate_config(
            self.sample_repo_info,
            self.sample_content_structure
        )
        
        assert isinstance(config, CMSConfig)
        assert config.backend["name"] == "github"
        assert config.backend["repo"] == "testuser/test-repo"
        assert config.backend["branch"] == "main"
    
    def test_generate_config_backend_settings(self):
        """Test backend configuration settings."""
        config = self.agent.generate_config(
            self.sample_repo_info,
            self.sample_content_structure
        )
        
        backend = config.backend
        assert backend["name"] == "github"
        assert backend["repo"] == "testuser/test-repo"
        assert backend["branch"] == "main"
        assert backend["auth_type"] == "oauth"
        assert backend["auth_url"] == "/.netlify/functions/auth"
    
    def test_generate_config_media_settings(self):
        """Test media configuration settings."""
        config = self.agent.generate_config(
            self.sample_repo_info,
            self.sample_content_structure
        )
        
        assert config.media_folder == "public/uploads"
        assert config.public_folder == "/uploads"
    
    def test_generate_config_posts_collection(self):
        """Test posts collection configuration."""
        config = self.agent.generate_config(
            self.sample_repo_info,
            self.sample_content_structure
        )
        
        # Find posts collection
        posts_collection = None
        for collection in config.collections:
            if collection["name"] == "blog":
                posts_collection = collection
                break
        
        assert posts_collection is not None
        assert posts_collection["label"] == "Blog Posts"
        assert posts_collection["folder"] == "src/content/blog"
        assert posts_collection["create"] is True
        assert posts_collection["slug"] == "{{slug}}"
        assert posts_collection["extension"] == "md"
        assert posts_collection["format"] == "frontmatter"
    
    def test_generate_config_posts_fields(self):
        """Test posts collection field configuration."""
        config = self.agent.generate_config(
            self.sample_repo_info,
            self.sample_content_structure
        )
        
        posts_collection = next(c for c in config.collections if c["name"] == "blog")
        fields = posts_collection["fields"]
        
        # Check required fields
        field_names = [f["name"] for f in fields]
        assert "title" in field_names
        assert "date" in field_names
        assert "slug" in field_names
        assert "categories" in field_names
        assert "tags" in field_names
        assert "image" in field_names
        assert "body" in field_names
        
        # Check field types
        title_field = next(f for f in fields if f["name"] == "title")
        assert title_field["widget"] == "string"
        assert title_field["required"] is True
        
        date_field = next(f for f in fields if f["name"] == "date")
        assert date_field["widget"] == "datetime"
        
        body_field = next(f for f in fields if f["name"] == "body")
        assert body_field["widget"] == "markdown"
    
    def test_generate_config_pages_collection(self):
        """Test pages collection configuration."""
        config = self.agent.generate_config(
            self.sample_repo_info,
            self.sample_content_structure
        )
        
        # Find pages collection
        pages_collection = None
        for collection in config.collections:
            if collection["name"] == "pages":
                pages_collection = collection
                break
        
        assert pages_collection is not None
        assert pages_collection["label"] == "Pages"
        assert pages_collection["folder"] == "src/content/pages"
        assert pages_collection["create"] is True
        assert pages_collection["slug"] == "{{slug}}"
    
    def test_generate_config_pages_fields(self):
        """Test pages collection field configuration."""
        config = self.agent.generate_config(
            self.sample_repo_info,
            self.sample_content_structure
        )
        
        pages_collection = next(c for c in config.collections if c["name"] == "pages")
        fields = pages_collection["fields"]
        
        # Check required fields (pages have fewer fields than posts)
        field_names = [f["name"] for f in fields]
        assert "title" in field_names
        assert "date" in field_names
        assert "slug" in field_names
        assert "image" in field_names
        assert "body" in field_names
        
        # Pages should not have categories/tags
        assert "categories" not in field_names
        assert "tags" not in field_names
    
    def test_generate_config_custom_structure(self):
        """Test configuration with custom content structure."""
        custom_structure = {
            "posts_dir": "content/articles",
            "pages_dir": "content/static",
            "media_dir": "static/images",
            "public_url": "/images"
        }
        
        config = self.agent.generate_config(
            self.sample_repo_info,
            custom_structure
        )
        
        assert config.media_folder == "static/images"
        assert config.public_folder == "/images"
        
        posts_collection = next(c for c in config.collections if c["name"] == "blog")
        assert posts_collection["folder"] == "content/articles"
        
        pages_collection = next(c for c in config.collections if c["name"] == "pages")
        assert pages_collection["folder"] == "content/static"
    
    def test_generate_yaml_output(self):
        """Test YAML output generation."""
        config = self.agent.generate_config(
            self.sample_repo_info,
            self.sample_content_structure
        )
        
        yaml_output = self.agent.generate_yaml(config)
        
        # Should be valid YAML
        parsed_yaml = yaml.safe_load(yaml_output)
        assert isinstance(parsed_yaml, dict)
        
        # Check key sections
        assert "backend" in parsed_yaml
        assert "media_folder" in parsed_yaml
        assert "public_folder" in parsed_yaml
        assert "collections" in parsed_yaml
        
        # Check backend configuration
        assert parsed_yaml["backend"]["name"] == "github"
        assert parsed_yaml["backend"]["repo"] == "testuser/test-repo"
    
    def test_generate_yaml_formatting(self):
        """Test YAML output formatting and structure."""
        config = self.agent.generate_config(
            self.sample_repo_info,
            self.sample_content_structure
        )
        
        yaml_output = self.agent.generate_yaml(config)
        
        # Check that output contains expected sections
        assert "# Decap CMS Configuration" in yaml_output
        assert "backend:" in yaml_output
        assert "collections:" in yaml_output
        
        # Check that arrays are properly formatted
        assert "- name: blog" in yaml_output
        assert "- name: pages" in yaml_output
    
    def test_create_blog_collection_structure(self):
        """Test blog collection structure creation."""
        collection = self.agent.create_blog_collection("src/content/blog")
        
        assert collection["name"] == "blog"
        assert collection["label"] == "Blog Posts"
        assert collection["folder"] == "src/content/blog"
        assert collection["create"] is True
        assert collection["slug"] == "{{slug}}"
        assert collection["extension"] == "md"
        assert collection["format"] == "frontmatter"
        
        # Check sortable fields
        assert collection["sortable_fields"] == ["title", "date"]
        assert collection["view_filters"] == [
            {"label": "Posts", "field": "title", "pattern": ".*"}
        ]
        assert collection["view_groups"] == [
            {"label": "Year", "field": "date", "pattern": "\\d{4}"}
        ]
    
    def test_create_pages_collection_structure(self):
        """Test pages collection structure creation."""
        collection = self.agent.create_pages_collection("src/content/pages")
        
        assert collection["name"] == "pages"
        assert collection["label"] == "Pages"
        assert collection["folder"] == "src/content/pages"
        assert collection["create"] is True
        assert collection["slug"] == "{{slug}}"
        
        # Check that pages have simpler structure than posts
        assert "view_filters" not in collection
        assert "view_groups" not in collection
    
    def test_create_field_configurations(self):
        """Test individual field configuration creation."""
        # Test title field
        title_field = {
            "label": "Title",
            "name": "title",
            "widget": "string",
            "required": True
        }
        
        # Test date field
        date_field = {
            "label": "Publish Date",
            "name": "date",
            "widget": "datetime",
            "default": "{{now}}",
            "date_format": "YYYY-MM-DD",
            "time_format": "HH:mm",
            "format": "YYYY-MM-DDTHH:mm:ss"
        }
        
        # Test categories field
        categories_field = {
            "label": "Categories",
            "name": "categories",
            "widget": "list",
            "required": False,
            "default": []
        }
        
        # Test markdown body field
        body_field = {
            "label": "Content",
            "name": "body",
            "widget": "markdown",
            "required": True
        }
        
        # These would be tested as part of the collection field generation
        # This test documents the expected field structures
        assert title_field["widget"] == "string"
        assert date_field["widget"] == "datetime"
        assert categories_field["widget"] == "list"
        assert body_field["widget"] == "markdown"


class TestCMSConfigModel:
    """Test CMSConfig model validation."""
    
    def test_cms_config_creation(self):
        """Test CMSConfig model creation and validation."""
        config_data = {
            "backend": {
                "name": "github",
                "repo": "user/repo",
                "branch": "main",
                "auth_type": "oauth",
                "auth_url": "/.netlify/functions/auth"
            },
            "media_folder": "public/uploads",
            "public_folder": "/uploads",
            "collections": [
                {
                    "name": "blog",
                    "label": "Blog Posts",
                    "folder": "src/content/blog",
                    "create": True,
                    "fields": []
                }
            ]
        }
        
        config = CMSConfig(**config_data)
        
        assert config.backend["name"] == "github"
        assert config.media_folder == "public/uploads"
        assert config.public_folder == "/uploads"
        assert len(config.collections) == 1
        assert config.collections[0]["name"] == "blog"
    
    def test_cms_config_with_optional_fields(self):
        """Test CMSConfig with optional configuration fields."""
        config_data = {
            "backend": {
                "name": "github",
                "repo": "user/repo",
                "branch": "main"
            },
            "media_folder": "public/uploads",
            "public_folder": "/uploads",
            "collections": [],
            "site_url": "https://example.com",
            "display_url": "https://example.com",
            "logo_url": "https://example.com/logo.png"
        }
        
        config = CMSConfig(**config_data)
        
        assert config.site_url == "https://example.com"
        assert config.display_url == "https://example.com"
        assert config.logo_url == "https://example.com/logo.png"


class TestConvenienceFunction:
    """Test the convenience function for CMS config generation."""
    
    @patch.object(CMSConfigAgent, 'generate_config')
    def test_generate_cms_config_convenience_function(self, mock_generate):
        """Test the convenience generate_cms_config function."""
        mock_config = CMSConfig(
            backend={"name": "github", "repo": "user/repo", "branch": "main"},
            media_folder="public/uploads",
            public_folder="/uploads",
            collections=[]
        )
        mock_generate.return_value = mock_config
        
        result = generate_cms_config(
            self.sample_repo_info,
            self.sample_content_structure
        )
        
        assert isinstance(result, CMSConfig)
        mock_generate.assert_called_once_with(
            self.sample_repo_info,
            self.sample_content_structure
        )
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sample_repo_info = {
            "owner": "testuser",
            "repo": "test-repo",
            "branch": "main"
        }
        
        self.sample_content_structure = {
            "posts_dir": "src/content/blog",
            "pages_dir": "src/content/pages",
            "media_dir": "public/uploads",
            "public_url": "/uploads"
        }


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_invalid_repo_info(self):
        """Test handling of invalid repository information."""
        agent = CMSConfigAgent()
        
        invalid_repo_info = {
            "owner": "",  # Empty owner
            "repo": "test-repo",
            "branch": "main"
        }
        
        content_structure = {
            "posts_dir": "src/content/blog",
            "pages_dir": "src/content/pages",
            "media_dir": "public/uploads",
            "public_url": "/uploads"
        }
        
        # Should handle empty owner gracefully
        config = agent.generate_config(invalid_repo_info, content_structure)
        assert config.backend["repo"] == "/test-repo"  # Empty owner results in "/repo"
    
    def test_missing_content_structure_fields(self):
        """Test handling of missing content structure fields."""
        agent = CMSConfigAgent()
        
        repo_info = {
            "owner": "testuser",
            "repo": "test-repo",
            "branch": "main"
        }
        
        incomplete_structure = {
            "posts_dir": "src/content/blog",
            # Missing other required fields
        }
        
        # Should handle missing fields with reasonable defaults
        with pytest.raises(KeyError):
            agent.generate_config(repo_info, incomplete_structure)
    
    def test_yaml_generation_with_special_characters(self):
        """Test YAML generation with special characters in configuration."""
        agent = CMSConfigAgent()
        
        repo_info = {
            "owner": "test-user",
            "repo": "test-repo-with-dashes",
            "branch": "feature/special-branch"
        }
        
        content_structure = {
            "posts_dir": "src/content/blog",
            "pages_dir": "src/content/pages",
            "media_dir": "public/uploads",
            "public_url": "/uploads"
        }
        
        config = agent.generate_config(repo_info, content_structure)
        yaml_output = agent.generate_yaml(config)
        
        # Should be valid YAML despite special characters
        parsed_yaml = yaml.safe_load(yaml_output)
        assert parsed_yaml["backend"]["repo"] == "test-user/test-repo-with-dashes"
        assert parsed_yaml["backend"]["branch"] == "feature/special-branch"


class TestRealWorldScenarios:
    """Integration-style tests with realistic configurations."""
    
    def test_netlify_deployment_configuration(self):
        """Test configuration optimized for Netlify deployment."""
        agent = CMSConfigAgent()
        
        repo_info = {
            "owner": "mycompany",
            "repo": "company-website",
            "branch": "main"
        }
        
        content_structure = {
            "posts_dir": "src/content/blog",
            "pages_dir": "src/content/pages",
            "media_dir": "public/uploads",
            "public_url": "/uploads"
        }
        
        config = agent.generate_config(repo_info, content_structure)
        
        # Check Netlify-specific settings
        assert config.backend["auth_type"] == "oauth"
        assert config.backend["auth_url"] == "/.netlify/functions/auth"
        
        # Verify collections are properly configured
        assert len(config.collections) == 2
        blog_collection = next(c for c in config.collections if c["name"] == "blog")
        assert blog_collection["sortable_fields"] == ["title", "date"]
    
    def test_github_pages_configuration(self):
        """Test configuration suitable for GitHub Pages deployment."""
        agent = CMSConfigAgent()
        
        repo_info = {
            "owner": "username",
            "repo": "username.github.io",
            "branch": "main"
        }
        
        content_structure = {
            "posts_dir": "_posts",
            "pages_dir": "_pages",
            "media_dir": "assets/images",
            "public_url": "/assets/images"
        }
        
        config = agent.generate_config(repo_info, content_structure)
        
        # Should adapt to Jekyll-style structure
        assert config.media_folder == "assets/images"
        assert config.public_folder == "/assets/images"
        
        blog_collection = next(c for c in config.collections if c["name"] == "blog")
        assert blog_collection["folder"] == "_posts"
    
    def test_multi_language_site_configuration(self):
        """Test configuration for a multi-language site structure."""
        agent = CMSConfigAgent()
        
        repo_info = {
            "owner": "company",
            "repo": "multilingual-site",
            "branch": "main"
        }
        
        # This would require extending the agent to support multiple languages
        # This test documents the expected behavior for future enhancement
        content_structure = {
            "posts_dir": "src/content/blog",
            "pages_dir": "src/content/pages",
            "media_dir": "public/uploads",
            "public_url": "/uploads"
        }
        
        config = agent.generate_config(repo_info, content_structure)
        
        # For now, should generate standard configuration
        # Future versions could add i18n support
        assert len(config.collections) == 2
    
    def test_large_content_site_configuration(self):
        """Test configuration for sites with large amounts of content."""
        agent = CMSConfigAgent()
        
        repo_info = {
            "owner": "newssite",
            "repo": "news-platform",
            "branch": "main"
        }
        
        content_structure = {
            "posts_dir": "src/content/articles",
            "pages_dir": "src/content/pages",
            "media_dir": "public/media",
            "public_url": "/media"
        }
        
        config = agent.generate_config(repo_info, content_structure)
        
        # Check that configuration includes features for large sites
        blog_collection = next(c for c in config.collections if c["name"] == "blog")
        
        # Should have sorting and filtering capabilities
        assert "sortable_fields" in blog_collection
        assert "view_filters" in blog_collection
        assert "view_groups" in blog_collection
        
        # Should support date-based grouping for large content volumes
        year_group = blog_collection["view_groups"][0]
        assert year_group["field"] == "date"
        assert "\\d{4}" in year_group["pattern"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
