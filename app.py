import streamlit as st
import streamlit_antd_components as sac
import json
import logging
from pathlib import Path
from extraction_agent import extract_from_wordpress
from transform_agent import transform_bundle
from extraction_agent import WPContentBundle
from cms_config_agent import generate_cms_config
from scaffold_agent import AstroScaffoldAgent, create_astro_project

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

# --- Main Application UI ---
st.title("WordPress-to-Astro Migration with Pydantic Models")
st.markdown("A demonstration of the agent-based migration pipeline.")

# --- Sidebar Navigation ---
PAGES = {
    "Customer UI": "page_customer_ui",
    "1. ExtractionAgent": "page_extraction",
    "2. TransformAgent": "page_transform", 
    "3. CMSConfigAgent": "page_cms_config",
    "4. AstroScaffoldAgent": "page_scaffold",
}
st.sidebar.title("Agent Workflow")

# --- Navigation ---
selected_page = st.sidebar.selectbox(
    "Select Stage:",
    options=list(PAGES.keys()),
    index=0
)

def page_customer_ui():
    st.header("🎯 Customer Migration Interface")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("WordPress Site Details")
        site_url = st.text_input("WordPress Site URL", "https://example.com")
        username = st.text_input("Username (optional)")
        password = st.text_input("Password (optional)", type="password")
        
        st.subheader("Target Configuration")
        repo_name = st.text_input("Repository Name", "my-astro-site")
        github_username = st.text_input("GitHub Username", "your-username")
        
    with col2:
        st.subheader("Migration Preview")
        if st.button("🚀 Start Migration", type="primary"):
            with st.spinner("Running migration pipeline..."):
                try:
                    # Step 1: Extract
                    st.info("📥 Extracting WordPress content...")
                    wp_content = extract_from_wordpress(site_url, username, password)
                    st.session_state.wp_content = wp_content
                    
                    # Step 2: Transform
                    st.info("🔄 Transforming to Markdown...")
                    markdown_bundle = transform_bundle(wp_content)
                    st.session_state.markdown_bundle = markdown_bundle
                    
                    # Step 3: CMS Config
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
                    
                    # Step 4: Scaffold
                    st.info("🏗️ Creating Astro project...")
                    project_path = f"output/generated-projects/{repo_name}"
                    
                    # Convert markdown bundle to content files format
                    from transform_agent import TransformAgent
                    transform_agent = TransformAgent()
                    content_files = transform_agent.create_content_files(markdown_bundle)
                    
                    # Create the project
                    project = create_astro_project(
                        project_root=project_path,
                        content=content_files,
                        cms_config=cms_config.model_dump()
                    )
                    st.session_state.project_scaffold = project
                    
                    st.success("✅ Migration completed successfully!")
                    st.balloons()
                    
                    # Show results
                    st.subheader("📊 Migration Results")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Blog Posts", len(wp_content.posts))
                    with col2:
                        st.metric("Pages", len(wp_content.pages))
                    with col3:
                        st.metric("Files Created", len(project.content_files) + len(project.config_files) + len(project.template_files))
                    
                    st.info(f"🎉 Your Astro site is ready at: `{project_path}`")
                    st.info("Next steps: Deploy to GitHub and set up hosting!")
                    
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

# --- Page Routing ---
def display_page(page_name):
    if page_name == "page_customer_ui":
        page_customer_ui()
    elif page_name == "page_extraction":
        page_extraction()
    elif page_name == "page_transform":
        page_transform()
    elif page_name == "page_cms_config":
        page_cms_config()
    elif page_name == "page_scaffold":
        page_scaffold()

# Display the selected page
display_page(PAGES[selected_page])
