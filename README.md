# WordPress-to-Astro Migration Tool

A comprehensive tool for migrating WordPress sites to Astro with automatic Decap CMS integration for ongoing content management.

## 🎯 Features

- **Complete WordPress Migration** - Extract all posts, pages, and content
- **Automatic Astro Setup** - Generate optimized Astro project structure
- **Decap CMS Integration** - Ready-to-use content management system
- **GitHub Integration** - Automatic repository setup and deployment
- **Client-Ready** - Handoff-ready solution for ongoing maintenance

## 🚀 Quick Start

### 1. Setup

```bash
# Clone and setup
cd WP2ASTRO+Decap
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run Migration Tool

```bash
streamlit run app.py
```

### 3. Use the Interface

1. **Enter WordPress site details** (URL, credentials if needed)
2. **Configure target repository** (GitHub username, repo name)
3. **Click "Start Migration"** - the tool will:
   - Extract all WordPress content
   - Transform to Astro-compatible markdown
   - Generate Decap CMS configuration
   - Create complete Astro project
   - Set up admin interface at `/admin`

## 📁 Generated Project Structure

```
your-astro-site/
├── src/
│   ├── content/
│   │   ├── blog/          # Migrated WordPress posts
│   │   └── pages/         # Migrated WordPress pages
│   ├── layouts/
│   │   ├── BaseLayout.astro
│   │   ├── BlogPost.astro
│   │   └── Page.astro
│   └── pages/
│       ├── index.astro    # Homepage
│       ├── [...slug].astro
│       └── blog/[...slug].astro
├── public/
│   ├── admin/
│   │   ├── index.html     # Decap CMS interface
│   │   └── config.yml     # CMS configuration
│   └── uploads/           # Media directory
├── package.json
├── astro.config.mjs
└── tsconfig.json
```

## 🎨 Client Handoff

After migration, clients get:

1. **Live Astro Website** - Fast, modern static site
2. **Content Management** - Beautiful CMS at `/admin`
3. **GitHub Integration** - All content in version control
4. **Automatic Deployment** - Changes deploy automatically
5. **Zero Maintenance** - Self-managing infrastructure

## 📋 Agent Architecture

The migration uses a 7-agent pipeline with built-in content sanitization:

1. **ExtractionAgent** - WordPress REST API content extraction
2. **TransformAgent** - HTML to Markdown conversion with content sanitization
3. **MediaAgent** - Asset migration and optimization
4. **CMSConfigAgent** - Decap CMS configuration generation
5. **AstroScaffoldAgent** - Complete project scaffolding with validation
6. **RepoAgent** - GitHub repository creation
7. **DeployAgent** - Automated deployment setup

### 🛡️ Content Sanitization

The migration tool includes comprehensive content sanitization to prevent build errors:

- **Image Reference Validation** - Fixes numeric image references (e.g., `![Alt](15)` → `_[Image: Alt]_`)
- **Empty Reference Cleanup** - Handles empty image references gracefully
- **Character Escaping** - Sanitizes problematic characters that could cause module import errors
- **Automatic Testing** - Includes automated tests to prevent regressions

## 🔧 Configuration

### Environment Variables

Create a `.env` file:

```env
GITHUB_TOKEN=your_github_token
CLOUDFLARE_TOKEN=your_cloudflare_token
GOOGLE_CLOUD_CREDENTIALS=path/to/credentials.json
```

### WordPress Requirements

- WordPress site with REST API enabled (default since WP 4.7)
- Optional: Username/password for private content
- No plugins required

## 🎯 Use Cases

- **Agency Migrations** - Streamline client site migrations
- **Freelancer Tool** - Professional WordPress-to-modern-stack migrations
- **Client Empowerment** - Give clients modern, maintainable websites
- **Performance Upgrades** - Convert slow WordPress sites to fast static sites

## 📝 Output Location

Generated projects are saved to:
```
output/generated-projects/your-project-name/
```

Each project is:
- **Timestamped** for easy identification
- **Self-contained** and ready to deploy
- **Fully documented** with README files
- **Git-ready** with proper .gitignore

## 🔒 Security

- Credentials never stored permanently
- GitHub tokens used securely via API
- Generated sites are static (inherently secure)
- CMS access controlled via GitHub OAuth

## 🤝 Contributing

This tool demonstrates modern Python development practices:
- **Pydantic Models** for data validation
- **Agent Architecture** for separation of concerns
- **Streamlit UI** for user-friendly interface
- **Type Hints** throughout codebase
- **Comprehensive Testing** with pytest

## 📄 License

MIT License - Feel free to use for commercial projects!
