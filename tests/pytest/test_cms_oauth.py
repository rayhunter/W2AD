"""Tests for per-site Decap CMS login: OAuth Pages Functions and their Cloudflare secrets."""

from unittest.mock import MagicMock
from cms_config_agent import generate_cms_config
from deploy_agent import CloudflareAPI, CloudflareDeployment
from scaffold_agent import AstroScaffoldAgent, OAUTH_FUNCTIONS_DIR

REPO_INFO = {"owner": "testuser", "repo": "test-repo", "branch": "main"}
CONTENT_STRUCTURE = {
    "posts_dir": "src/content/blog",
    "pages_dir": "src/content/pages",
    "media_dir": "public/uploads",
    "public_url": "/uploads",
}


def scaffold_cms(tmp_path):
    config = generate_cms_config(REPO_INFO, CONTENT_STRUCTURE)
    agent = AstroScaffoldAgent(str(tmp_path), {"posts": [], "pages": []}, config)
    agent.create_cms_config()
    return agent


def test_scaffold_copies_oauth_functions(tmp_path):
    agent = scaffold_cms(tmp_path)

    for name in ("auth.js", "callback.js"):
        written = tmp_path / "functions" / name
        assert written.read_text() == (OAUTH_FUNCTIONS_DIR / name).read_text()
        assert str(written) in agent.project_structure.config_files


def test_admin_uses_site_origin_for_login(tmp_path):
    scaffold_cms(tmp_path)
    html = (tmp_path / "public/admin/index.html").read_text()

    # Manual init must be declared before Decap loads, or it initializes twice
    assert html.index("window.CMS_MANUAL_INIT = true") < html.index("decap-cms.js")
    assert "base_url: window.location.origin" in html


def test_pages_project_sends_typed_and_secret_env_vars():
    api = CloudflareAPI("token", "account")
    api.session = MagicMock()
    deployment = CloudflareDeployment(
        project_name="test-site",
        environment_variables={"NODE_VERSION": "18"},
        secret_environment_variables={"GITHUB_CLIENT_ID": "id123", "GITHUB_CLIENT_SECRET": "shh"},
    )

    api.create_pages_project(deployment, "testuser/test-repo")

    payload = api.session.post.call_args.kwargs["json"]
    for env in ("production", "preview"):
        env_vars = payload["deployment_configs"][env]["environment_variables"]
        assert env_vars["NODE_VERSION"] == {"type": "plain_text", "value": "18"}
        assert env_vars["GITHUB_CLIENT_ID"] == {"type": "secret_text", "value": "id123"}
        assert env_vars["GITHUB_CLIENT_SECRET"] == {"type": "secret_text", "value": "shh"}
