# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Running the Application
```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run the main Streamlit application
streamlit run app.py
```

### Testing
```bash
# Run all tests
pytest

# Run specific test files
pytest test_content_sanitization.py -v
pytest test_migration.py -v

# Run test with coverage
pytest --cov=. --cov-report=html
```

### Generated Astro Projects
When working with generated Astro projects in `output/generated-projects/`:
```bash
cd output/generated-projects/[project-name]/
npm install
npm run dev      # Development server
npm run build    # Production build  
npm run preview  # Preview build
```

## Architecture

### Agent-Based Migration Pipeline
This tool uses a 7-agent architecture for WordPress-to-Astro migration:

1. **ExtractionAgent** (`extraction_agent.py`) - Extracts content from WordPress REST API
   - Models: `WPPost`, `WPPage`, `WPContentBundle`
   - Handles authentication and pagination

2. **TransformAgent** (`transform_agent.py`) - Converts HTML to Markdown with content sanitization  
   - Models: `MarkdownPost`, `MarkdownPage`, `StaticContentBundle`
   - Critical: Includes `sanitize_markdown_content()` to prevent module import errors

3. **MediaAgent** (`media_agent.py`) - Migrates media files to Google Cloud Storage
   - Downloads WordPress attachments and uploads to GCS
   - Updates content references to new URLs

4. **CMSConfigAgent** (`cms_config_agent.py`) - Generates Decap CMS configuration
   - Creates admin interface config for content editing

5. **AstroScaffoldAgent** (`scaffold_agent.py`) - Creates complete Astro project
   - Models: `ProjectStructure`
   - Includes content validation and sanitization
   - Generates layouts, pages, and configuration files

6. **GitHubAgent** (`github_agent.py`) - Creates repository and pushes code
   - Handles GitHub API integration and Git operations

7. **DeployAgent** (referenced but not implemented) - Deployment automation

### Content Sanitization System
**Critical for preventing build failures**: The tool includes comprehensive content sanitization to prevent Astro module import errors:

- **Image Reference Validation**: Converts numeric references like `![Alt](15)` to descriptive text `_[Image: Alt]_`
- **Empty Reference Cleanup**: Handles empty image references gracefully  
- **Character Escaping**: Prevents problematic characters that could cause import errors
- **Automated Testing**: `test_content_sanitization.py` ensures no regressions

### Data Flow
1. WordPress content extracted → Pydantic models
2. Media migration (optional) → Updates content URLs  
3. HTML→Markdown transformation → Content sanitization applied
4. Astro project scaffolding → Validation and final sanitization
5. GitHub integration → Repository creation and code push

### Key Dependencies
- **Streamlit**: Web UI framework (`app.py`)
- **Pydantic**: Data validation and serialization throughout agents
- **html2text**: HTML to Markdown conversion
- **google-cloud-storage**: Media migration to GCS
- **PyGithub + GitPython**: GitHub integration
- **BeautifulSoup4**: HTML processing
- **PyYAML**: Configuration file generation

### Project Output Structure
Generated Astro projects follow this structure:
```
output/generated-projects/[project-name]/
├── src/content/blog/     # Migrated WordPress posts
├── src/content/pages/    # Migrated WordPress pages  
├── src/layouts/          # Astro layout templates
├── public/admin/         # Decap CMS interface
└── package.json          # Astro + Tailwind dependencies
```

### Environment Configuration
Required environment variables:
- `GITHUB_TOKEN`: GitHub Personal Access Token
- `CLOUDFLARE_TOKEN`: For deployment (optional)
- `GOOGLE_CLOUD_CREDENTIALS`: Path to GCS service account JSON

### Testing Strategy
- **Unit tests**: Individual agent functionality
- **Integration tests**: Full migration pipeline (`test_migration.py`)  
- **Content sanitization tests**: Prevent build failures (`test_content_sanitization.py`)
- **Manual testing**: `tests/manual/` directory for user acceptance testing