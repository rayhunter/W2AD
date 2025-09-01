import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging
from github import Github, GithubException
import git
from base_agent import BaseAgent, BaseResult, AgentStatus

class GitHubRepoInfo(BaseModel):
    """Model for GitHub repository information."""
    owner: str
    repo_name: str
    description: str = "WordPress site migrated to Astro with Decap CMS"
    private: bool = False
    clone_url: str = ""
    ssh_url: str = ""
    html_url: str = ""

class GitHubPushResult(BaseModel):
    """Model for GitHub push operation result."""
    success: bool
    repo_info: GitHubRepoInfo
    commit_hash: Optional[str] = None
    error_message: Optional[str] = None
    files_pushed: int = 0

class GitHubCloneResult(BaseModel):
    """Model for GitHub clone operation result."""
    success: bool
    repo_info: GitHubRepoInfo
    local_path: str = ""
    error_message: Optional[str] = None

class GitHubAgent(BaseAgent):
    """Agent for creating GitHub repositories and pushing Astro projects."""
    
    def __init__(self, github_token: str, **kwargs):
        """Initialize the GitHub agent.
        
        Args:
            github_token: Personal access token for GitHub API
            **kwargs: Additional configuration passed to BaseAgent
        """
        # Initialize base agent first
        agent_name = kwargs.pop('name', 'GitHubAgent')
        super().__init__(name=agent_name, github_token=github_token, **kwargs)
        
        # Set up GitHub-specific configuration
        if not github_token:
            raise ValueError("GitHub token is required")
            
        self.github_token = github_token
        self.github_client = Github(github_token)
        
        # Verify token and get user info
        try:
            self.user = self.github_client.get_user()
            self.logger.info(f"Authenticated as GitHub user: {self.user.login}")
        except GithubException as e:
            self.logger.error(f"GitHub authentication failed: {e}")
            raise ValueError(f"Invalid GitHub token: {e}")
        
        # Validate configuration
        self.validate_configuration()
    
    def create_repository(self, repo_name: str, description: str = None, private: bool = False) -> GitHubRepoInfo:
        """Create a new GitHub repository.
        
        Args:
            repo_name: Name of the repository
            description: Repository description
            private: Whether the repository should be private
            
        Returns:
            GitHubRepoInfo object with repository details
        """
        try:
            # Check if repository already exists
            try:
                existing_repo = self.user.get_repo(repo_name)
                self.logger.warning(f"Repository {repo_name} already exists")
                return GitHubRepoInfo(
                    owner=self.user.login,
                    repo_name=repo_name,
                    description=existing_repo.description or description or "",
                    private=existing_repo.private,
                    clone_url=existing_repo.clone_url,
                    ssh_url=existing_repo.ssh_url,
                    html_url=existing_repo.html_url
                )
            except GithubException:
                pass  # Repository doesn't exist, continue with creation
            
            # Create the repository
            self.logger.info(f"Creating GitHub repository: {repo_name}")
            repo = self.user.create_repo(
                name=repo_name,
                description=description or "WordPress site migrated to Astro with Decap CMS",
                private=private,
                auto_init=False  # Don't auto-init, we'll push our own content
                # Removed gitignore_template=None and license_template=None 
                # as they cause AssertionError in some PyGithub versions
            )
            
            repo_info = GitHubRepoInfo(
                owner=self.user.login,
                repo_name=repo_name,
                description=repo.description,
                private=repo.private,
                clone_url=repo.clone_url,
                ssh_url=repo.ssh_url,
                html_url=repo.html_url
            )
            
            self.logger.info(f"Successfully created repository: {repo.html_url}")
            return repo_info
            
        except GithubException as e:
            self.logger.error(f"Failed to create repository: {e}")
            raise RuntimeError(f"GitHub repository creation failed: {e}")
    
    def create_and_clone_repository(self, repo_name: str, local_path: Path, description: str = None, private: bool = False) -> GitHubCloneResult:
        """Create a GitHub repository and clone it to a local directory.
        
        Args:
            repo_name: Name of the repository
            local_path: Local path where to clone the repository
            description: Repository description
            private: Whether the repository should be private
            
        Returns:
            GitHubCloneResult with operation details
        """
        try:
            # Create the repository first
            repo_info = self.create_repository(repo_name, description, private)
            
            # Ensure the parent directory exists and the target directory is clean
            local_path.parent.mkdir(parents=True, exist_ok=True)
            if local_path.exists():
                shutil.rmtree(local_path)
            
            # Clone the repository
            self.logger.info(f"Cloning repository to: {local_path}")
            clone_url = f"https://{self.github_token}@github.com/{repo_info.owner}/{repo_info.repo_name}.git"
            
            # Clone the repository
            repo = git.Repo.clone_from(clone_url, local_path)
            
            # Create an initial README if the repo is empty
            readme_path = local_path / "README.md"
            if not readme_path.exists():
                readme_content = f"""# {repo_name}

WordPress site migrated to Astro with Decap CMS integration.

## Getting Started

This repository was created as part of an automated WordPress-to-Astro migration.
The Astro project files will be added by the migration tool.

## Next Steps

1. The migration tool will populate this repository with:
   - Astro project structure
   - Migrated content from WordPress
   - Decap CMS configuration
   - Ready-to-deploy static site

2. After migration, you can:
   - Run `npm install` to install dependencies
   - Run `npm run dev` to start development server
   - Visit `/admin/` for content management
   - Deploy to your preferred hosting platform
"""
                readme_path.write_text(readme_content)
                
                # Commit the initial README
                repo.index.add([str(readme_path)])
                repo.index.commit("Initial commit: Add README")
                repo.remotes.origin.push()
                
                self.logger.info("Created and committed initial README")
            
            self.logger.info(f"Successfully cloned repository to: {local_path}")
            
            return GitHubCloneResult(
                success=True,
                repo_info=repo_info,
                local_path=str(local_path)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create and clone repository: {e}")
            return GitHubCloneResult(
                success=False,
                repo_info=GitHubRepoInfo(owner="", repo_name=repo_name),
                local_path=str(local_path),
                error_message=str(e)
            )
    
    def initialize_git_repo(self, project_path: Path) -> git.Repo:
        """Initialize a Git repository in the project directory.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            GitPython Repo object
        """
        try:
            # Initialize git repository
            self.logger.info(f"Initializing Git repository in {project_path}")
            repo = git.Repo.init(project_path)
            
            # Create .gitignore file
            gitignore_content = """# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Build outputs
dist/
.astro/

# Environment files
.env
.env.local
.env.production

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db

# Logs
logs
*.log

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Coverage directory used by tools like istanbul
coverage/

# Dependency directories
node_modules/
jspm_packages/

# Optional npm cache directory
.npm

# Optional eslint cache
.eslintcache

# Microbundle cache
.rpt2_cache/
.rts2_cache_cjs/
.rts2_cache_es/
.rts2_cache_umd/

# Optional REPL history
.node_repl_history

# Output of 'npm pack'
*.tgz

# Yarn Integrity file
.yarn-integrity

# dotenv environment variables file
.env

# parcel-bundler cache (https://parceljs.org/)
.cache
.parcel-cache

# next.js build output
.next

# nuxt.js build output
.nuxt

# vuepress build output
.vuepress/dist

# Serverless directories
.serverless

# FuseBox cache
.fusebox/

# DynamoDB Local files
.dynamodb/

# TernJS port file
.tern-port
"""
            
            gitignore_path = project_path / ".gitignore"
            gitignore_path.write_text(gitignore_content)
            
            # Create README.md if it doesn't exist
            readme_path = project_path / "README.md"
            if not readme_path.exists():
                readme_content = f"""# {project_path.name}

A WordPress site migrated to Astro with Decap CMS integration.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## 📝 Content Management

Visit `/admin/` to access the Decap CMS interface for content management.

## 🔧 Development

This site was migrated from WordPress using an automated migration tool that:

- Extracted all WordPress content via REST API
- Converted HTML to Markdown with proper frontmatter
- Generated Astro project structure with content collections
- Set up Decap CMS for ongoing content management
- Configured GitHub integration for version control

## 📁 Project Structure

```
{project_path.name}/
├── src/
│   ├── content/
│   │   ├── blog/          # Blog posts
│   │   └── pages/         # Static pages
│   ├── layouts/           # Astro layouts
│   └── pages/             # Route pages
├── public/
│   ├── admin/             # Decap CMS
│   └── uploads/           # Media files
└── package.json
```

## 🎨 Customization

- Edit layouts in `src/layouts/`
- Modify styles in the layout files
- Add new content types in `public/admin/config.yml`
- Customize the CMS interface as needed

Built with ❤️ using Astro and Decap CMS.
"""
                readme_path.write_text(readme_content)
            
            return repo
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Git repository: {e}")
            raise RuntimeError(f"Git initialization failed: {e}")
    
    def push_to_github(self, project_path: Path, repo_info: GitHubRepoInfo, commit_message: str = None) -> GitHubPushResult:
        """Push the project to GitHub repository.
        
        Args:
            project_path: Path to the project directory
            repo_info: GitHub repository information
            commit_message: Custom commit message
            
        Returns:
            GitHubPushResult with operation details
        """
        try:
            # Initialize Git repository
            repo = self.initialize_git_repo(project_path)
            
            # Add remote origin
            origin_url = f"https://{self.github_token}@github.com/{repo_info.owner}/{repo_info.repo_name}.git"
            
            # Remove existing origin if it exists
            try:
                repo.delete_remote('origin')
            except:
                pass
            
            origin = repo.create_remote('origin', origin_url)
            self.logger.info(f"Added remote origin: {repo_info.html_url}")
            
            # Add all files
            repo.git.add('.')
            
            # Count files to be committed
            files_to_commit = len(list(project_path.rglob('*')))
            self.logger.info(f"Adding {files_to_commit} files to Git")
            
            # Create initial commit
            default_message = f"Initial commit: WordPress to Astro migration"
            commit_msg = commit_message or default_message
            
            try:
                commit = repo.index.commit(commit_msg)
                self.logger.info(f"Created commit: {commit.hexsha[:8]} - {commit_msg}")
            except Exception as e:
                if "nothing to commit" in str(e):
                    self.logger.warning("No changes to commit")
                    return GitHubPushResult(
                        success=True,
                        repo_info=repo_info,
                        error_message="No changes to commit",
                        files_pushed=0
                    )
                else:
                    raise e
            
            # Push to GitHub
            self.logger.info("Pushing to GitHub...")
            origin.push(refspec='HEAD:main')
            
            self.logger.info(f"Successfully pushed to GitHub: {repo_info.html_url}")
            
            return GitHubPushResult(
                success=True,
                repo_info=repo_info,
                commit_hash=commit.hexsha,
                files_pushed=files_to_commit
            )
            
        except Exception as e:
            self.logger.error(f"Failed to push to GitHub: {e}")
            return GitHubPushResult(
                success=False,
                repo_info=repo_info,
                error_message=str(e),
                files_pushed=0
            )
    
    def create_and_push_project(
        self, 
        project_path: Path, 
        repo_name: str,
        description: str = None,
        private: bool = False,
        commit_message: str = None
    ) -> GitHubPushResult:
        """Create a GitHub repository and push the project in one operation.
        
        Args:
            project_path: Path to the project directory
            repo_name: Name of the repository to create
            description: Repository description
            private: Whether the repository should be private
            commit_message: Custom commit message
            
        Returns:
            GitHubPushResult with operation details
        """
        try:
            # Create the repository
            repo_info = self.create_repository(repo_name, description, private)
            
            # Push the project
            result = self.push_to_github(project_path, repo_info, commit_message)
            
            if result.success:
                self.logger.info(f"✅ Successfully created and pushed to: {repo_info.html_url}")
            else:
                self.logger.error(f"❌ Failed to push project: {result.error_message}")
            
            return result
            
        except Exception as e:
            error_details = f"Type: {type(e).__name__}, Message: {str(e) if str(e) else 'No message'}"
            self.logger.error(f"Failed to create and push project: {error_details}")
            self.logger.exception("Full stack trace:")  # This will log the full traceback
            return GitHubPushResult(
                success=False,
                repo_info=GitHubRepoInfo(owner="", repo_name=repo_name),
                error_message=error_details,
                files_pushed=0
            )
    
    def process(self, repo_name: str, project_path: str = None, description: str = None, 
               private: bool = False, commit_message: str = None, *args, **kwargs) -> BaseResult:
        """Main processing method - creates GitHub repository and optionally pushes project.
        
        Args:
            repo_name: Name of the repository to create
            project_path: Optional path to project directory to push
            description: Repository description
            private: Whether the repository should be private
            commit_message: Custom commit message
        """
        try:
            self.validate_input(repo_name, str)
            
            if project_path:
                # Create repository and push project
                result = self.create_and_push_project(
                    Path(project_path),
                    repo_name,
                    description,
                    private,
                    commit_message
                )
                
                return BaseResult(
                    success=result.success,
                    status=AgentStatus.SUCCESS if result.success else AgentStatus.ERROR,
                    data=result,
                    message=f"Successfully created and pushed to {result.repo_info.html_url}" if result.success else "Failed to create/push repository",
                    error=result.error_message if not result.success else None
                )
            else:
                # Just create repository
                repo_info = self.create_repository(repo_name, description, private)
                
                return BaseResult(
                    success=True,
                    status=AgentStatus.SUCCESS,
                    data=repo_info,
                    message=f"Successfully created repository: {repo_info.html_url}"
                )
                
        except Exception as e:
            return BaseResult(
                success=False,
                status=AgentStatus.ERROR,
                error=str(e),
                message="Failed to process GitHub repository operation"
            )
    
    def validate_configuration(self) -> bool:
        """Validate the agent's configuration."""
        if not self.github_token:
            raise ValueError("GitHub token is required")
        
        # Test GitHub API connectivity
        try:
            self.user.login  # Simple API test
        except Exception as e:
            raise ValueError(f"GitHub API access failed: {str(e)}")
        
        return True

def create_github_repo(
    project_path: str,
    repo_name: str,
    github_token: str,
    description: str = None,
    private: bool = False,
    commit_message: str = None
) -> GitHubPushResult:
    """Main function to create a GitHub repository and push an Astro project.
    
    Args:
        project_path: Path to the Astro project directory
        repo_name: Name of the GitHub repository to create
        github_token: Personal access token for GitHub API
        description: Repository description
        private: Whether the repository should be private
        commit_message: Custom commit message
        
    Returns:
        GitHubPushResult with operation details
    """
    agent = GitHubAgent(github_token)
    return agent.create_and_push_project(
        Path(project_path),
        repo_name,
        description,
        private,
        commit_message
    )

def create_and_clone_github_repo(
    repo_name: str,
    local_path: str,
    github_token: str,
    description: str = None,
    private: bool = False
) -> GitHubCloneResult:
    """Main function to create a GitHub repository and clone it locally.
    
    Args:
        repo_name: Name of the GitHub repository to create
        local_path: Local path where to clone the repository
        github_token: Personal access token for GitHub API
        description: Repository description
        private: Whether the repository should be private
        
    Returns:
        GitHubCloneResult with operation details
    """
    agent = GitHubAgent(github_token)
    return agent.create_and_clone_repository(
        repo_name,
        Path(local_path),
        description,
        private
    )
