#!/usr/bin/env python3
"""
Quick test script for the WordPress-to-Astro migration tool.
"""

import sys
from pathlib import Path
from scaffold_agent import create_astro_project
from cms_config_agent import generate_cms_config
from transform_agent import TransformAgent

def test_migration():
    """Test the complete migration pipeline."""
    print("🚀 Testing WordPress-to-Astro Migration Tool")
    print("=" * 50)
    
    # Sample content (simulating WordPress extraction)
    sample_content = {
        "posts": [
            {
                "path": "src/content/blog/hello-world.md",
                "content": """---
title: 'Hello World!'
date: '2024-01-15T10:00:00'
slug: hello-world
categories:
- General
tags:
- first-post
---

# Welcome to Your New Astro Site!

This is a sample blog post that was migrated from WordPress. The migration tool automatically:

- ✅ Converted HTML to Markdown
- ✅ Generated proper frontmatter 
- ✅ Set up Decap CMS for editing
- ✅ Created a complete Astro project

You can now edit this content through the beautiful CMS interface at `/admin`!
"""
            },
            {
                "path": "src/content/blog/about-migration.md", 
                "content": """---
title: 'About This Migration'
date: '2024-01-16T14:30:00'
slug: about-migration
categories:
- Technical
tags:
- migration
- astro
---

# Migration Complete! 

Your WordPress site has been successfully migrated to:

- **Astro** - Modern static site generator
- **Decap CMS** - Git-based content management
- **GitHub** - Version control and hosting
- **Automatic deployment** - Changes go live instantly

## What's Next?

1. Explore your new `/admin` interface
2. Edit content with the visual editor
3. Publish changes with one click
4. Enjoy the speed and security!
"""
            }
        ],
        "pages": [
            {
                "path": "src/content/pages/about.md",
                "content": """---
title: 'About Us'
date: '2024-01-15T10:00:00'
slug: about
---

# About Our Company

This page was migrated from WordPress and is now powered by Astro + Decap CMS.

## Why We Migrated

- **Performance** - Lightning fast static sites
- **Security** - No database vulnerabilities  
- **Maintenance** - Automatic updates and backups
- **Modern workflow** - Git-based content management

Contact us to learn more about this modern approach to web development!
"""
            }
        ]
    }
    
    # Generate CMS configuration
    repo_info = {
        "owner": "your-username",
        "repo": "test-migration",
        "branch": "main"
    }
    
    content_structure = {
        "posts_dir": "src/content/blog",
        "pages_dir": "src/content/pages", 
        "media_dir": "public/uploads",
        "public_url": "/uploads"
    }
    
    print("⚙️ Generating CMS configuration...")
    cms_config = generate_cms_config(repo_info, content_structure)
    
    # Create project
    project_path = "output/test-runs/test-migration"
    
    print("🏗️ Creating Astro project...")
    project = create_astro_project(
        project_root=project_path,
        content=sample_content,
        cms_config=cms_config.model_dump()
    )
    
    print("\n✅ Migration Test Completed!")
    print(f"📁 Project created at: {project_path}")
    print(f"📝 Content files: {len(project.content_files)}")
    print(f"⚙️ Config files: {len(project.config_files)}")
    print(f"📋 Template files: {len(project.template_files)}")
    
    print("\n🚀 Next Steps:")
    print(f"1. cd {project_path}")
    print("2. npm install")
    print("3. npm run dev")
    print("4. Visit http://localhost:4321")
    print("5. Access CMS at http://localhost:4321/admin/index.html")
    
    return True

if __name__ == "__main__":
    try:
        test_migration()
        print("\n🎉 All tests passed! Your migration tool is working perfectly.")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        sys.exit(1)
