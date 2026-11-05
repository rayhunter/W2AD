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

Requires Python 3.11 and Node.js (for building generated sites).

```bash
# Clone and setup
cd W2AD
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
2. **MediaAgent** - Media and featured image migration to Google Cloud Storage
3. **TransformAgent** - HTML to Markdown conversion with content sanitization
4. **CMSConfigAgent** - Decap CMS configuration generation
5. **AstroScaffoldAgent** - Complete project scaffolding with validation
6. **GitHubAgent** - GitHub repository creation and code push
7. **DeployAgent** - Automated Cloudflare Pages deployment

### 🛡️ Content Sanitization

The migration tool includes comprehensive content sanitization to prevent build errors:

- **Image Reference Validation** - Fixes numeric image references (e.g., `![Alt](15)` → `_[Image: Alt]_`)
- **Empty Reference Cleanup** - Handles empty image references gracefully
- **Character Escaping** - Sanitizes problematic characters that could cause module import errors
- **Automatic Testing** - Includes automated tests to prevent regressions

## 🔧 Configuration

### Credentials

All credentials are entered in the app's form (no `.env` needed). Media, GitHub, and Cloudflare are optional — leave them blank to skip that step.

- **Google Cloud Storage** (media) - a service account JSON key (enter its full path) and a bucket. The bucket needs **fine-grained** access control and the service account needs **Storage Object Admin** on it; otherwise image links fall back to URLs that expire.
- **GitHub** - a personal access token that can create repos: classic with the `repo` scope, or fine-grained with *All repositories* + *Administration* and *Contents* read/write.
- **Cloudflare Pages** - an API token (not the Global API Key) with *Cloudflare Pages: Edit* and *Account Settings: Read*, plus your Account ID. Connect Cloudflare to your GitHub account once (Workers & Pages → Create → Connect to Git) before deploying.

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

The folder is named after the repository name you enter; re-running with the same name overwrites it. A README and `.gitignore` are added when the GitHub step runs.

To run a generated site locally:

```bash
cd output/generated-projects/your-project-name/
npm install
npm run dev      # http://localhost:4321
npm run build    # static output in dist/
```

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
- **Tests** with pytest - run `pytest` (tests live in `tests/pytest/`; many are out of date with the current agents)

## 📄 License

MIT License - Feel free to use for commercial projects!
