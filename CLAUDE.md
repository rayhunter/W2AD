# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup (venv/ already exists locally; virtual/ is an older, unused env)
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run the Streamlit UI
streamlit run app.py

# Tests live in tests/pytest/; pytest.ini sets testpaths and puts the repo root on sys.path
pytest
pytest tests/pytest/test_content_sanitization.py -v
pytest tests/pytest/test_content_sanitization.py::TestIntegrationScenarios::test_batch_content_processing
pytest tests/pytest --cov=. --cov-report=html
```

Some test files (e.g. `test_base_agent.py`, `test_updated_agents.py`, `test_gcs_setup.py`) are print-heavy scripts that hit real/fake external services; they are not pure unit tests. Manual acceptance test scripts are in `tests/manual/`.

Standalone debugging scripts at the root: `debug_deploy_agent.py`, `debug_wp_content.py`, `list_wp_media.py`, `test_cloudflare_credentials.py`, `demo_base_agent.py`.

Generated Astro projects (`output/generated-projects/<name>/`) are ordinary Astro apps: `npm install`, `npm run dev`, `npm run build`.

## Architecture

WordPress → Astro + Decap CMS migration tool. All modules are flat at the repo root (no package).

### Agents and BaseAgent
Every agent subclasses `BaseAgent` (`base_agent.py`), which provides logging, `_execute_with_metrics()` (timing + success/failure tracking), `validate_input/output`, `health_check`, and an abstract `process()` returning `BaseResult`. See `BASE_AGENT_SUMMARY.md` for details.

Each agent module also exposes a module-level convenience function, and **`app.py` calls these functions, not the classes directly**:

| Step | Module | Entry function |
|---|---|---|
| 1. Extract (WP REST API) | `extraction_agent.py` | `extract_from_wordpress()` → `WPContentBundle` |
| 2. Media → GCS (optional) | `media_agent.py` | `process_media_migration()` (rewrites content URLs) |
| 3. HTML → Markdown | `transform_agent.py` | `transform_bundle()` → `StaticContentBundle` |
| 4. Decap CMS config | `cms_config_agent.py` | `generate_cms_config()` |
| 5. Astro scaffold | `scaffold_agent.py` | `create_astro_project()` |
| 6. GitHub repo + push | `github_agent.py` | `create_github_repo()` |
| 7. Cloudflare Pages deploy | `deploy_agent.py` | `deploy_to_cloudflare()` |

The full pipeline is orchestrated inside `page_customer_ui()` in `app.py` (the "Start Migration" button). `app.py` also has one page per agent (`page_extraction`, `page_media`, …, routed via `display_page`) for running/debugging steps individually.

`content_schemas.py` holds a richer set of Pydantic content models (`WordPressPost`, `MediaAttachment`, `ContentCollection`, …) that is tested but not yet wired into the pipeline, which still uses the per-agent models (`WPPost`, `MarkdownPost`, etc.).

### Content sanitization (prevents Astro build failures)
WordPress content often yields markdown like `![Alt](15)` (numeric attachment IDs), which Astro treats as module imports and fails the build. Sanitization converts these to `_[Image: Alt]_`. The rules live in `content_sanitizer.py` (`ContentSanitizer`, covered by `test_content_sanitization.py`). The pipeline applies them twice, both via `ContentSanitizer.sanitize_image_references()`:
- `TransformAgent.sanitize_markdown_content()` — during HTML → Markdown
- `AstroScaffoldAgent.validate_and_sanitize_content()` — before writing content files

The pipeline deliberately does **not** call the full `sanitize_markdown_content()` / `sanitize_content()`. Its `sanitize_links` step turns any link whose URL contains `?`, `*`, `|`, `<`, `>` or `"` into plain text, which would break WordPress links like `/?p=123`.

### Configuration / credentials
Credentials (GitHub token, Cloudflare API token + account ID, GCS service-account JSON path + bucket) are entered in the Streamlit form and passed as arguments; `.env` is not auto-loaded by the app. `CLOUDFLARE_API_TOKEN` / `CLOUDFLARE_ACCOUNT_ID` env vars are only read by `deploy_agent.py`'s `__main__` block. `media_agent.py` sets `GOOGLE_APPLICATION_CREDENTIALS` from the provided path.

### Output
Generated projects are written to `output/generated-projects/<project-name>/` with content in `src/content/blog/` and `src/content/pages/`, layouts in `src/layouts/`, and the Decap admin at `public/admin/` (`index.html` + `config.yml`).
