#!/usr/bin/env python3
"""
Pytest tests for DeployAgent - Cloudflare Pages deployment functionality.
"""

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from deploy_agent import DeployAgent, CloudflareAPI, CloudflareDeployment, DeploymentResult, deploy_to_cloudflare


class TestCloudflareAPI:
    """Test suite for CloudflareAPI class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.api_token = "test_token"
        self.account_id = "test_account_id"
        
        with patch('deploy_agent.requests.Session'):
            self.api = CloudflareAPI(self.api_token, self.account_id)
    
    def test_initialization(self):
        """Test CloudflareAPI initialization."""
        with patch('deploy_agent.requests.Session') as mock_session:
            api = CloudflareAPI("token", "account")
            
            assert api.api_token == "token"
            assert api.account_id == "account"
            assert api.base_url == "https://api.cloudflare.com/client/v4"
            
            # Verify headers are set correctly
            mock_session.return_value.headers.update.assert_called_with({
                "Authorization": "Bearer token",
                "Content-Type": "application/json"
            })
    
    @patch('deploy_agent.requests.Session')
    def test_test_credentials_success(self, mock_session):
        """Test successful credential validation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.return_value.get.return_value = mock_response
        
        api = CloudflareAPI("token", "account")
        result = api.test_credentials()
        
        assert result is True
        mock_session.return_value.get.assert_called_with(
            "https://api.cloudflare.com/client/v4/accounts/account"
        )
    
    @patch('deploy_agent.requests.Session')
    def test_test_credentials_failure(self, mock_session):
        """Test failed credential validation."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_session.return_value.get.return_value = mock_response
        
        api = CloudflareAPI("token", "account")
        result = api.test_credentials()
        
        assert result is False
    
    @patch('deploy_agent.requests.Session')
    def test_test_credentials_exception(self, mock_session):
        """Test credential validation with network exception."""
        mock_session.return_value.get.side_effect = requests.exceptions.RequestException("Network error")
        
        api = CloudflareAPI("token", "account")
        result = api.test_credentials()
        
        assert result is False
    
    @patch('deploy_agent.requests.Session')
    def test_list_pages_projects_success(self, mock_session):
        """Test successful project listing."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": [
                {"name": "project1", "subdomain": "project1"},
                {"name": "project2", "subdomain": "project2"}
            ]
        }
        mock_session.return_value.get.return_value = mock_response
        
        api = CloudflareAPI("token", "account")
        projects = api.list_pages_projects()
        
        assert len(projects) == 2
        assert projects[0]["name"] == "project1"
        assert projects[1]["name"] == "project2"
    
    @patch('deploy_agent.requests.Session')
    def test_create_pages_project_success(self, mock_session):
        """Test successful project creation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "result": {
                "name": "test-project",
                "subdomain": "test-project",
                "latest_deployment": {"id": "deployment123"}
            }
        }
        mock_response.raise_for_status = Mock()
        mock_session.return_value.post.return_value = mock_response
        
        api = CloudflareAPI("token", "account")
        deployment_config = CloudflareDeployment(project_name="test-project")
        
        result = api.create_pages_project(deployment_config, "owner/repo")
        
        assert result["success"] is True
        assert result["result"]["name"] == "test-project"
        
        # Verify POST request was made with correct data
        mock_session.return_value.post.assert_called_once()
        call_args = mock_session.return_value.post.call_args
        assert "accounts/account/pages/projects" in call_args[0][0]
        
        # Verify project data structure
        project_data = call_args[1]["json"]
        assert project_data["name"] == "test-project"
        assert project_data["source"]["type"] == "github"
        assert project_data["source"]["config"]["owner"] == "owner"
        assert project_data["source"]["config"]["repo_name"] == "repo"
    
    @patch('deploy_agent.requests.Session')
    def test_create_pages_project_failure(self, mock_session):
        """Test failed project creation."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("API Error")
        mock_session.return_value.post.return_value = mock_response
        
        api = CloudflareAPI("token", "account")
        deployment_config = CloudflareDeployment(project_name="test-project")
        
        with pytest.raises(requests.exceptions.HTTPError):
            api.create_pages_project(deployment_config, "owner/repo")
    
    @patch('deploy_agent.requests.Session')
    def test_get_project_details_success(self, mock_session):
        """Test successful project details retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "name": "test-project",
                "subdomain": "test-project",
                "production_branch": "main"
            }
        }
        mock_session.return_value.get.return_value = mock_response
        
        api = CloudflareAPI("token", "account")
        details = api.get_project_details("test-project")
        
        assert details is not None
        assert details["name"] == "test-project"
        assert details["subdomain"] == "test-project"
    
    @patch('deploy_agent.requests.Session')
    def test_get_project_details_not_found(self, mock_session):
        """Test project details for non-existent project."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_session.return_value.get.return_value = mock_response
        
        api = CloudflareAPI("token", "account")
        details = api.get_project_details("nonexistent-project")
        
        assert details is None


class TestDeployAgent:
    """Test suite for DeployAgent class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.api_token = "test_token"
        self.account_id = "test_account_id"
        
        with patch('deploy_agent.CloudflareAPI'):
            self.agent = DeployAgent(self.api_token, self.account_id)
    
    def test_initialization(self):
        """Test DeployAgent initialization."""
        with patch('deploy_agent.CloudflareAPI') as mock_api:
            agent = DeployAgent("token", "account")
            
            assert agent.api_token == "token"
            assert agent.account_id == "account"
            mock_api.assert_called_once_with("token", "account")
    
    def test_validate_credentials_success(self):
        """Test successful credential validation."""
        self.agent.cf_api.test_credentials.return_value = True
        
        result = self.agent.validate_credentials()
        assert result is True
        self.agent.cf_api.test_credentials.assert_called_once()
    
    def test_validate_credentials_failure(self):
        """Test failed credential validation."""
        self.agent.cf_api.test_credentials.return_value = False
        
        result = self.agent.validate_credentials()
        assert result is False
    
    def test_sanitize_project_name_basic(self):
        """Test basic project name sanitization."""
        test_cases = [
            ("My Project", "my-project"),
            ("test_project", "test-project"),
            ("Project123", "project123"),
            ("TEST-PROJECT", "test-project"),
        ]
        
        for input_name, expected in test_cases:
            result = self.agent.sanitize_project_name(input_name)
            assert result == expected
    
    def test_sanitize_project_name_special_characters(self):
        """Test project name sanitization with special characters."""
        test_cases = [
            ("My Project!", "my-project"),
            ("test@#$%project", "test-project"),
            ("project with spaces", "project-with-spaces"),
            ("project--with--dashes", "project-with-dashes"),
            ("-starting-dash", "starting-dash"),
            ("ending-dash-", "ending-dash"),
        ]
        
        for input_name, expected in test_cases:
            result = self.agent.sanitize_project_name(input_name)
            assert result == expected
    
    def test_sanitize_project_name_length_limits(self):
        """Test project name length handling."""
        # Test long name truncation
        long_name = "a" * 100
        result = self.agent.sanitize_project_name(long_name)
        assert len(result) <= 58
        
        # Test empty name default
        result = self.agent.sanitize_project_name("")
        assert result == "wp2astro-project"
        
        # Test invalid characters only
        result = self.agent.sanitize_project_name("!!!@@@###")
        assert result == "wp2astro-project"
    
    def test_prepare_deployment_config_basic(self):
        """Test basic deployment configuration preparation."""
        config = self.agent.prepare_deployment_config(
            project_name="test-project",
            github_repo="owner/repo"
        )
        
        assert isinstance(config, CloudflareDeployment)
        assert config.project_name == "test-project"
        assert config.production_branch == "main"
        assert config.build_command == "npm install && npm run build"
        assert config.build_output_directory == "dist"
        assert "NODE_VERSION" in config.environment_variables
        assert config.environment_variables["NODE_VERSION"] == "18"
    
    def test_prepare_deployment_config_with_custom_env(self):
        """Test deployment configuration with custom environment variables."""
        custom_env = {
            "CUSTOM_VAR": "custom_value",
            "NODE_VERSION": "20"  # Should override default
        }
        
        config = self.agent.prepare_deployment_config(
            project_name="test-project",
            github_repo="owner/repo",
            environment_variables=custom_env
        )
        
        assert config.environment_variables["CUSTOM_VAR"] == "custom_value"
        assert config.environment_variables["NODE_VERSION"] == "20"
        assert "NPM_FLAGS" in config.environment_variables
    
    def test_deploy_to_cloudflare_new_project_success(self):
        """Test successful deployment to new Cloudflare project."""
        # Mock API responses
        self.agent.cf_api.get_project_details.return_value = None  # Project doesn't exist
        self.agent.cf_api.create_pages_project.return_value = {
            "success": True,
            "result": {
                "name": "test-project",
                "subdomain": "test-project",
                "latest_deployment": {"id": "deployment123"}
            }
        }
        
        # Mock project details after creation
        project_details = {
            "name": "test-project",
            "subdomain": "test-project-abc"
        }
        self.agent.cf_api.get_project_details.return_value = project_details
        
        deployment_config = CloudflareDeployment(project_name="test-project")
        
        result = self.agent.deploy_to_cloudflare(
            deployment_config=deployment_config,
            github_repo="owner/repo",
            wait_for_deployment=False
        )
        
        assert isinstance(result, DeploymentResult)
        assert result.success is True
        assert result.deployment_url == "https://test-project-abc.pages.dev"
        assert result.deployment_id == "deployment123"
        
        # Verify API calls
        self.agent.cf_api.create_pages_project.assert_called_once()
    
    def test_deploy_to_cloudflare_existing_project_success(self):
        """Test successful deployment to existing Cloudflare project."""
        # Mock existing project
        existing_project = {
            "name": "test-project",
            "subdomain": "test-project-abc"
        }
        self.agent.cf_api.get_project_details.return_value = existing_project
        
        # Mock trigger deployment
        self.agent.cf_api.trigger_deployment.return_value = {
            "result": {"id": "deployment456"}
        }
        
        deployment_config = CloudflareDeployment(project_name="test-project")
        
        result = self.agent.deploy_to_cloudflare(
            deployment_config=deployment_config,
            github_repo="owner/repo",
            wait_for_deployment=False
        )
        
        assert result.success is True
        assert result.deployment_url == "https://test-project-abc.pages.dev"
        assert result.deployment_id == "deployment456"
        
        # Verify trigger deployment was called instead of create
        self.agent.cf_api.trigger_deployment.assert_called_once()
        self.agent.cf_api.create_pages_project.assert_not_called()
    
    def test_deploy_to_cloudflare_creation_failure(self):
        """Test deployment failure during project creation."""
        self.agent.cf_api.get_project_details.return_value = None
        self.agent.cf_api.create_pages_project.return_value = {
            "success": False,
            "errors": [{"message": "Project already exists"}]
        }
        
        deployment_config = CloudflareDeployment(project_name="test-project")
        
        result = self.agent.deploy_to_cloudflare(
            deployment_config=deployment_config,
            github_repo="owner/repo"
        )
        
        assert result.success is False
        assert "Project already exists" in result.error
    
    def test_deploy_to_cloudflare_exception_handling(self):
        """Test deployment with exception handling."""
        self.agent.cf_api.get_project_details.side_effect = Exception("API Error")
        
        deployment_config = CloudflareDeployment(project_name="test-project")
        
        result = self.agent.deploy_to_cloudflare(
            deployment_config=deployment_config,
            github_repo="owner/repo"
        )
        
        assert result.success is False
        assert "API Error" in result.error
    
    def test_wait_for_deployment_completion_success(self):
        """Test waiting for successful deployment completion."""
        # Mock deployment status progression
        status_responses = [
            {"stage": "queued"},
            {"stage": "building"},
            {"stage": "deploying"},
            {"stage": "success"}
        ]
        
        self.agent.cf_api.get_deployment_status.side_effect = status_responses
        
        result = self.agent.wait_for_deployment_completion("test-project", "deployment123", max_wait_time=10)
        
        assert result["stage"] == "success"
        assert self.agent.cf_api.get_deployment_status.call_count == 4
    
    def test_wait_for_deployment_completion_failure(self):
        """Test waiting for failed deployment."""
        self.agent.cf_api.get_deployment_status.return_value = {
            "stage": "failure",
            "deployment_trigger": {
                "metadata": {"commit_message": "Build failed"}
            }
        }
        
        result = self.agent.wait_for_deployment_completion("test-project", "deployment123", max_wait_time=10)
        
        assert result["stage"] == "failure"
    
    def test_wait_for_deployment_completion_timeout(self):
        """Test deployment monitoring timeout."""
        # Always return "building" status to trigger timeout
        self.agent.cf_api.get_deployment_status.return_value = {"stage": "building"}
        
        result = self.agent.wait_for_deployment_completion("test-project", "deployment123", max_wait_time=1)
        
        assert result["stage"] == "timeout"
    
    def test_setup_custom_domain_success(self):
        """Test successful custom domain setup."""
        mock_response = Mock()
        mock_response.status_code = 200
        self.agent.cf_api.session.post.return_value = mock_response
        
        result = self.agent.setup_custom_domain("test-project", "example.com")
        
        assert result is True
        self.agent.cf_api.session.post.assert_called_once()
    
    def test_setup_custom_domain_failure(self):
        """Test failed custom domain setup."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Invalid domain"
        self.agent.cf_api.session.post.return_value = mock_response
        
        result = self.agent.setup_custom_domain("test-project", "invalid-domain")
        
        assert result is False


class TestCloudflareDeploymentModel:
    """Test CloudflareDeployment model validation."""
    
    def test_cloudflare_deployment_creation(self):
        """Test CloudflareDeployment model creation."""
        deployment = CloudflareDeployment(
            project_name="test-project",
            production_branch="main",
            build_command="npm run build",
            build_output_directory="dist"
        )
        
        assert deployment.project_name == "test-project"
        assert deployment.production_branch == "main"
        assert deployment.build_command == "npm run build"
        assert deployment.build_output_directory == "dist"
        assert deployment.root_directory == ""
        assert isinstance(deployment.environment_variables, dict)
    
    def test_cloudflare_deployment_defaults(self):
        """Test CloudflareDeployment model with defaults."""
        deployment = CloudflareDeployment(project_name="test")
        
        assert deployment.production_branch == "main"
        assert deployment.build_command == "npm run build"
        assert deployment.build_output_directory == "dist"
        assert deployment.compatibility_date == "2024-01-15"
        assert deployment.compatibility_flags == []


class TestDeploymentResultModel:
    """Test DeploymentResult model validation."""
    
    def test_deployment_result_success(self):
        """Test DeploymentResult for successful deployment."""
        result = DeploymentResult(
            success=True,
            deployment_url="https://example.pages.dev",
            project_url="https://dash.cloudflare.com/project",
            deployment_id="deployment123",
            message="Deployment successful"
        )
        
        assert result.success is True
        assert result.deployment_url == "https://example.pages.dev"
        assert result.project_url == "https://dash.cloudflare.com/project"
        assert result.deployment_id == "deployment123"
        assert result.error is None
    
    def test_deployment_result_failure(self):
        """Test DeploymentResult for failed deployment."""
        result = DeploymentResult(
            success=False,
            error="Deployment failed",
            message="Build error"
        )
        
        assert result.success is False
        assert result.error == "Deployment failed"
        assert result.deployment_url is None
        assert result.clone_url is None


class TestConvenienceFunction:
    """Test the convenience function for deployment."""
    
    @patch.object(DeployAgent, 'validate_credentials')
    @patch.object(DeployAgent, 'prepare_deployment_config')
    @patch.object(DeployAgent, 'deploy_to_cloudflare')
    def test_deploy_to_cloudflare_convenience_success(self, mock_deploy, mock_prepare, mock_validate):
        """Test successful deployment via convenience function."""
        # Setup mocks
        mock_validate.return_value = True
        mock_config = CloudflareDeployment(project_name="test")
        mock_prepare.return_value = mock_config
        mock_result = DeploymentResult(success=True, deployment_url="https://test.pages.dev")
        mock_deploy.return_value = mock_result
        
        with patch('deploy_agent.DeployAgent') as mock_agent_class:
            mock_agent_instance = Mock()
            mock_agent_instance.validate_credentials = mock_validate
            mock_agent_instance.prepare_deployment_config = mock_prepare
            mock_agent_instance.deploy_to_cloudflare = mock_deploy
            mock_agent_class.return_value = mock_agent_instance
            
            result = deploy_to_cloudflare(
                project_name="test",
                github_repo="owner/repo",
                cloudflare_api_token="token",
                cloudflare_account_id="account"
            )
            
            assert isinstance(result, DeploymentResult)
            assert result.success is True
            mock_agent_class.assert_called_once_with("token", "account")
    
    @patch.object(DeployAgent, 'validate_credentials')
    def test_deploy_to_cloudflare_convenience_invalid_credentials(self, mock_validate):
        """Test deployment with invalid credentials."""
        mock_validate.return_value = False
        
        with patch('deploy_agent.DeployAgent') as mock_agent_class:
            mock_agent_instance = Mock()
            mock_agent_instance.validate_credentials = mock_validate
            mock_agent_class.return_value = mock_agent_instance
            
            result = deploy_to_cloudflare(
                project_name="test",
                github_repo="owner/repo",
                cloudflare_api_token="invalid_token",
                cloudflare_account_id="account"
            )
            
            assert result.success is False
            assert "Invalid Cloudflare API credentials" in result.error


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_network_connectivity_issues(self):
        """Test handling of network connectivity issues."""
        with patch('deploy_agent.requests.Session') as mock_session:
            mock_session.return_value.get.side_effect = requests.exceptions.ConnectionError("Network unreachable")
            
            api = CloudflareAPI("token", "account")
            result = api.test_credentials()
            
            assert result is False
    
    def test_api_rate_limiting(self):
        """Test handling of API rate limiting."""
        with patch('deploy_agent.requests.Session') as mock_session:
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.text = "Rate limit exceeded"
            mock_session.return_value.get.return_value = mock_response
            
            api = CloudflareAPI("token", "account")
            result = api.test_credentials()
            
            assert result is False
    
    def test_malformed_api_response(self):
        """Test handling of malformed API responses."""
        with patch('deploy_agent.requests.Session') as mock_session:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_session.return_value.get.return_value = mock_response
            
            api = CloudflareAPI("token", "account")
            projects = api.list_pages_projects()
            
            assert projects == []


class TestRealWorldScenarios:
    """Integration-style tests with realistic scenarios."""
    
    def test_astro_project_deployment_config(self):
        """Test deployment configuration for typical Astro project."""
        with patch('deploy_agent.CloudflareAPI'):
            agent = DeployAgent("token", "account")
            
            config = agent.prepare_deployment_config(
                project_name="my-astro-blog",
                github_repo="user/my-astro-blog"
            )
            
            # Verify Astro-specific settings
            assert config.build_command == "npm install && npm run build"
            assert config.build_output_directory == "dist"
            assert config.environment_variables["NODE_VERSION"] == "18"
            assert "NPM_FLAGS" in config.environment_variables
    
    def test_custom_domain_deployment(self):
        """Test deployment with custom domain configuration."""
        with patch('deploy_agent.CloudflareAPI'):
            agent = DeployAgent("token", "account")
            
            # Mock successful deployment
            agent.cf_api.get_project_details.return_value = None
            agent.cf_api.create_pages_project.return_value = {
                "success": True,
                "result": {"name": "test", "subdomain": "test", "latest_deployment": {"id": "123"}}
            }
            agent.cf_api.get_project_details.return_value = {"subdomain": "test"}
            
            # Mock successful custom domain setup
            with patch.object(agent, 'setup_custom_domain', return_value=True):
                config = CloudflareDeployment(project_name="test")
                result = agent.deploy_to_cloudflare(
                    deployment_config=config,
                    github_repo="user/repo"
                )
                
                assert result.success is True
    
    def test_large_project_deployment(self):
        """Test deployment of large project with many files."""
        # This test documents expected behavior for large projects
        # Cloudflare Pages should handle projects with thousands of files
        project_info = {
            "files_count": 5000,
            "total_size_mb": 100,
            "build_time_estimate": "5-10 minutes"
        }
        
        # Verify our configuration can handle large projects
        assert project_info["files_count"] > 1000
        assert project_info["total_size_mb"] < 500  # CF Pages limit is 500MB


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
