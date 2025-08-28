#!/usr/bin/env python3
"""
Pytest tests for AstroScaffoldAgent - Astro project scaffolding functionality.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import json
from scaffold_agent import AstroScaffoldAgent, ProjectStructure, create_astro_project


class TestAstroScaffoldAgent:
    """Test suite for AstroScaffoldAgent class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = AstroScaffoldAgent()
        
        self.sample_content = {
            "posts": [
                {
                    "path": "src/content/blog/test-post.md",
                    "content": """---
title: 'Test Post'
date: '2024-01-15T10:00:00'
slug: test-post
categories:
- Technology
tags:
- Python
---

# Test Post Content

This is a test blog post."""
                }
            ],
            "pages": [
                {
                    "path": "src/content/pages/about.md",
                    "content": """---
title: 'About'
date: '2024-01-15T10:00:00'
slug: about
---

# About Page

This is the about page."""
                }
            ]
        }
        
        self.sample_cms_config = {
            "backend": {
                "name": "github",
                "repo": "user/repo",
                "branch": "main"
            },
            "media_folder": "public/uploads",
            "public_folder": "/uploads",
            "collections": []
        }
    
    def test_initialization(self):
        """Test agent initialization."""
        agent = AstroScaffoldAgent()
        assert agent is not None
    
    def test_create_directory_structure(self):
        """Test creation of Astro project directory structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "test-project"
            
            self.agent.create_directory_structure(project_root)
            
            # Check that main directories are created
            assert (project_root / "src").exists()
            assert (project_root / "src" / "content").exists()
            assert (project_root / "src" / "content" / "blog").exists()
            assert (project_root / "src" / "content" / "pages").exists()
            assert (project_root / "src" / "layouts").exists()
            assert (project_root / "src" / "pages").exists()
            assert (project_root / "src" / "pages" / "blog").exists()
            assert (project_root / "src" / "components").exists()
            assert (project_root / "public").exists()
            assert (project_root / "public" / "admin").exists()
            assert (project_root / "public" / "uploads").exists()
    
    def test_create_package_json(self):
        """Test package.json creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "test-project"
            project_root.mkdir(parents=True)
            
            self.agent.create_package_json(project_root, "test-project")
            
            package_json_path = project_root / "package.json"
            assert package_json_path.exists()
            
            # Verify content
            with open(package_json_path) as f:
                package_data = json.load(f)
            
            assert package_data["name"] == "test-project"
            assert "astro" in package_data["dependencies"]
            assert "@astrojs/check" in package_data["dependencies"]
            assert "typescript" in package_data["dependencies"]
            assert "scripts" in package_data
            assert "dev" in package_data["scripts"]
            assert "build" in package_data["scripts"]
    
    def test_create_astro_config(self):
        """Test astro.config.mjs creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "test-project"
            project_root.mkdir(parents=True)
            
            self.agent.create_astro_config(project_root)
            
            config_path = project_root / "astro.config.mjs"
            assert config_path.exists()
            
            # Verify content contains expected imports and configuration
            with open(config_path) as f:
                content = f.read()
            
            assert "import { defineConfig }" in content
            assert "integrations:" in content
            assert "content collections" in content.lower()
    
    def test_create_tsconfig(self):
        """Test tsconfig.json creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "test-project"
            project_root.mkdir(parents=True)
            
            self.agent.create_tsconfig(project_root)
            
            tsconfig_path = project_root / "tsconfig.json"
            assert tsconfig_path.exists()
            
            # Verify valid JSON
            with open(tsconfig_path) as f:
                tsconfig_data = json.load(f)
            
            assert "extends" in tsconfig_data
            assert "astro/tsconfigs/strict" in tsconfig_data["extends"]
    
    def test_create_env_d_ts(self):
        """Test env.d.ts creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "test-project"
            src_dir = project_root / "src"
            src_dir.mkdir(parents=True)
            
            self.agent.create_env_d_ts(project_root)
            
            env_d_ts_path = src_dir / "env.d.ts"
            assert env_d_ts_path.exists()
            
            # Verify content
            with open(env_d_ts_path) as f:
                content = f.read()
            
            assert "astro/client" in content
            assert "reference types" in content
    
    def test_create_base_layout(self):
        """Test BaseLayout.astro creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "test-project"
            layouts_dir = project_root / "src" / "layouts"
            layouts_dir.mkdir(parents=True)
            
            self.agent.create_base_layout(project_root)
            
            layout_path = layouts_dir / "BaseLayout.astro"
            assert layout_path.exists()
            
            # Verify Astro component structure
            with open(layout_path) as f:
                content = f.read()
            
            assert "---" in content  # Frontmatter
            assert "<html" in content
            assert "<head>" in content
            assert "<body>" in content
            assert "<slot />" in content  # Astro slot for content
    
    def test_create_blog_post_layout(self):
        """Test BlogPost.astro layout creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "test-project"
            layouts_dir = project_root / "src" / "layouts"
            layouts_dir.mkdir(parents=True)
            
            self.agent.create_blog_post_layout(project_root)
            
            layout_path = layouts_dir / "BlogPost.astro"
            assert layout_path.exists()
            
            # Verify blog-specific layout
            with open(layout_path) as f:
                content = f.read()
            
            assert "Astro.props" in content
            assert "title" in content
            assert "date" in content
            assert "<article>" in content or "<main>" in content
    
    def test_create_page_layout(self):
        """Test Page.astro layout creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "test-project"
            layouts_dir = project_root / "src" / "layouts"
            layouts_dir.mkdir(parents=True)
            
            self.agent.create_page_layout(project_root)
            
            layout_path = layouts_dir / "Page.astro"
            assert layout_path.exists()
            
            # Verify page layout structure
            with open(layout_path) as f:
                content = f.read()
            
            assert "Astro.props" in content
            assert "title" in content
    
    def test_create_index_page(self):
        """Test index.astro page creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "test-project"
            pages_dir = project_root / "src" / "pages"
            pages_dir.mkdir(parents=True)
            
            self.agent.create_index_page(project_root)
            
            index_path = pages_dir / "index.astro"
            assert index_path.exists()
            
            # Verify homepage content
            with open(index_path) as f:
                content = f.read()
            
            assert "---" in content  # Frontmatter
            assert "getCollection" in content  # Content collection usage
            assert "blog" in content.lower()
    
    def test_create_blog_pages(self):
        """Test blog page creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "test-project"
            blog_dir = project_root / "src" / "pages" / "blog"
            blog_dir.mkdir(parents=True)
            
            self.agent.create_blog_pages(project_root)
            
            # Check blog listing page
            blog_index_path = blog_dir / "[...slug].astro"
            assert blog_index_path.exists()
            
            # Verify dynamic routing
            with open(blog_index_path) as f:
                content = f.read()
            
            assert "getStaticPaths" in content
            assert "getCollection" in content
            assert "slug" in content
    
    def test_create_dynamic_pages(self):
        """Test dynamic page routing creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "test-project"
            pages_dir = project_root / "src" / "pages"
            pages_dir.mkdir(parents=True)
            
            self.agent.create_dynamic_pages(project_root)
            
            dynamic_page_path = pages_dir / "[...slug].astro"
            assert dynamic_page_path.exists()
            
            # Verify dynamic routing for pages
            with open(dynamic_page_path) as f:
                content = f.read()
            
            assert "getStaticPaths" in content
            assert "pages" in content.lower()
    
    def test_create_cms_admin_interface(self):
        """Test Decap CMS admin interface creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "test-project"
            admin_dir = project_root / "public" / "admin"
            admin_dir.mkdir(parents=True)
            
            self.agent.create_cms_admin_interface(project_root, self.sample_cms_config)
            
            # Check admin files
            index_path = admin_dir / "index.html"
            config_path = admin_dir / "config.yml"
            
            assert index_path.exists()
            assert config_path.exists()
            
            # Verify admin interface
            with open(index_path) as f:
                html_content = f.read()
            
            assert "decap-cms" in html_content.lower()
            assert "<script>" in html_content
            
            # Verify config file
            with open(config_path) as f:
                config_content = f.read()
            
            assert "backend:" in config_content
            assert "github" in config_content
    
    def test_write_content_files(self):
        """Test writing content files from content bundle."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "test-project"
            content_dir = project_root / "src" / "content"
            content_dir.mkdir(parents=True)
            
            self.agent.write_content_files(project_root, self.sample_content)
            
            # Check blog post
            blog_post_path = project_root / "src" / "content" / "blog" / "test-post.md"
            assert blog_post_path.exists()
            
            with open(blog_post_path) as f:
                content = f.read()
            
            assert "title: 'Test Post'" in content
            assert "# Test Post Content" in content
            
            # Check page
            page_path = project_root / "src" / "content" / "pages" / "about.md"
            assert page_path.exists()
            
            with open(page_path) as f:
                content = f.read()
            
            assert "title: 'About'" in content
            assert "# About Page" in content
    
    @patch('scaffold_agent.sanitize_content')
    def test_content_sanitization_during_write(self, mock_sanitize):
        """Test that content sanitization is applied when writing files."""
        mock_sanitize.side_effect = lambda x: x + " [SANITIZED]"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "test-project"
            content_dir = project_root / "src" / "content"
            content_dir.mkdir(parents=True)
            
            self.agent.write_content_files(project_root, self.sample_content)
            
            # Verify sanitization was called
            assert mock_sanitize.call_count > 0
            
            # Check that sanitized content was written
            blog_post_path = project_root / "src" / "content" / "blog" / "test-post.md"
            with open(blog_post_path) as f:
                content = f.read()
            
            assert "[SANITIZED]" in content
    
    def test_create_astro_project_complete(self):
        """Test complete Astro project creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "test-project"
            
            project = self.agent.create_astro_project(
                project_root=str(project_root),
                content=self.sample_content,
                cms_config=self.sample_cms_config
            )
            
            assert isinstance(project, ProjectStructure)
            
            # Verify project structure
            assert project_root.exists()
            assert (project_root / "package.json").exists()
            assert (project_root / "astro.config.mjs").exists()
            assert (project_root / "tsconfig.json").exists()
            assert (project_root / "src").exists()
            assert (project_root / "public").exists()
            
            # Verify content files
            assert (project_root / "src" / "content" / "blog" / "test-post.md").exists()
            assert (project_root / "src" / "content" / "pages" / "about.md").exists()
            
            # Verify admin interface
            assert (project_root / "public" / "admin" / "index.html").exists()
            assert (project_root / "public" / "admin" / "config.yml").exists()
            
            # Check project structure model
            assert len(project.content_files) >= 2  # posts + pages
            assert len(project.config_files) >= 3  # package.json, astro.config.mjs, tsconfig.json
            assert len(project.template_files) >= 3  # layouts
    
    def test_project_name_sanitization(self):
        """Test project name sanitization for package.json."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "Test Project With Spaces"
            project_root.mkdir(parents=True)
            
            self.agent.create_package_json(project_root, "Test Project With Spaces & Special!@# Characters")
            
            package_json_path = project_root / "package.json"
            with open(package_json_path) as f:
                package_data = json.load(f)
            
            # Name should be sanitized for npm compatibility
            project_name = package_data["name"]
            assert " " not in project_name
            assert "&" not in project_name
            assert "!" not in project_name
            assert "@" not in project_name
            assert "#" not in project_name
    
    def test_error_handling_invalid_content(self):
        """Test error handling for invalid content structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "test-project"
            
            invalid_content = {
                "posts": [
                    {
                        "path": "invalid/path/without/content.md"
                        # Missing 'content' field
                    }
                ]
            }
            
            # Should handle missing content gracefully
            try:
                self.agent.write_content_files(project_root, invalid_content)
            except KeyError:
                # Expected behavior for missing required fields
                pass


class TestProjectStructureModel:
    """Test ProjectStructure model validation."""
    
    def test_project_structure_creation(self):
        """Test ProjectStructure model creation and validation."""
        project_data = {
            "root_path": "/tmp/test-project",
            "content_files": [
                "src/content/blog/post1.md",
                "src/content/pages/about.md"
            ],
            "config_files": [
                "package.json",
                "astro.config.mjs",
                "tsconfig.json"
            ],
            "template_files": [
                "src/layouts/BaseLayout.astro",
                "src/layouts/BlogPost.astro",
                "src/pages/index.astro"
            ]
        }
        
        project = ProjectStructure(**project_data)
        
        assert project.root_path == "/tmp/test-project"
        assert len(project.content_files) == 2
        assert len(project.config_files) == 3
        assert len(project.template_files) == 3
    
    def test_project_structure_with_empty_lists(self):
        """Test ProjectStructure with empty file lists."""
        project_data = {
            "root_path": "/tmp/empty-project",
            "content_files": [],
            "config_files": [],
            "template_files": []
        }
        
        project = ProjectStructure(**project_data)
        
        assert len(project.content_files) == 0
        assert len(project.config_files) == 0
        assert len(project.template_files) == 0


class TestConvenienceFunction:
    """Test the convenience function for project creation."""
    
    @patch.object(AstroScaffoldAgent, 'create_astro_project')
    def test_create_astro_project_convenience_function(self, mock_create):
        """Test the convenience create_astro_project function."""
        mock_project = ProjectStructure(
            root_path="/tmp/test",
            content_files=[],
            config_files=[],
            template_files=[]
        )
        mock_create.return_value = mock_project
        
        result = create_astro_project(
            project_root="/tmp/test",
            content={},
            cms_config={}
        )
        
        assert isinstance(result, ProjectStructure)
        mock_create.assert_called_once_with(
            project_root="/tmp/test",
            content={},
            cms_config={}
        )


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_permission_denied_directory_creation(self):
        """Test handling of permission denied errors."""
        # Test with a read-only directory
        with tempfile.TemporaryDirectory() as temp_dir:
            readonly_dir = Path(temp_dir) / "readonly"
            readonly_dir.mkdir()
            readonly_dir.chmod(0o444)  # Read-only
            
            project_root = readonly_dir / "test-project"
            
            agent = AstroScaffoldAgent()
            
            with pytest.raises(PermissionError):
                agent.create_directory_structure(project_root)
    
    def test_disk_space_exhaustion(self):
        """Test handling when disk space is exhausted."""
        # This test documents expected behavior
        # In real scenarios, OSError would be raised for no space left
        pass
    
    def test_invalid_project_root_path(self):
        """Test handling of invalid project root paths."""
        agent = AstroScaffoldAgent()
        
        # Test with invalid characters in path
        invalid_paths = [
            "",  # Empty path
            "/dev/null/cannot/create/here",  # Invalid path
        ]
        
        for invalid_path in invalid_paths:
            if invalid_path:  # Skip empty path for mkdir
                with pytest.raises((OSError, ValueError)):
                    agent.create_directory_structure(Path(invalid_path))


class TestRealWorldScenarios:
    """Integration-style tests with realistic project scenarios."""
    
    def test_large_blog_migration(self):
        """Test scaffolding for a large blog with many posts."""
        agent = AstroScaffoldAgent()
        
        # Simulate large blog content
        large_content = {
            "posts": [
                {
                    "path": f"src/content/blog/post-{i}.md",
                    "content": f"---\ntitle: 'Post {i}'\n---\n\nContent {i}"
                }
                for i in range(100)  # 100 blog posts
            ],
            "pages": [
                {
                    "path": "src/content/pages/about.md",
                    "content": "---\ntitle: 'About'\n---\n\nAbout page"
                }
            ]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "large-blog"
            
            project = agent.create_astro_project(
                project_root=str(project_root),
                content=large_content,
                cms_config=self.sample_cms_config
            )
            
            # Should handle large number of files
            assert len(project.content_files) >= 100
            
            # Verify all posts were created
            blog_dir = project_root / "src" / "content" / "blog"
            post_files = list(blog_dir.glob("post-*.md"))
            assert len(post_files) == 100
    
    def test_multilingual_site_structure(self):
        """Test scaffolding for potential multilingual site structure."""
        agent = AstroScaffoldAgent()
        
        # This test documents expected behavior for future i18n support
        content = {
            "posts": [
                {
                    "path": "src/content/blog/en/welcome.md",
                    "content": "---\ntitle: 'Welcome'\nlang: 'en'\n---\n\nWelcome!"
                },
                {
                    "path": "src/content/blog/es/bienvenido.md",
                    "content": "---\ntitle: 'Bienvenido'\nlang: 'es'\n---\n\n¡Bienvenido!"
                }
            ],
            "pages": []
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "multilingual-site"
            
            # Should create nested language directories
            agent.write_content_files(project_root, content)
            
            assert (project_root / "src" / "content" / "blog" / "en" / "welcome.md").exists()
            assert (project_root / "src" / "content" / "blog" / "es" / "bienvenido.md").exists()
    
    def test_corporate_website_structure(self):
        """Test scaffolding for a corporate website with multiple page types."""
        agent = AstroScaffoldAgent()
        
        corporate_content = {
            "posts": [
                {
                    "path": "src/content/blog/company-news.md",
                    "content": "---\ntitle: 'Company News'\ncategory: 'news'\n---\n\nNews content"
                }
            ],
            "pages": [
                {
                    "path": "src/content/pages/about.md",
                    "content": "---\ntitle: 'About Us'\ntype: 'about'\n---\n\nAbout content"
                },
                {
                    "path": "src/content/pages/services.md",
                    "content": "---\ntitle: 'Services'\ntype: 'services'\n---\n\nServices content"
                },
                {
                    "path": "src/content/pages/contact.md",
                    "content": "---\ntitle: 'Contact'\ntype: 'contact'\n---\n\nContact content"
                }
            ]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "corporate-site"
            
            project = agent.create_astro_project(
                project_root=str(project_root),
                content=corporate_content,
                cms_config=self.sample_cms_config
            )
            
            # Should handle different page types
            assert (project_root / "src" / "content" / "pages" / "about.md").exists()
            assert (project_root / "src" / "content" / "pages" / "services.md").exists()
            assert (project_root / "src" / "content" / "pages" / "contact.md").exists()
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sample_cms_config = {
            "backend": {
                "name": "github",
                "repo": "user/repo",
                "branch": "main"
            },
            "media_folder": "public/uploads",
            "public_folder": "/uploads",
            "collections": []
        }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
