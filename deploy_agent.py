#!/usr/bin/env python3
"""
DeployAgent - Cloudflare Pages deployment functionality for WP2ASTRO migration tool.

This agent handles the deployment of generated Astro projects to Cloudflare Pages
using the Cloudflare API for automated deployment setup.
"""

import requests
import json
import time
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from pydantic import BaseModel
import subprocess
import tempfile
import shutil
from base_agent import BaseAgent, BaseResult, AgentStatus


class CloudflareDeployment(BaseModel):
    """Model for Cloudflare Pages deployment configuration."""
    project_name: str
    production_branch: str = "main"
    build_command: str = "npm run build"
    build_output_directory: str = "dist"
    root_directory: str = ""
    environment_variables: Dict[str, str] = {}
    compatibility_date: str = "2024-01-15"
    compatibility_flags: List[str] = []


class DeploymentResult(BaseModel):
    """Model for deployment operation results."""
    success: bool
    deployment_url: Optional[str] = None
    project_url: Optional[str] = None
    deployment_id: Optional[str] = None
    build_log: Optional[str] = None
    error: Optional[str] = None
    message: Optional[str] = None


class CloudflareAPI:
    """Cloudflare API client for Pages operations."""
    
    def __init__(self, api_token: str, account_id: str, logger=None):
        """Initialize Cloudflare API client.
        
        Args:
            api_token: Cloudflare API token with Pages permissions
            account_id: Cloudflare account ID
            logger: Logger instance to use (optional)
        """
        self.api_token = api_token
        self.account_id = account_id
        self.base_url = "https://api.cloudflare.com/client/v4"
        self.logger = logger or logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        })
    
    def test_credentials(self) -> bool:
        """Test API credentials and account access."""
        try:
            response = self.session.get(f"{self.base_url}/accounts/{self.account_id}")
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Failed to test Cloudflare credentials: {e}")
            return False
    
    def list_pages_projects(self) -> List[Dict[str, Any]]:
        """List all Cloudflare Pages projects."""
        try:
            response = self.session.get(
                f"{self.base_url}/accounts/{self.account_id}/pages/projects"
            )
            response.raise_for_status()
            return response.json().get("result", [])
        except Exception as e:
            self.logger.error(f"Failed to list Pages projects: {e}")
            return []
    
    def create_pages_project(self, deployment_config: CloudflareDeployment, 
                           github_repo: str) -> Optional[Dict[str, Any]]:
        """Create a new Cloudflare Pages project.
        
        Args:
            deployment_config: Deployment configuration
            github_repo: GitHub repository in format "owner/repo"
            
        Returns:
            API response with project details
        """
        project_data = {
            "name": deployment_config.project_name,
            "production_branch": deployment_config.production_branch,
            "source": {
                "type": "github",
                "config": {
                    "owner": github_repo.split("/")[0],
                    "repo_name": github_repo.split("/")[1],
                    "production_branch": deployment_config.production_branch,
                    "pr_comments_enabled": True,
                    "deployments_enabled": True,
                    "production_deployments_enabled": True,
                    "preview_deployment_setting": "all"
                }
            },
            "build_config": {
                "build_command": deployment_config.build_command,
                "destination_dir": deployment_config.build_output_directory,
                "root_dir": deployment_config.root_directory,
                "web_analytics_tag": None,
                "web_analytics_token": None
            },
            "deployment_configs": {
                "production": {
                    "environment_variables": deployment_config.environment_variables,
                    "kv_namespaces": {},
                    "durable_object_namespaces": {},
                    "d1_databases": {},
                    "r2_buckets": {},
                    "compatibility_date": deployment_config.compatibility_date,
                    "compatibility_flags": deployment_config.compatibility_flags
                },
                "preview": {
                    "environment_variables": deployment_config.environment_variables,
                    "kv_namespaces": {},
                    "durable_object_namespaces": {},
                    "d1_databases": {},
                    "r2_buckets": {},
                    "compatibility_date": deployment_config.compatibility_date,
                    "compatibility_flags": deployment_config.compatibility_flags
                }
            }
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/accounts/{self.account_id}/pages/projects",
                json=project_data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to create Pages project: {e}")
            return None
    
    def get_project_details(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Get details for a specific Pages project."""
        try:
            response = self.session.get(
                f"{self.base_url}/accounts/{self.account_id}/pages/projects/{project_name}"
            )
            if response.status_code == 200:
                return response.json().get("result")
            return None
        except Exception as e:
            self.logger.error(f"Failed to get project details: {e}")
            return None
    
    def trigger_deployment(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Trigger a new deployment for the project."""
        try:
            response = self.session.post(
                f"{self.base_url}/accounts/{self.account_id}/pages/projects/{project_name}/deployments"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to trigger deployment: {e}")
            return None
    
    def get_deployment_status(self, project_name: str, deployment_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific deployment."""
        try:
            response = self.session.get(
                f"{self.base_url}/accounts/{self.account_id}/pages/projects/{project_name}/deployments/{deployment_id}"
            )
            response.raise_for_status()
            return response.json().get("result", {})
        except Exception as e:
            self.logger.error(f"Failed to get deployment status: {e}")
            return None


class DeployAgent(BaseAgent):
    """Agent responsible for deploying Astro projects to Cloudflare Pages."""
    
    def __init__(self, api_token: str, account_id: str, **kwargs):
        """Initialize the deployment agent.
        
        Args:
            api_token: Cloudflare API token
            account_id: Cloudflare account ID
            **kwargs: Additional configuration passed to BaseAgent
        """
        # Initialize base agent first
        agent_name = kwargs.pop('name', 'DeployAgent')
        super().__init__(name=agent_name, api_token=api_token, account_id=account_id, **kwargs)
        
        # Set up Cloudflare-specific configuration
        self.api_token = api_token
        self.account_id = account_id
        self.cf_api = CloudflareAPI(api_token, account_id, logger=self.logger)
        
        # Validate configuration
        self.validate_configuration()
    
    def validate_credentials(self) -> bool:
        """Validate Cloudflare API credentials."""
        self.logger.info("Validating Cloudflare credentials...")
        return self.cf_api.test_credentials()
    
    def prepare_deployment_config(self, project_name: str, 
                                github_repo: str,
                                custom_domain: Optional[str] = None,
                                environment_variables: Optional[Dict[str, str]] = None) -> CloudflareDeployment:
        """Prepare deployment configuration for Astro project.
        
        Args:
            project_name: Name for the Cloudflare Pages project
            github_repo: GitHub repository in format "owner/repo"
            custom_domain: Optional custom domain
            environment_variables: Optional environment variables
            
        Returns:
            CloudflareDeployment configuration
        """
        # Sanitize project name for Cloudflare Pages
        sanitized_name = self.sanitize_project_name(project_name)
        
        # Default environment variables for Astro
        default_env_vars = {
            "NODE_VERSION": "18",
            "NPM_FLAGS": "--production=false",
            "SKIP_DEPENDENCY_INSTALL": "false"
        }
        
        if environment_variables:
            default_env_vars.update(environment_variables)
        
        config = CloudflareDeployment(
            project_name=sanitized_name,
            production_branch="main",
            build_command="npm install && npm run build",
            build_output_directory="dist",
            root_directory="",
            environment_variables=default_env_vars,
            compatibility_date="2024-01-15",
            compatibility_flags=[]
        )
        
        self.logger.info(f"Prepared deployment config for project: {sanitized_name}")
        return config
    
    def sanitize_project_name(self, name: str) -> str:
        """Sanitize project name for Cloudflare Pages compatibility.
        
        Cloudflare Pages project names must:
        - Be lowercase
        - Contain only alphanumeric characters and hyphens
        - Start and end with alphanumeric characters
        - Be between 1-58 characters
        """
        import re
        
        # Convert to lowercase and replace invalid characters
        sanitized = re.sub(r'[^a-z0-9\-]', '-', name.lower())
        
        # Remove leading/trailing hyphens
        sanitized = sanitized.strip('-')
        
        # Replace multiple consecutive hyphens with single hyphen
        sanitized = re.sub(r'-+', '-', sanitized)
        
        # Ensure it starts and ends with alphanumeric
        sanitized = re.sub(r'^-+|-+$', '', sanitized)
        
        # Truncate to 58 characters
        if len(sanitized) > 58:
            sanitized = sanitized[:58].rstrip('-')
        
        # Ensure minimum length
        if len(sanitized) < 1:
            sanitized = "wp2astro-project"
        
        return sanitized
    
    def deploy_to_cloudflare(self, deployment_config: CloudflareDeployment,
                           github_repo: str,
                           wait_for_deployment: bool = True) -> DeploymentResult:
        """Deploy Astro project to Cloudflare Pages.
        
        Args:
            deployment_config: Deployment configuration
            github_repo: GitHub repository in format "owner/repo"
            wait_for_deployment: Whether to wait for deployment completion
            
        Returns:
            DeploymentResult with deployment details
        """
        try:
            self.logger.info(f"Starting deployment to Cloudflare Pages: {deployment_config.project_name}")
            
            # Check if project already exists
            existing_project = self.cf_api.get_project_details(deployment_config.project_name)
            
            if existing_project:
                self.logger.info(f"Project {deployment_config.project_name} already exists, triggering new deployment")
                
                # Trigger new deployment
                deployment_response = self.cf_api.trigger_deployment(deployment_config.project_name)
                if deployment_response is None:
                    raise ValueError("Failed to trigger deployment: No response from API")
                deployment_id = deployment_response.get("result", {}).get("id")
                
            else:
                self.logger.info(f"Creating new Cloudflare Pages project: {deployment_config.project_name}")
                
                # Create new project
                project_response = self.cf_api.create_pages_project(deployment_config, github_repo)
                
                if project_response is None:
                    return DeploymentResult(
                        success=False,
                        error="Failed to create Pages project: No response from API"
                    )
                
                if not project_response.get("success"):
                    error_msg = project_response.get("errors", [{}])[0].get("message", "Unknown error")
                    return DeploymentResult(
                        success=False,
                        error=f"Failed to create Cloudflare Pages project: {error_msg}"
                    )
                
                project_data = project_response.get("result")
                if not project_data:
                    return DeploymentResult(
                        success=False,
                        error="Failed to create Pages project: No project data in API response"
                    )
                
                # Safely get deployment ID from project data
                latest_deployment = project_data.get("latest_deployment", {})
                deployment_id = latest_deployment.get("id") if latest_deployment else None
            
            # Get project details for URLs
            project_details = self.cf_api.get_project_details(deployment_config.project_name)
            
            if not project_details:
                return DeploymentResult(
                    success=False,
                    error="Failed to retrieve project details after creation"
                )
            
            # Extract URLs
            if project_details is None:
                return DeploymentResult(
                    success=False,
                    error="Failed to get project details for URL generation"
                )
            subdomain = project_details.get("subdomain", "")
            # Check if subdomain already includes .pages.dev to avoid duplication
            if subdomain:
                if subdomain.endswith(".pages.dev"):
                    deployment_url = f"https://{subdomain}"
                else:
                    deployment_url = f"https://{subdomain}.pages.dev"
            else:
                deployment_url = None
            project_url = f"https://dash.cloudflare.com/{self.account_id}/pages/view/{deployment_config.project_name}"
            
            result = DeploymentResult(
                success=True,
                deployment_url=deployment_url,
                project_url=project_url,
                deployment_id=deployment_id,
                message=f"Deployment initiated successfully for {deployment_config.project_name}"
            )
            
            # Wait for deployment completion if requested
            if wait_for_deployment and deployment_id:
                self.logger.info("Waiting for deployment to complete...")
                final_status = self.wait_for_deployment_completion(
                    deployment_config.project_name, 
                    deployment_id
                )
                
                if final_status.get("stage") == "success":
                    result.message = f"Deployment completed successfully! Site is live at {deployment_url}"
                elif final_status.get("stage") == "failure":
                    result.success = False
                    result.error = f"Deployment failed: {final_status.get('deployment_trigger', {}).get('metadata', {}).get('commit_message', 'Unknown error')}"
                
            self.logger.info(f"Deployment process completed for {deployment_config.project_name}")
            return result
            
        except Exception as e:
            self.logger.error(f"Deployment failed: {str(e)}")
            return DeploymentResult(
                success=False,
                error=f"Deployment failed: {str(e)}"
            )
    
    def wait_for_deployment_completion(self, project_name: str, deployment_id: str, 
                                     max_wait_time: int = 600) -> Dict[str, Any]:
        """Wait for deployment to complete.
        
        Args:
            project_name: Cloudflare Pages project name
            deployment_id: Deployment ID to monitor
            max_wait_time: Maximum time to wait in seconds (default 10 minutes)
            
        Returns:
            Final deployment status
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status = self.cf_api.get_deployment_status(project_name, deployment_id)
            
            if status is None:
                self.logger.warning("Failed to get deployment status")
                return {"stage": "unknown"}
            
            stage = status.get("stage")
            self.logger.info(f"Deployment status: {stage}")
            
            if stage in ["success", "failure"]:
                return status
            
            # Wait before checking again
            time.sleep(30)
        
        self.logger.warning(f"Deployment monitoring timed out after {max_wait_time} seconds")
        return {"stage": "timeout"}
    
    def setup_custom_domain(self, project_name: str, domain: str) -> bool:
        """Setup custom domain for the Cloudflare Pages project.
        
        Args:
            project_name: Cloudflare Pages project name
            domain: Custom domain to configure
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Setting up custom domain {domain} for project {project_name}")
            
            # Custom domain setup via API
            domain_data = {
                "name": domain
            }
            
            response = self.cf_api.session.post(
                f"{self.cf_api.base_url}/accounts/{self.account_id}/pages/projects/{project_name}/domains",
                json=domain_data
            )
            
            if response.status_code in [200, 201]:
                self.logger.info(f"Custom domain {domain} configured successfully")
                return True
            else:
                self.logger.error(f"Failed to setup custom domain: {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error setting up custom domain: {e}")
            return False
    
    def process(self, project_name: str, github_repo: str, custom_domain: str = None, 
               environment_variables: Dict[str, str] = None, wait_for_completion: bool = True, 
               *args, **kwargs) -> BaseResult:
        """Main processing method - deploys project to Cloudflare Pages.
        
        Args:
            project_name: Name for the deployment project
            github_repo: GitHub repository in format "owner/repo"
            custom_domain: Optional custom domain
            environment_variables: Optional environment variables
            wait_for_completion: Whether to wait for deployment completion
        """
        try:
            self.validate_input(project_name, str)
            self.validate_input(github_repo, str)
            
            # Prepare deployment configuration
            deployment_config = self.prepare_deployment_config(
                project_name=project_name,
                github_repo=github_repo,
                custom_domain=custom_domain,
                environment_variables=environment_variables
            )
            
            # Deploy to Cloudflare Pages
            result = self.deploy_to_cloudflare(
                deployment_config=deployment_config,
                github_repo=github_repo,
                wait_for_deployment=wait_for_completion
            )
            
            # Setup custom domain if provided and deployment was successful
            if result.success and custom_domain:
                domain_success = self.setup_custom_domain(
                    deployment_config.project_name, 
                    custom_domain
                )
                if domain_success:
                    result.deployment_url = f"https://{custom_domain}"
            
            return BaseResult(
                success=result.success,
                status=AgentStatus.SUCCESS if result.success else AgentStatus.ERROR,
                data=result,
                message=result.message,
                error=result.error
            )
            
        except Exception as e:
            return BaseResult(
                success=False,
                status=AgentStatus.ERROR,
                error=str(e),
                message="Failed to deploy to Cloudflare Pages"
            )
    
    def validate_configuration(self) -> bool:
        """Validate the agent's configuration."""
        if not self.api_token:
            raise ValueError("Cloudflare API token is required")
        
        if not self.account_id:
            raise ValueError("Cloudflare account ID is required")
        
        # Test API connectivity
        if not self.validate_credentials():
            raise ValueError("Invalid Cloudflare API credentials or account access denied")
        
        return True


def deploy_to_cloudflare(project_name: str, github_repo: str, 
                        cloudflare_api_token: str, cloudflare_account_id: str,
                        custom_domain: Optional[str] = None,
                        environment_variables: Optional[Dict[str, str]] = None,
                        wait_for_completion: bool = True) -> DeploymentResult:
    """Convenience function for deploying to Cloudflare Pages.
    
    Args:
        project_name: Name for the deployment project
        github_repo: GitHub repository in format "owner/repo"
        cloudflare_api_token: Cloudflare API token
        cloudflare_account_id: Cloudflare account ID
        custom_domain: Optional custom domain
        environment_variables: Optional environment variables
        wait_for_completion: Whether to wait for deployment completion
        
    Returns:
        DeploymentResult with deployment status and URLs
    """
    try:
        # Initialize deployment agent
        agent = DeployAgent(cloudflare_api_token, cloudflare_account_id)
        
        # Validate credentials
        if not agent.validate_credentials():
            return DeploymentResult(
                success=False,
                error="Invalid Cloudflare API credentials or account access"
            )
        
        # Prepare deployment configuration
        deployment_config = agent.prepare_deployment_config(
            project_name=project_name,
            github_repo=github_repo,
            custom_domain=custom_domain,
            environment_variables=environment_variables
        )
        
        # Deploy to Cloudflare Pages
        result = agent.deploy_to_cloudflare(
            deployment_config=deployment_config,
            github_repo=github_repo,
            wait_for_deployment=wait_for_completion
        )
        
        # Setup custom domain if provided and deployment was successful
        if result.success and custom_domain:
            domain_success = agent.setup_custom_domain(
                deployment_config.project_name, 
                custom_domain
            )
            if domain_success:
                result.deployment_url = f"https://{custom_domain}"
        
        return result
        
    except Exception as e:
        logging.error(f"Deployment failed: {e}")
        return DeploymentResult(
            success=False,
            error=f"Deployment failed: {str(e)}"
        )


if __name__ == "__main__":
    # Example usage
    import os
    
    # Test deployment (requires environment variables)
    api_token = os.getenv("CLOUDFLARE_API_TOKEN")
    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    
    if api_token and account_id:
        result = deploy_to_cloudflare(
            project_name="test-wp2astro-deployment",
            github_repo="username/test-repo",
            cloudflare_api_token=api_token,
            cloudflare_account_id=account_id,
            wait_for_completion=False
        )
        
        print(f"Deployment result: {result}")
    else:
        print("Please set CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID environment variables")
