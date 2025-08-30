import yaml
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
import logging
from base_agent import BaseAgent, BaseResult, AgentStatus

class CMSCollection(BaseModel):
    """Model for a CMS collection configuration."""
    name: str
    label: str
    folder: str
    create: bool = True
    slug: str = "{{slug}}"
    fields: List[Dict[str, Any]]

class CMSConfig(BaseModel):
    """Model for Decap CMS configuration."""
    backend: Dict[str, Any]
    media_folder: str = "public/uploads"
    public_folder: str = "/uploads"
    collections: List[Dict[str, Any]]
    
    def to_yaml(self) -> str:
        """Convert the configuration to YAML format."""
        config_dict = self.model_dump()
        return yaml.dump(config_dict, sort_keys=False)

class CMSConfigAgent(BaseAgent):
    """Agent for generating Decap CMS configuration."""
    
    def __init__(self, repo_info: Dict[str, str], content_structure: Dict[str, str], **kwargs):
        """Initialize the CMS config agent.
        
        Args:
            repo_info: Repository information (owner, repo, branch)
            content_structure: Content directory structure
            **kwargs: Additional configuration passed to BaseAgent
        """
        # Initialize base agent first
        agent_name = kwargs.pop('name', 'CMSConfigAgent')
        super().__init__(name=agent_name, repo_info=repo_info, content_structure=content_structure, **kwargs)
        
        # Set up CMS-specific configuration
        self.repo_info = repo_info
        self.content_structure = content_structure
        
        # Validate configuration
        self.validate_configuration()
    
    def generate_config(self) -> CMSConfig:
        """Generate the complete CMS configuration."""
        backend_config = {
            "name": "github",
            "repo": f"{self.repo_info['owner']}/{self.repo_info['repo']}",
            "branch": self.repo_info.get("branch", "main"),
            "publish_mode": "editorial_workflow"
        }
        
        collections = [
            {
                "name": "posts",
                "label": "Blog Posts",
                "folder": "src/content/blog",
                "create": True,
                "slug": "{{slug}}",
                "fields": [
                    {"label": "Title", "name": "title", "widget": "string"},
                    {"label": "Date", "name": "date", "widget": "datetime"},
                    {"label": "Featured Image", "name": "image", "widget": "image", "required": False},
                    {"label": "Categories", "name": "categories", "widget": "list"},
                    {"label": "Tags", "name": "tags", "widget": "list"},
                    {"label": "Body", "name": "body", "widget": "markdown"}
                ]
            },
            {
                "name": "pages",
                "label": "Pages",
                "folder": "src/content/pages",
                "create": True,
                "slug": "{{slug}}",
                "fields": [
                    {"label": "Title", "name": "title", "widget": "string"},
                    {"label": "Featured Image", "name": "image", "widget": "image", "required": False},
                    {"label": "Body", "name": "body", "widget": "markdown"}
                ]
            }
        ]
        
        return CMSConfig(
            backend=backend_config,
            media_folder=self.content_structure.get("media_dir", "public/uploads"),
            public_folder=self.content_structure.get("public_url", "/uploads"),
            collections=collections
        )
    
    def generate_config_with_metrics(self) -> CMSConfig:
        """Generate CMS configuration with metrics tracking."""
        return self._execute_with_metrics("generate_config", self.generate_config).data
    
    def process(self, *args, **kwargs) -> BaseResult:
        """Main processing method - generates CMS configuration."""
        try:
            config = self.generate_config()
            
            return BaseResult(
                success=True,
                status=AgentStatus.SUCCESS,
                data=config,
                message=f"Successfully generated CMS config for {self.repo_info.get('repo', 'repository')}"
            )
        except Exception as e:
            return BaseResult(
                success=False,
                status=AgentStatus.ERROR,
                error=str(e),
                message="Failed to generate CMS configuration"
            )
    
    def validate_configuration(self) -> bool:
        """Validate the agent's configuration."""
        if not self.repo_info:
            raise ValueError("Repository information is required")
        
        if not self.repo_info.get('owner'):
            raise ValueError("Repository owner is required")
        
        if not self.repo_info.get('repo'):
            raise ValueError("Repository name is required")
        
        if not self.content_structure:
            raise ValueError("Content structure configuration is required")
        
        return True

def generate_cms_config(repo_info: Dict[str, str], content_structure: Dict[str, str], github_token: str = None, site_url: str = None) -> CMSConfig:
    """Generate CMS configuration for a repository.
    
    Args:
        repo_info: Repository information
        content_structure: Content directory structure
        github_token: Optional GitHub token for OAuth setup
        site_url: Optional site URL for OAuth setup
        
    Returns:
        CMSConfig object
    """
    agent = CMSConfigAgent(repo_info, content_structure)
    return agent.generate_config()
