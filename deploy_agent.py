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
    
    def get_build_logs(self, project_name: str, deployment_id: str) -> Optional[Dict[str, Any]]:
        """Get build logs for a specific deployment."""
        try:
            response = self.session.get(
                f"{self.base_url}/accounts/{self.account_id}/pages/projects/{project_name}/deployments/{deployment_id}/history/logs"
            )
            response.raise_for_status()
            return response.json().get("result", {})
        except Exception as e:
            self.logger.error(f"Failed to get build logs: {e}")
            return None
    
    def get_deployment_files(self, project_name: str, deployment_id: str) -> List[str]:
        """List files in a specific deployment."""
        try:
            response = self.session.get(
                f"{self.base_url}/accounts/{self.account_id}/pages/projects/{project_name}/deployments/{deployment_id}/files"
            )
            response.raise_for_status()
            files_data = response.json().get("result", [])
            return [file_info.get("name", "") for file_info in files_data if file_info.get("name")]
        except Exception as e:
            self.logger.error(f"Failed to get deployment files: {e}")
            return []
    
    def get_deployment_analytics(self, project_name: str, deployment_id: str) -> Optional[Dict[str, Any]]:
        """Get analytics data for a specific deployment."""
        try:
            response = self.session.get(
                f"{self.base_url}/accounts/{self.account_id}/pages/projects/{project_name}/deployments/{deployment_id}/analytics"
            )
            if response.status_code == 200:
                return response.json().get("result", {})
            return None
        except Exception as e:
            self.logger.error(f"Failed to get deployment analytics: {e}")
            return None
    
    def get_project_build_config(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Get build configuration for a project to validate settings."""
        try:
            project_details = self.get_project_details(project_name)
            if project_details:
                return project_details.get("build_config", {})
            return None
        except Exception as e:
            self.logger.error(f"Failed to get project build config: {e}")
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
                
                # If no initial deployment was created, trigger one manually
                if not deployment_id:
                    self.logger.info("No initial deployment found, triggering first deployment from GitHub")
                    deployment_response = self.cf_api.trigger_deployment(deployment_config.project_name)
                    if deployment_response:
                        deployment_id = deployment_response.get("result", {}).get("id")
                        self.logger.info(f"Triggered initial deployment: {deployment_id}")
                    else:
                        self.logger.warning("Failed to trigger initial deployment")
            
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
        """Wait for deployment to complete with detailed progress reporting.
        
        Args:
            project_name: Cloudflare Pages project name
            deployment_id: Deployment ID to monitor
            max_wait_time: Maximum time to wait in seconds (default 10 minutes)
            
        Returns:
            Final deployment status with enhanced error information
        """
        start_time = time.time()
        last_stage = None
        
        self.logger.info(f"Monitoring deployment {deployment_id} for project {project_name}")
        
        while time.time() - start_time < max_wait_time:
            status = self.cf_api.get_deployment_status(project_name, deployment_id)
            
            if status is None:
                self.logger.warning("Failed to get deployment status - API may be temporarily unavailable")
                time.sleep(10)  # Shorter wait for API failures
                continue
            
            stage = status.get("stage")
            
            # Log stage changes for better visibility
            if stage != last_stage:
                self.logger.info(f"Deployment stage changed: {last_stage} -> {stage}")
                last_stage = stage
                
                # Get additional context for certain stages
                if stage in ["building", "deploying"]:
                    created_on = status.get("created_on")
                    if created_on:
                        self.logger.info(f"Stage '{stage}' started at {created_on}")
            
            if stage == "success":
                self.logger.info("Deployment completed successfully!")
                # Get deployed files for verification
                deployed_files = self.cf_api.get_deployment_files(project_name, deployment_id)
                if deployed_files:
                    self.logger.info(f"Successfully deployed {len(deployed_files)} files")
                    # Log key files for verification
                    key_files = [f for f in deployed_files if f in ['index.html', '404.html', '_astro/']]
                    if key_files:
                        self.logger.info(f"Key files deployed: {', '.join(key_files[:5])}")
                return status
                
            elif stage == "failure":
                self.logger.error("Deployment failed!")
                # Get build logs for failure analysis
                build_logs = self.cf_api.get_build_logs(project_name, deployment_id)
                if build_logs:
                    # Extract error information from build logs
                    log_data = build_logs.get('data', [])
                    if log_data:
                        error_lines = [log.get('line', '') for log in log_data if 'error' in log.get('line', '').lower()]
                        if error_lines:
                            self.logger.error(f"Build errors found: {'; '.join(error_lines[:3])}")
                            status['build_errors'] = error_lines
                return status
            
            # Provide periodic progress updates
            elapsed_time = time.time() - start_time
            if elapsed_time > 0 and int(elapsed_time) % 120 == 0:  # Every 2 minutes
                self.logger.info(f"Deployment still in progress ({stage}) - elapsed: {int(elapsed_time/60)}m")
            
            # Wait before checking again
            time.sleep(30)
        
        self.logger.warning(f"Deployment monitoring timed out after {max_wait_time} seconds in stage: {last_stage}")
        return {"stage": "timeout", "last_known_stage": last_stage}
    
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
    
    def validate_build_config(self, local_project_path: Optional[str] = None, 
                             expected_output_dir: str = "dist") -> Dict[str, Any]:
        """Validate build configuration against local Astro project settings.
        
        Args:
            local_project_path: Path to the local Astro project (optional)
            expected_output_dir: Expected output directory name
            
        Returns:
            Dictionary with validation results and recommendations
        """
        validation_result = {
            "valid": True,
            "issues": [],
            "recommendations": []
        }
        
        if local_project_path:
            project_path = Path(local_project_path)
            
            # Check if astro.config.js/ts exists
            astro_config_files = [
                project_path / "astro.config.js",
                project_path / "astro.config.ts",
                project_path / "astro.config.mjs"
            ]
            
            config_file = None
            for config in astro_config_files:
                if config.exists():
                    config_file = config
                    break
            
            if config_file:
                try:
                    # Read and analyze Astro config
                    config_content = config_file.read_text()
                    
                    # Look for output configuration
                    if "outDir" in config_content:
                        self.logger.info(f"Found custom outDir configuration in {config_file.name}")
                        validation_result["recommendations"].append(
                            "Review astro.config file for custom outDir setting - ensure it matches Cloudflare Pages build output directory"
                        )
                    
                    # Check for static adapter (required for Cloudflare Pages)
                    if "@astrojs/static" not in config_content and "static" not in config_content:
                        validation_result["valid"] = False
                        validation_result["issues"].append(
                            "Astro project should use @astrojs/static adapter for Cloudflare Pages deployment"
                        )
                        validation_result["recommendations"].append(
                            "Add @astrojs/static adapter to astro.config: import { defineConfig } from 'astro/config'; import { staticAdapter } from '@astrojs/static'; export default defineConfig({ adapter: staticAdapter() });"
                        )
                    
                except Exception as e:
                    self.logger.warning(f"Could not analyze Astro config: {e}")
                    validation_result["recommendations"].append(
                        "Manually verify Astro configuration for static site generation"
                    )
            else:
                validation_result["issues"].append("No Astro config file found")
                validation_result["recommendations"].append(
                    "Create astro.config.js with static adapter for Cloudflare Pages deployment"
                )
            
            # Check if package.json exists and has build script
            package_json_path = project_path / "package.json"
            if package_json_path.exists():
                try:
                    import json
                    with open(package_json_path) as f:
                        package_data = json.load(f)
                    
                    scripts = package_data.get("scripts", {})
                    if "build" not in scripts:
                        validation_result["valid"] = False
                        validation_result["issues"].append("No 'build' script found in package.json")
                        validation_result["recommendations"].append(
                            "Add build script to package.json: \"build\": \"astro build\""
                        )
                    elif "astro build" not in scripts["build"]:
                        validation_result["recommendations"].append(
                            "Verify build script uses 'astro build' command"
                        )
                        
                except Exception as e:
                    self.logger.warning(f"Could not read package.json: {e}")
            else:
                validation_result["valid"] = False
                validation_result["issues"].append("No package.json found")
        
        # Check if expected output directory name follows best practices
        if expected_output_dir not in ["dist", "build", "public"]:
            validation_result["recommendations"].append(
                f"Output directory '{expected_output_dir}' is non-standard. Consider using 'dist' for Astro projects"
            )
        
        return validation_result
    
    def troubleshoot_deployment(self, project_name: str, deployment_id: Optional[str] = None) -> Dict[str, Any]:
        """Troubleshoot common deployment issues for Error 522 and other problems.
        
        Args:
            project_name: Cloudflare Pages project name
            deployment_id: Optional specific deployment ID to analyze
            
        Returns:
            Dictionary with troubleshooting information and recommendations
        """
        troubleshoot_result = {
            "project_status": None,
            "build_config": None,
            "recent_deployments": [],
            "issues_found": [],
            "recommendations": []
        }
        
        try:
            # Get project details
            project_details = self.cf_api.get_project_details(project_name)
            if project_details:
                troubleshoot_result["project_status"] = {
                    "name": project_details.get("name"),
                    "subdomain": project_details.get("subdomain"),
                    "created_on": project_details.get("created_on"),
                    "production_branch": project_details.get("production_branch")
                }
                
                # Get build configuration
                build_config = project_details.get("build_config", {})
                troubleshoot_result["build_config"] = {
                    "build_command": build_config.get("build_command"),
                    "destination_dir": build_config.get("destination_dir"),
                    "root_dir": build_config.get("root_dir")
                }
                
                # Analyze build configuration for common issues
                if not build_config.get("build_command"):
                    troubleshoot_result["issues_found"].append("No build command configured")
                    troubleshoot_result["recommendations"].append("Configure build command: 'npm install && npm run build'")
                
                if build_config.get("destination_dir") != "dist":
                    troubleshoot_result["recommendations"].append(
                        f"Build output directory is '{build_config.get('destination_dir')}'. Ensure your Astro project outputs to this directory."
                    )
                
                # Get latest deployments
                latest_deployment = project_details.get("latest_deployment", {})
                if latest_deployment:
                    deployment_info = {
                        "id": latest_deployment.get("id"),
                        "stage": latest_deployment.get("stage"),
                        "created_on": latest_deployment.get("created_on"),
                        "url": latest_deployment.get("url")
                    }
                    troubleshoot_result["recent_deployments"].append(deployment_info)
                    
                    # Analyze deployment status
                    if latest_deployment.get("stage") == "failure":
                        troubleshoot_result["issues_found"].append("Latest deployment failed")
                        troubleshoot_result["recommendations"].extend([
                            "Check build logs for specific error messages",
                            "Verify all dependencies are properly installed",
                            "Ensure build command produces output in the configured directory"
                        ])
                    elif latest_deployment.get("stage") == "success":
                        # Check if files were actually deployed
                        if deployment_id or latest_deployment.get("id"):
                            dep_id = deployment_id or latest_deployment.get("id")
                            deployed_files = self.cf_api.get_deployment_files(project_name, dep_id)
                            
                            if not deployed_files:
                                troubleshoot_result["issues_found"].append("No files found in successful deployment")
                                troubleshoot_result["recommendations"].append("Build may not be producing output files - check build process")
                            elif "index.html" not in deployed_files:
                                troubleshoot_result["issues_found"].append("No index.html found in deployment")
                                troubleshoot_result["recommendations"].append("Astro build should generate an index.html file")
            else:
                troubleshoot_result["issues_found"].append("Project not found or inaccessible")
                troubleshoot_result["recommendations"].append("Verify project name and API permissions")
                
        except Exception as e:
            self.logger.error(f"Error during troubleshooting: {e}")
            troubleshoot_result["issues_found"].append(f"Troubleshooting error: {str(e)}")
        
        return troubleshoot_result
    
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
