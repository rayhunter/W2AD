import streamlit as st
import streamlit_antd_components as sac
import json
import logging
from pathlib import Path
from streamlit_elements import elements, mui, html

# Enable debug logging for media agent
logging.getLogger('media_agent').setLevel(logging.DEBUG)
from extraction_agent import extract_from_wordpress
from transform_agent import transform_bundle
from extraction_agent import WPContentBundle
from media_agent import process_media_migration
from cms_config_agent import generate_cms_config
from scaffold_agent import AstroScaffoldAgent, create_astro_project
from github_agent import create_github_repo
from deploy_agent import deploy_to_cloudflare

# --- Page Configuration ---
st.set_page_config(
    page_title="WP-to-Astro Migration Agents",
    page_icon="🤖",
    layout="wide",
)





# --- Mock Data and State Initialization ---
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'wp_content' not in st.session_state:
    st.session_state.wp_content = None
if 'markdown_bundle' not in st.session_state:
    st.session_state.markdown_bundle = None
if 'cms_config' not in st.session_state:
    st.session_state.cms_config = None
if 'project_scaffold' not in st.session_state:
    st.session_state.project_scaffold = None
if 'github_result' not in st.session_state:
    st.session_state.github_result = None
if 'media_bundle' not in st.session_state:
    st.session_state.media_bundle = None
if 'deploy_result' not in st.session_state:
    st.session_state.deploy_result = None

# --- Main Application UI ---
with elements("main_header"):
    mui.Typography(
        "WordPress-to-Astro Migration with Pydantic Models",
        variant="h4",
        sx={"mb": 1, "color": "primary.main"}
    )
    mui.Typography(
        "An Agent-based migration pipeline.",
        variant="body1",
        sx={"color": "yellow", "mb": 2}
    )

# --- Sidebar Navigation ---
PAGES = {
    "Customer UI": "page_customer_ui",
    "1. ExtractionAgent": "page_extraction",
    "2. TransformAgent": "page_transform", 
    "3. MediaAgent": "page_media",
    "4. CMSConfigAgent": "page_cms_config",
    "5. AstroScaffoldAgent": "page_scaffold",
    "6. GitHubAgent": "page_github",
    "7. DeployAgent": "page_deploy",
}

# --- Navigation ---
selected_page = st.sidebar.selectbox(
    "AGENT WORKFLOW:",
    options=list(PAGES.keys()),
    index=0
)

def page_customer_ui():
    with elements("customer_header"):
        mui.Typography(
            "🎯 Customer Migration Interface",
            variant="h3",
            sx={"mb": 2}
        )
    
    col1, col2 = st.columns(2)
    
    with col1:
        with elements("wp_details_header"):
            mui.Typography(
                "WordPress Site Details",
                variant="h5",
                sx={"mb": 1.5, "fontStyle": "italic","color": "primary.main"}
            )
        site_url = st.text_input("WordPress Site URL", "https://example.com")
        username = st.text_input("Username (optional)")
        password = st.text_input("Password (optional)", type="password")
        
        with elements("target_config_header"):
            mui.Typography(
                "Target Configuration",
                variant="h5",
                sx={"mb": 1.5, "mt": 2, "fontStyle": "italic","color": "primary.main"}
            )
        repo_name = st.text_input("Repository Name", "my-astro-site")
        github_username = st.text_input("GitHub Username", "your-username")
        
        st.subheader(":blue[GitHub Integration]")
        github_token = st.text_input(
            "GitHub Personal Access Token", 
            type="password",
            help="Create a token at: https://github.com/settings/tokens with 'repo' permissions"
        )
        private_repo = st.checkbox("Create private repository", value=False)
        
        st.subheader(":blue[Cloudflare Deployment]")
        enable_cloudflare_deploy = st.checkbox("Enable Cloudflare Pages deployment", value=False)
        
        cloudflare_api_token = None
        cloudflare_account_id = None
        custom_domain = None
        
        if enable_cloudflare_deploy:
            cloudflare_api_token = st.text_input(
                "Cloudflare API Token", 
                type="password",
                help="Create a token at: https://dash.cloudflare.com/profile/api-tokens with Pages permissions"
            )
            cloudflare_account_id = st.text_input(
                "Cloudflare Account ID",
                help="Find your Account ID in the Cloudflare dashboard right sidebar"
            )
            custom_domain = st.text_input(
                "Custom Domain (Optional)",
                placeholder="example.com",
                help="Optional: Custom domain to configure for your site"
            )
        
        st.subheader(":orange[Media Migration (Optional)]")
        enable_media_migration = st.checkbox("Enable media migration to Google Cloud Storage", value=False)
        
        gcs_credentials_path = ""
        gcs_bucket_name = ""
        gcs_folder = ""
        
        if enable_media_migration:
            gcs_credentials_path = st.text_input(
                "GCS Service Account JSON Path",
                placeholder="/path/to/service-account.json",
                help="Path to your Google Cloud Storage service account credentials JSON file"
            )
            gcs_bucket_name = st.text_input(
                "GCS Bucket Name",
                placeholder="my-wp-media-bucket",
                help="Name of the Google Cloud Storage bucket for media files"
            )
            gcs_folder = st.text_input(
                "GCS Folder (Optional)",
                value="wp-migration",
                help="Folder prefix within the bucket (leave empty for root)"
            )
        
    with col2:
        st.subheader(":green[Migration Preview]", divider="green")
        if st.button("🚀 Start Migration", type="primary"):
            with st.spinner("Running migration pipeline..."):
                try:
                    # Step 1: Extract
                    st.info("📥 Extracting WordPress content...")
                    wp_content = extract_from_wordpress(site_url, username, password)
                    st.session_state.wp_content = wp_content
                    
                    # Step 2: Media Migration (if enabled) - BEFORE transform to preserve original URLs
                    if enable_media_migration and gcs_credentials_path and gcs_bucket_name:
                        st.info("📸 Migrating media to Google Cloud Storage...")
                        try:
                            # Work with original WordPress content to preserve image URLs
                            wp_posts = [post.model_dump() for post in wp_content.posts]
                            wp_pages = [page.model_dump() for page in wp_content.pages]
                            
                            media_result = process_media_migration(
                                posts=wp_posts,
                                pages=wp_pages,
                                gcs_credentials_path=gcs_credentials_path,
                                gcs_bucket_name=gcs_bucket_name,
                                gcs_folder=gcs_folder or "wp-migration",
                                wp_site_url=site_url
                            )
                            st.session_state.media_bundle = media_result.media_bundle
                            
                            # Create updated WordPress content with GCS URLs
                            from extraction_agent import WPPost, WPPage, WPContentBundle
                            
                            updated_posts = []
                            for post_data in media_result.posts:
                                updated_post = WPPost(**post_data)
                                updated_posts.append(updated_post)
                            
                            updated_pages = []
                            for page_data in media_result.pages:
                                updated_page = WPPage(**page_data)
                                updated_pages.append(updated_page)
                            
                            # Use updated content for transform step
                            wp_content = WPContentBundle(
                                posts=updated_posts,
                                pages=updated_pages,
                                site_info=wp_content.site_info
                            )
                            
                            st.success(f"✅ Migrated {media_result.media_bundle.successful_uploads} media files to GCS")
                            if media_result.media_bundle.failed_uploads > 0:
                                st.warning(f"⚠️ {media_result.media_bundle.failed_uploads} media files failed to upload")
                                
                        except Exception as e:
                            st.error(f"❌ Media migration failed: {str(e)}")
                            st.info("📝 Continuing with migration without media...")
                    else:
                        if enable_media_migration:
                            st.info("ℹ️ Media migration skipped - missing GCS credentials or bucket name")
                        else:
                            st.info("ℹ️ Media migration disabled - using placeholder text for images")
                    
                    # Step 3: Transform
                    st.info("🔄 Transforming to Markdown...")
                    markdown_bundle = transform_bundle(wp_content)
                    st.session_state.markdown_bundle = markdown_bundle
                    
                    # Convert to final format
                    final_posts = [post.model_dump() for post in markdown_bundle.posts]
                    final_pages = [page.model_dump() for page in markdown_bundle.pages]
                    
                    # Step 4: CMS Config
                    st.info("⚙️ Generating CMS configuration...")
                    repo_info = {
                        "owner": github_username,
                        "repo": repo_name,
                        "branch": "main"
                    }
                    content_structure = {
                        "posts_dir": "src/content/blog",
                        "pages_dir": "src/content/pages",
                        "media_dir": "public/uploads",
                        "public_url": "/uploads"
                    }
                    cms_config = generate_cms_config(repo_info, content_structure)
                    st.session_state.cms_config = cms_config
                    
                    # Step 5: Scaffold Astro Project
                    st.info("🏗️ Creating Astro project...")
                    project_path = f"output/generated-projects/{repo_name}"
                    
                    # Create content files format from processed posts/pages
                    content_files = {
                        "posts": [],
                        "pages": []
                    }
                    
                    # Convert posts to content files
                    for post in final_posts:
                        # Escape single quotes in title
                        escaped_title = post['title'].replace("'", "\'")
                        
                        frontmatter = f"""---
title: '{escaped_title}'
date: '{post['date']}'
slug: {post['slug']}
categories:
{chr(10).join(f'- {cat}' for cat in post.get('categories', []))}
tags:
{chr(10).join(f'- {tag}' for tag in post.get('tags', []))}
---"""
                        file_content = f"{frontmatter}\n\n{post['content']}"
                        content_files["posts"].append({
                            "path": f"src/content/blog/{post['slug']}.md",
                            "content": file_content
                        })
                    
                    # Convert pages to content files
                    for page in final_pages:
                        # Escape single quotes in title
                        escaped_title = page['title'].replace("'", "\'")
                        
                        frontmatter = f"""---
title: '{escaped_title}'
date: '{page['date']}'
slug: {page['slug']}
---"""
                        file_content = f"{frontmatter}\n\n{page['content']}"
                        content_files["pages"].append({
                            "path": f"src/content/pages/{page['slug']}.md",
                            "content": file_content
                        })
                    
                    # Create the project
                    project = create_astro_project(
                        project_root=project_path,
                        content=content_files,
                        cms_config=cms_config.model_dump()
                    )
                    st.session_state.project_scaffold = project
                    
                    # Step 6: GitHub Integration (if token provided)
                    github_success = True  # Track overall success
                    
                    if github_token:
                        st.info("🐙 Creating GitHub repository and pushing code...")
                        try:
                            github_result = create_github_repo(
                                project_path=project_path,
                                repo_name=repo_name,
                                github_token=github_token,
                                description=f"WordPress site migrated to Astro with Decap CMS",
                                private=private_repo,
                                commit_message="Initial commit: WordPress to Astro migration"
                            )
                            st.session_state.github_result = github_result
                            
                            if github_result.success:
                                st.success(f"✅ Successfully pushed to GitHub: {github_result.repo_info.html_url}")
                            else:
                                st.error(f"❌ GitHub push failed: {github_result.error_message}")
                                github_success = False
                        except Exception as e:
                            error_msg = str(e)
                            if "Bad credentials" in error_msg or "401" in error_msg:
                                st.error("❌ GitHub authentication failed: Invalid or expired token")
                                st.info("💡 Please check your GitHub Personal Access Token:")
                                st.info("   • Visit: https://github.com/settings/tokens")
                                st.info("   • Ensure token has 'repo' permissions")
                                st.info("   • Check if token is expired")
                            else:
                                st.error(f"❌ GitHub integration failed: {error_msg}")
                            github_success = False
                    else:
                        st.info("ℹ️ Skipping GitHub integration (no token provided)")
                    
                    # Step 7: Cloudflare Deployment (if enabled and GitHub was successful)
                    deploy_success = True
                    
                    if enable_cloudflare_deploy and cloudflare_api_token and cloudflare_account_id:
                        if github_success and st.session_state.github_result and st.session_state.github_result.success:
                            st.info("☁️ Deploying to Cloudflare Pages...")
                            try:
                                # Extract GitHub repository from result
                                github_repo = f"{github_username}/{repo_name}"
                                
                                deploy_result = deploy_to_cloudflare(
                                    project_name=repo_name,
                                    github_repo=github_repo,
                                    cloudflare_api_token=cloudflare_api_token,
                                    cloudflare_account_id=cloudflare_account_id,
                                    custom_domain=custom_domain if custom_domain else None,
                                    wait_for_completion=False  # Don't wait for build to complete
                                )
                                st.session_state.deploy_result = deploy_result
                                
                                if deploy_result.success:
                                    st.success(f"✅ Successfully deployed to Cloudflare Pages!")
                                    if deploy_result.deployment_url:
                                        st.info(f"🌐 Your site will be available at: {deploy_result.deployment_url}")
                                    if deploy_result.project_url:
                                        st.info(f"📊 Manage your deployment: {deploy_result.project_url}")
                                else:
                                    st.error(f"❌ Cloudflare deployment failed: {deploy_result.error}")
                                    deploy_success = False
                                    
                            except Exception as e:
                                st.error(f"❌ Cloudflare deployment failed: {str(e)}")
                                deploy_success = False
                        else:
                            st.warning("⚠️ Skipping Cloudflare deployment - GitHub integration failed or was skipped")
                            deploy_success = False
                    else:
                        if enable_cloudflare_deploy:
                            st.info("ℹ️ Skipping Cloudflare deployment (missing credentials)")
                        else:
                            st.info("ℹ️ Skipping Cloudflare deployment (not enabled)")
                    
                    # Show appropriate completion message
                    if github_token and not github_success:
                        st.warning("⚠️ Migration completed with errors - Astro project created locally but GitHub push failed")
                        st.info("💡 You can manually push the project later or check your GitHub token")
                    elif enable_cloudflare_deploy and not deploy_success:
                        st.warning("⚠️ Migration completed with partial success - GitHub push succeeded but Cloudflare deployment failed")
                        st.info("💡 You can manually deploy to Cloudflare Pages using the GitHub repository")
                    else:
                        if enable_cloudflare_deploy and deploy_success:
                            st.success("✅ Complete migration pipeline succeeded - Your site is being deployed to Cloudflare Pages!")
                        else:
                            st.success("✅ Migration completed successfully!")
                        st.balloons()
                    
                    # Show results
                    st.subheader("📊 Migration Results")
                    col1, col2, col3, col4, col5, col6 = st.columns(6)
                    
                    with col1:
                        st.metric("Blog Posts", len(wp_content.posts))
                    with col2:
                        st.metric("Pages", len(wp_content.pages))
                    with col3:
                        if st.session_state.media_bundle:
                            st.metric("Media Files", st.session_state.media_bundle.successful_uploads)
                        else:
                            st.metric("Media Files", "⏭️ Skipped")
                    with col4:
                        st.metric("Files Created", len(project.content_files) + len(project.config_files) + len(project.template_files))
                    with col5:
                        if github_token:
                            if st.session_state.github_result and st.session_state.github_result.success:
                                st.metric("Files Pushed", st.session_state.github_result.files_pushed)
                            else:
                                st.metric("GitHub Status", "❌ Failed", delta="Check token")
                        else:
                            st.metric("GitHub Status", "⏭️ Skipped", delta="No token")
                    
                    with col6:
                        if enable_cloudflare_deploy:
                            if st.session_state.deploy_result and st.session_state.deploy_result.success:
                                st.metric("Deployment", "✅ Live", delta="Cloudflare")
                            else:
                                st.metric("Deployment", "❌ Failed", delta="Check credentials")
                        else:
                            st.metric("Deployment", "⏭️ Skipped", delta="Not enabled")
                    
                    st.info(f"🎉 Your Astro site is ready at: `{project_path}`")
                    
                    if st.session_state.github_result and st.session_state.github_result.success:
                        st.success(f"🐙 GitHub Repository: {st.session_state.github_result.repo_info.html_url}")
                        
                        if st.session_state.deploy_result and st.session_state.deploy_result.success:
                            st.success(f"☁️ Live Site: {st.session_state.deploy_result.deployment_url}")
                            st.info("🎯 Next steps: Configure Decap CMS OAuth and customize your site!")
                        else:
                            st.info("🎯 Next steps: Set up hosting (Netlify, Vercel, etc.) and configure Decap CMS OAuth!")
                    else:
                        st.info("📝 Next steps: Push to GitHub and set up hosting!")
                    
                except Exception as e:
                    st.error(f"❌ Migration failed: {str(e)}")

def page_extraction():
    st.header("📥 ExtractionAgent - WordPress Content Extraction")
    
    st.markdown("""
    The ExtractionAgent fetches content from WordPress sites via the REST API.
    """)
    
    if st.session_state.wp_content:
        st.success("✅ WordPress content extracted!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Posts", len(st.session_state.wp_content.posts))
        with col2:
            st.metric("Pages", len(st.session_state.wp_content.pages))
        
        # Show sample post
        if st.session_state.wp_content.posts:
            with st.expander("Sample Post Data"):
                sample_post = st.session_state.wp_content.posts[0]
                st.json(sample_post.model_dump())
    else:
        st.info("Run the migration from the Customer UI to see extracted content.")

def page_transform():
    st.header("🔄 TransformAgent - Content Transformation")
    
    st.markdown("""
    The TransformAgent converts WordPress HTML content to Markdown with YAML frontmatter.
    """)
    
    if st.session_state.markdown_bundle:
        st.success("✅ Content transformed to Markdown!")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Markdown Posts", len(st.session_state.markdown_bundle.posts))
        with col2:
            st.metric("Markdown Pages", len(st.session_state.markdown_bundle.pages))
        
        # Show sample markdown
        if st.session_state.markdown_bundle.posts:
            with st.expander("Sample Markdown Post"):
                sample_post = st.session_state.markdown_bundle.posts[0]
                st.code(f"""---
title: '{sample_post.title}'
date: '{sample_post.date}'
slug: {sample_post.slug}
---

{sample_post.content[:500]}...""", language="markdown")
    else:
        st.info("Run the extraction step first to see transformed content.")

def page_media():
    st.header("📸 MediaAgent - Media Migration to Google Cloud Storage")
    
    st.markdown("""
    The MediaAgent downloads WordPress media files and uploads them to Google Cloud Storage,
    then updates all content links to point to the new GCS URLs.
    """)
    
    if st.session_state.media_bundle:
        st.success("✅ Media migration completed!")
        
        media = st.session_state.media_bundle
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Files", media.total_files)
        with col2:
            st.metric("Successful", media.successful_uploads)
        with col3:
            st.metric("Failed", media.failed_uploads)
        with col4:
            st.metric("Total Size", f"{media.total_size_bytes / 1024 / 1024:.1f} MB")
        
        if media.files:
            with st.expander("Migrated Media Files"):
                for media_file in media.files:
                    st.write(f"**{media_file.filename}**")
                    st.write(f"- Original: {media_file.original_url}")
                    st.write(f"- GCS URL: {media_file.gcs_url}")
                    st.write(f"- Size: {media_file.size_bytes:,} bytes")
                    st.write(f"- Type: {media_file.content_type}")
                    st.write("---")
        
        if media.failed_uploads > 0:
            st.warning(f"⚠️ {media.failed_uploads} files failed to upload. Check your GCS configuration.")
    else:
        st.info("Media migration not performed. Either disabled or run the migration from the Customer UI.")

def page_cms_config():
    st.header("⚙️ CMSConfigAgent - Decap CMS Configuration")
    
    st.markdown("""
    The CMSConfigAgent generates Decap CMS configuration for content management.
    """)
    
    if st.session_state.cms_config:
        st.success("✅ CMS configuration generated!")
        
        with st.expander("CMS Configuration (config.yml)"):
            st.code(st.session_state.cms_config.to_yaml(), language="yaml")
    else:
        st.info("Run the migration from the Customer UI to see CMS configuration.")

def page_scaffold():
    st.header("🏗️ AstroScaffoldAgent - Project Scaffolding")
    
    st.markdown("""
    The AstroScaffoldAgent creates a complete Astro project with Decap CMS integration.
    """)
    
    if st.session_state.project_scaffold:
        st.success("✅ Astro project scaffolded!")
        
        project = st.session_state.project_scaffold
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Content Files", len(project.content_files))
        with col2:
            st.metric("Config Files", len(project.config_files))
        with col3:
            st.metric("Template Files", len(project.template_files))
        
        with st.expander("Project Structure"):
            st.text("Content Files:")
            for file in project.content_files[:5]:  # Show first 5
                st.text(f"  📄 {file}")
            
            st.text("\nConfig Files:")
            for file in project.config_files:
                st.text(f"  ⚙️ {file}")
                
            st.text("\nTemplate Files:")
            for file in project.template_files[:5]:  # Show first 5
                st.text(f"  📋 {file}")
    else:
        st.info("Run the migration from the Customer UI to see scaffolded project.")

def page_github():
    st.header("🐙 GitHubAgent - Repository Creation & Push")
    
    st.markdown("""
    The GitHubAgent creates a GitHub repository and pushes the complete Astro project.
    """)
    
    if st.session_state.github_result:
        if st.session_state.github_result.success:
            st.success("✅ GitHub repository created and project pushed!")
            
            result = st.session_state.github_result
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Files Pushed", result.files_pushed)
            with col2:
                st.metric("Repository", "Created")
            
            with st.expander("Repository Details"):
                st.write(f"**Repository URL:** {result.repo_info.html_url}")
                st.write(f"**Owner:** {result.repo_info.owner}")
                st.write(f"**Repository Name:** {result.repo_info.repo_name}")
                st.write(f"**Private:** {result.repo_info.private}")
                if result.commit_hash:
                    st.write(f"**Latest Commit:** {result.commit_hash[:8]}")
                
                st.markdown("### 🎯 Next Steps")
                st.markdown(f"""
                1. **Visit your repository:** [{result.repo_info.html_url}]({result.repo_info.html_url})
                2. **Set up hosting** (Netlify, Vercel, GitHub Pages, etc.)
                3. **Configure Decap CMS OAuth** for content management
                4. **Customize your site** as needed
                """)
        else:
            st.error("❌ GitHub push failed!")
            st.error(f"Error: {st.session_state.github_result.error_message}")
    else:
        st.info("Run the migration from the Customer UI to see GitHub integration results.")

def page_deploy():
    st.header("☁️ DeployAgent - Cloudflare Pages Deployment")
    
    st.markdown("""
    The DeployAgent automatically deploys your Astro site to Cloudflare Pages with optimized build settings.
    """)
    
    if st.session_state.deploy_result:
        if st.session_state.deploy_result.success:
            st.success("✅ Successfully deployed to Cloudflare Pages!")
            
            result = st.session_state.deploy_result
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Deployment Status", "✅ Live")
            with col2:
                st.metric("Platform", "Cloudflare Pages")
            
            with st.expander("Deployment Details"):
                if result.deployment_url:
                    st.write(f"**Live Site:** [{result.deployment_url}]({result.deployment_url})")
                if result.project_url:
                    st.write(f"**Project Dashboard:** [{result.project_url}]({result.project_url})")
                if result.deployment_id:
                    st.write(f"**Deployment ID:** {result.deployment_id}")
                
                st.markdown("### ⚙️ Build Configuration")
                st.code("""
Build Command: npm install && npm run build
Output Directory: dist
Node Version: 18
Framework: Astro (Auto-detected)
                """)
                
                st.markdown("### 🎯 Next Steps")
                st.markdown(f"""
                1. **Visit your live site:** [{result.deployment_url}]({result.deployment_url}) 
                2. **Configure custom domain** (if needed) in Cloudflare dashboard
                3. **Set up Decap CMS OAuth** for content management
                4. **Configure preview deployments** for branches
                5. **Monitor analytics** in Cloudflare dashboard
                """)
                
                st.markdown("### 🔄 Auto-Deploy")
                st.info("✅ Your site will automatically redeploy when you push changes to your GitHub repository!")
                
        else:
            st.error("❌ Cloudflare deployment failed!")
            st.error(f"Error: {st.session_state.deploy_result.error}")
            
            st.markdown("### 🔧 Troubleshooting")
            st.markdown("""
            **Common issues:**
            - Invalid Cloudflare API token or Account ID
            - Insufficient API token permissions (needs Pages permissions)
            - GitHub repository not accessible
            - Project name conflicts with existing Cloudflare project
            
            **How to fix:**
            1. Verify your Cloudflare API token at: https://dash.cloudflare.com/profile/api-tokens
            2. Ensure token has "Cloudflare Pages:Edit" permissions
            3. Check that your Account ID is correct
            4. Try a different project name if there's a naming conflict
            """)
    else:
        st.info("Run the migration from the Customer UI with Cloudflare deployment enabled to see results.")
        
        st.markdown("### 🚀 About Cloudflare Pages")
        st.markdown("""
        Cloudflare Pages provides:
        - **Global CDN** - Fast content delivery worldwide
        - **Automatic SSL** - HTTPS enabled by default  
        - **Git Integration** - Auto-deploy from GitHub
        - **Preview Deployments** - Test changes before going live
        - **Analytics** - Built-in web analytics
        - **Custom Domains** - Easy domain setup
        - **Edge Functions** - Serverless functions at the edge
        """)

# --- Page Routing ---
def display_page(page_name):
    if page_name == "page_customer_ui":
        page_customer_ui()
    elif page_name == "page_extraction":
        page_extraction()
    elif page_name == "page_transform":
        page_transform()
    elif page_name == "page_media":
        page_media()
    elif page_name == "page_cms_config":
        page_cms_config()
    elif page_name == "page_scaffold":
        page_scaffold()
    elif page_name == "page_github":
        page_github()
    elif page_name == "page_deploy":
        page_deploy()

# Display the selected page
display_page(PAGES[selected_page])
