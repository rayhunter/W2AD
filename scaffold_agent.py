import os
import json
import yaml
import re
from pathlib import Path
from typing import Dict, List, Any
from pydantic import BaseModel
import logging
import shutil
from base_agent import BaseAgent, BaseResult, AgentStatus
from content_sanitizer import ContentSanitizer

_sanitizer = ContentSanitizer()

class ProjectStructure(BaseModel):
    """Model representing the Astro project structure."""
    project_root: str
    content_files: List[str] = []
    config_files: List[str] = []
    template_files: List[str] = []

class AstroScaffoldAgent(BaseAgent):
    """Agent for scaffolding an Astro project with Decap CMS integration."""
    
    def __init__(self, project_root: str, content: Dict[str, List[Dict[str, str]]], cms_config: Dict[str, Any], **kwargs):
        """Initialize the scaffold agent.
        
        Args:
            project_root: Root directory for the new project
            content: Dictionary containing posts and pages content
            cms_config: Decap CMS configuration
            **kwargs: Additional configuration passed to BaseAgent
        """
        # Initialize base agent first
        agent_name = kwargs.pop('name', 'AstroScaffoldAgent')
        super().__init__(name=agent_name, project_root=project_root, content=content, cms_config=cms_config, **kwargs)
        
        # Validate content structure
        if not all(key in content for key in ["posts", "pages"]):
            raise ValueError("Content must contain 'posts' and 'pages' keys")
            
        self.project_root = Path(project_root)
        self.content = content
        self.cms_config = cms_config
        self.project_structure = ProjectStructure(project_root=str(project_root))
        
        # Validate configuration
        self.validate_configuration()
        
    def create_directory_structure(self):
        """Create the basic Astro project directory structure."""
        directories = [
            "src/content/blog",
            "src/content/pages",
            "src/components",
            "src/layouts",
            "src/pages",
            "src/pages/blog",
            "public/admin",
            "public/uploads"
        ]
        
        for dir_path in directories:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created directory: {full_path}")
            
    def validate_and_sanitize_content(self, content: str) -> str:
        """Validate and sanitize markdown content to prevent module import errors.
        
        This function fixes common issues that can cause Astro build errors.
        Delegates to the shared ContentSanitizer image rules.
        """
        content = _sanitizer.sanitize_image_references(content)

        self.logger.debug("Content sanitized to prevent module import errors")
        return content
    
    def create_content_files(self):
        """Create content files from the provided content."""
        # Create blog posts
        for post in self.content["posts"]:
            file_path = self.project_root / post["path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Validate and sanitize content before writing
            sanitized_content = self.validate_and_sanitize_content(post["content"])
            file_path.write_text(sanitized_content)
            self.project_structure.content_files.append(str(file_path))
            self.logger.info(f"Created post: {file_path}")
            
        # Create pages
        for page in self.content["pages"]:
            file_path = self.project_root / page["path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Validate and sanitize content before writing
            sanitized_content = self.validate_and_sanitize_content(page["content"])
            file_path.write_text(sanitized_content)
            self.project_structure.content_files.append(str(file_path))
            self.logger.info(f"Created page: {file_path}")
            
    def create_astro_config(self):
        """Create Astro configuration files."""
        # astro.config.mjs
        config_content = """import { defineConfig } from 'astro/config';

export default defineConfig({
    site: 'https://your-site.com',
    output: 'static'
});"""
        
        config_path = self.project_root / "astro.config.mjs"
        config_path.write_text(config_content)
        self.project_structure.config_files.append(str(config_path))
        self.logger.info(f"Created Astro config: {config_path}")
        
        # tsconfig.json
        tsconfig_content = """{
  "extends": "astro/tsconfigs/base",
  "compilerOptions": {
    "strict": true,
    "jsx": "preserve"
  }
}"""
        
        tsconfig_path = self.project_root / "tsconfig.json"
        tsconfig_path.write_text(tsconfig_content)
        self.project_structure.config_files.append(str(tsconfig_path))
        self.logger.info(f"Created TypeScript config: {tsconfig_path}")
        
    def create_cms_config(self):
        """Create Decap CMS configuration file."""
        config_path = self.project_root / "public/admin/config.yml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # If cms_config is a CMSConfig object, use its to_yaml method
        if hasattr(self.cms_config, 'to_yaml'):
            config_content = self.cms_config.to_yaml()
        else:
            # Fallback to yaml.dump for dict objects
            config_content = yaml.dump(self.cms_config, sort_keys=False)
        
        with open(config_path, 'w') as f:
            f.write(config_content)
            
        # Create admin/index.html with enhanced setup
        admin_html = """<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Content Manager</title>
    <style>
      body { margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
      .cms-loading { display: flex; justify-content: center; align-items: center; height: 100vh; }
      .cms-loading::after { content: 'Loading CMS...'; color: #666; }
    </style>
  </head>
  <body>
    <script src="https://unpkg.com/decap-cms@^3.0.0/dist/decap-cms.js"></script>
    <script>
      // Initialize Decap CMS
      if (typeof DecapCMS !== 'undefined') {
        DecapCMS.init();
      } else {
        console.error('Decap CMS failed to load');
      }
    </script>
  </body>
</html>"""
        
        admin_path = self.project_root / "public/admin/index.html"
        admin_path.write_text(admin_html)
        
        self.project_structure.config_files.extend([str(config_path), str(admin_path)])
        self.logger.info(f"Created CMS config: {config_path}")
        
        # If OAuth app was created, save credentials for reference
        if hasattr(self.cms_config, 'oauth_app') and self.cms_config.oauth_app:
            oauth_path = config_path.parent / "oauth_config.json"
            with open(oauth_path, 'w') as f:
                json.dump(self.cms_config.oauth_app.model_dump(), f, indent=2)
            self.project_structure.config_files.append(str(oauth_path))
            self.logger.info(f"Saved OAuth config: {oauth_path}")
        
    def create_package_json(self):
        """Create package.json with necessary dependencies."""
        package_content = {
            "name": self.project_root.name,
            "version": "0.1.0",
            "private": True,
            "scripts": {
                "dev": "astro dev",
                "build": "astro build",
                "preview": "astro preview"
            },
            "dependencies": {
                "astro": "^4.15.0"
            },
            "devDependencies": {
                "@astrojs/tailwind": "^5.1.0",
                "tailwindcss": "^3.4.0"
            }
        }
        
        package_path = self.project_root / "package.json"
        with open(package_path, 'w') as f:
            json.dump(package_content, f, indent=2)
            
        self.project_structure.config_files.append(str(package_path))
        self.logger.info(f"Created package.json: {package_path}")
        
    def create_templates(self):
        """Create Astro template files."""
        # Base layout
        base_layout = """---
interface Props {
  title: string;
  description?: string;
}

const { title, description = "A WordPress site migrated to Astro" } = Astro.props;
---

<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="description" content={description} />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="icon" type="image/x-icon" href="/favicon.ico" />
    <title>{title}</title>
    <style>
      html {
        font-family: system-ui, sans-serif;
        background: #ffffff;
        color: #333;
      }
      body {
        margin: 0;
        padding: 20px;
        line-height: 1.6;
      }
      h1 {
        color: #2c3e50;
        border-bottom: 2px solid #e1e8ed;
        padding-bottom: 10px;
      }
      .blog-post, .page {
        max-width: 800px;
        margin: 0 auto;
      }
      .metadata {
        color: #666;
        font-size: 0.9em;
        margin-bottom: 20px;
      }
      .featured-image {
        max-width: 100%;
        height: auto;
        margin: 20px 0;
      }
      a {
        color: #3498db;
        text-decoration: none;
      }
      a:hover {
        text-decoration: underline;
      }
    </style>
  </head>
  <body>
    <main>
      <slot />
    </main>
  </body>
</html>"""
        
        base_layout_path = self.project_root / "src/layouts/BaseLayout.astro"
        base_layout_path.write_text(base_layout)

        # Blog post layout
        blog_layout = """---
import BaseLayout from './BaseLayout.astro';

const { frontmatter } = Astro.props;
---
<BaseLayout title={frontmatter.title}>
  <article class="blog-post">
    <h1>{frontmatter.title}</h1>
    <div class="metadata">
      <time datetime={frontmatter.date}>
        {new Date(frontmatter.date).toLocaleDateString()}
      </time>
    </div>
    {frontmatter.image && (
      <img src={frontmatter.image} alt={frontmatter.title} class="featured-image" />
    )}
    <slot />
  </article>
</BaseLayout>"""
        
        blog_layout_path = self.project_root / "src/layouts/BlogPost.astro"
        blog_layout_path.write_text(blog_layout)
        
        # Page layout
        page_layout = """---
import BaseLayout from './BaseLayout.astro';

const { frontmatter } = Astro.props;
---
<BaseLayout title={frontmatter.title}>
  <article class="page">
    <h1>{frontmatter.title}</h1>
    {frontmatter.image && (
      <img src={frontmatter.image} alt={frontmatter.title} class="featured-image" />
    )}
    <slot />
  </article>
</BaseLayout>"""
        
        page_layout_path = self.project_root / "src/layouts/Page.astro"
        page_layout_path.write_text(page_layout)
        
        # Dynamic blog post route
        blog_route = """---
import { getCollection } from 'astro:content';
import BlogPost from '../../layouts/BlogPost.astro';

export async function getStaticPaths() {
  const posts = await getCollection('blog');
  return posts.map(post => ({
    params: { slug: post.slug },
    props: { post },
  }));
}

const { post } = Astro.props;
const { Content } = await post.render();
---
<BlogPost frontmatter={post.data}>
  <Content />
</BlogPost>"""
        
        blog_route_path = self.project_root / "src/pages/blog/[...slug].astro"
        blog_route_path.write_text(blog_route)

        # Dynamic page route
        page_route = """---
import { getCollection } from 'astro:content';
import Page from '../layouts/Page.astro';

export async function getStaticPaths() {
  const pages = await getCollection('pages');
  return pages
    .filter(page => page.slug !== 'admin') // Exclude admin to avoid conflicts with /admin/ CMS
    .map(page => ({
      params: { slug: page.slug },
      props: { page },
    }));
}

const { page } = Astro.props;
const { Content } = await page.render();
---
<Page frontmatter={page.data}>
  <Content />
</Page>"""
        
        page_route_path = self.project_root / "src/pages/[...slug].astro"
        page_route_path.write_text(page_route)
        
        # Homepage
        homepage = """---
import BaseLayout from '../layouts/BaseLayout.astro';
import { getCollection } from 'astro:content';

const posts = await getCollection('blog');
---

<BaseLayout title="WordPress Site Migrated to Astro">
  <h1>Welcome to Your Migrated Site</h1>
  
  <p>This WordPress site has been successfully migrated to Astro with Decap CMS integration.</p>
  
  <h2>Recent Blog Posts</h2>
  
  {posts.length > 0 ? (
    <ul>
      {posts.map(post => (
        <li>
          <a href={`/blog/${post.slug}/`}>
            {post.data.title}
          </a>
          <span> - {new Date(post.data.date).toLocaleDateString()}</span>
        </li>
      ))}
    </ul>
  ) : (
    <p>No blog posts found. Visit <a href="/admin/index.html">the CMS</a> to add content!</p>
  )}
  
  <hr>
  
  <h2>Content Management</h2>
  <p>
    <a href="/admin/index.html" style="background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
      Access CMS Admin →
    </a>
  </p>
  
  <p><em>Note: You'll need to authenticate with GitHub to access the content management system.</em></p>
</BaseLayout>"""
        
        homepage_path = self.project_root / "src/pages/index.astro"
        homepage_path.write_text(homepage)
        
        # Create .gitkeep for pages collection
        pages_gitkeep = self.project_root / "src/content/pages/.gitkeep"
        pages_gitkeep.parent.mkdir(parents=True, exist_ok=True)
        pages_gitkeep.write_text("# This directory exists for Astro content collections\n# Add .md files here for static pages")
        
        self.project_structure.template_files.extend([
            str(base_layout_path),
            str(blog_layout_path),
            str(page_layout_path),
            str(blog_route_path),
            str(page_route_path),
            str(homepage_path),
            str(pages_gitkeep)
        ])
        self.logger.info(f"Created template files in {self.project_root / 'src/layouts'} and {self.project_root / 'src/pages'}")
        
    def scaffold_project(self) -> ProjectStructure:
        """Execute the complete scaffolding process.
        
        Returns:
            ProjectStructure object containing all created files
        """
        self.logger.info(f"Starting project scaffolding in {self.project_root}")
        
        self.create_directory_structure()
        self.create_content_files()
        self.create_astro_config()
        self.create_cms_config()
        self.create_package_json()
        self.create_templates()
        
        self.logger.info("Project scaffolding completed")
        return self.project_structure
    
    def scaffold_project_with_metrics(self) -> ProjectStructure:
        """Execute scaffolding with metrics tracking."""
        return self._execute_with_metrics("scaffold_project", self.scaffold_project).data
    
    def process(self, *args, **kwargs) -> BaseResult:
        """Main processing method - scaffolds the complete Astro project."""
        try:
            project_structure = self.scaffold_project()
            
            total_files = (
                len(project_structure.content_files) +
                len(project_structure.config_files) + 
                len(project_structure.template_files)
            )
            
            return BaseResult(
                success=True,
                status=AgentStatus.SUCCESS,
                data=project_structure,
                message=f"Successfully scaffolded Astro project with {total_files} files in {self.project_root}"
            )
        except Exception as e:
            return BaseResult(
                success=False,
                status=AgentStatus.ERROR,
                error=str(e),
                message="Failed to scaffold Astro project"
            )
    
    def validate_configuration(self) -> bool:
        """Validate the agent's configuration."""
        if not self.project_root:
            raise ValueError("Project root directory is required")
        
        if not self.content:
            raise ValueError("Content dictionary is required")
        
        if not isinstance(self.content, dict):
            raise ValueError("Content must be a dictionary")
        
        if not all(key in self.content for key in ["posts", "pages"]):
            raise ValueError("Content must contain 'posts' and 'pages' keys")
        
        if not self.cms_config:
            raise ValueError("CMS configuration is required")
        
        # Check if project root parent directory exists and is writable
        parent_dir = self.project_root.parent
        if not parent_dir.exists():
            raise ValueError(f"Parent directory does not exist: {parent_dir}")
        
        if not os.access(parent_dir, os.W_OK):
            raise ValueError(f"Parent directory is not writable: {parent_dir}")
        
        return True

def create_astro_project(
    project_root: str,
    content: Dict[str, List[Dict[str, str]]],
    cms_config: Dict[str, Any]
) -> ProjectStructure:
    """Main function to create an Astro project.
    
    Args:
        project_root: Root directory for the new project
        content: Dictionary containing posts and pages content
        cms_config: Decap CMS configuration
        
    Returns:
        ProjectStructure object containing all created files
    """
    agent = AstroScaffoldAgent(project_root, content, cms_config)
    return agent.scaffold_project()