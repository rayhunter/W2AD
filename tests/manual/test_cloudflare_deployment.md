# Cloudflare Deployment Test

**Objective**: Verify that the complete WordPress-to-Astro migration pipeline works end-to-end with Cloudflare Pages deployment.

**Duration**: ~25-30 minutes

**Prerequisites**:
- Tool is running locally (`streamlit run app.py`)
- GitHub account with valid Personal Access Token
- Cloudflare account with Pages access
- Cloudflare API token with Pages permissions

## Test Setup

### Cloudflare Setup
1. **Create Cloudflare Account** (if needed): https://dash.cloudflare.com/sign-up
2. **Get Account ID**:
   - Log into Cloudflare dashboard
   - Find Account ID in right sidebar (copy it)
3. **Create API Token**:
   - Visit: https://dash.cloudflare.com/profile/api-tokens
   - Click "Create Token"
   - Use "Custom token" template
   - **Permissions**: `Cloudflare Pages:Edit`, `Account:Read`
   - **Account Resources**: Include your account
   - **Zone Resources**: All zones (or specific zones if preferred)
   - Click "Continue to summary" → "Create Token"
   - **Copy the token** (you won't see it again!)

### GitHub Repository
- Use a fresh repository name for testing
- Ensure your GitHub token has `repo` permissions

## Test Steps

### Step 1: Configure WordPress Source
1. Navigate to `http://localhost:8501`
2. Click on "Customer UI" tab
3. Enter WordPress site URL: `https://demo.wp-api.org/`
4. Leave username/password empty (public site)
5. Verify site connection successful

**Expected Result**: Site connected, basic site information displayed.

### Step 2: Configure GitHub Integration
1. In the same Customer UI page
2. Enter your GitHub username
3. Enter GitHub Personal Access Token
4. Enter a unique repository name (e.g., `wp2astro-cf-test-[timestamp]`)
5. Choose repository visibility (public/private)

**Expected Result**: GitHub configuration accepted.

### Step 3: Configure Cloudflare Deployment
1. Check "Enable Cloudflare Pages deployment"
2. Enter your Cloudflare API Token
3. Enter your Cloudflare Account ID
4. Optional: Enter custom domain (e.g., `test.yourdomain.com`)

**Expected Result**: Cloudflare configuration fields visible and accepted.

### Step 4: Disable Media Migration (for speed)
1. Ensure "Enable media migration to Google Cloud Storage" is unchecked
2. This speeds up testing by skipping GCS setup

**Expected Result**: Media migration disabled for faster testing.

### Step 5: Start Complete Migration
1. Click "🚀 Start Migration" button
2. Monitor progress indicators for all agents:
   - ✅ Extract
   - ⏭️ Media (skipped)
   - ✅ Transform
   - ✅ CMS Config
   - ✅ Scaffold
   - ✅ GitHub
   - ✅ Deploy

**Expected Result**: All agents complete successfully, including new Deploy step.

### Step 6: Verify GitHub Repository
1. Click the GitHub repository URL from results
2. Verify repository contains complete Astro project structure
3. Check that all files are present and correctly structured

**Expected Result**: Complete Astro project in GitHub with all source files.

### Step 7: Verify Cloudflare Pages Project
1. Visit Cloudflare dashboard: https://dash.cloudflare.com/
2. Navigate to "Pages" section
3. Find your new project (should match repository name)
4. Verify project shows "Connected to Git"

**Expected Result**: Cloudflare Pages project created and connected to GitHub.

### Step 8: Monitor Deployment Progress
1. In Cloudflare Pages project, click on "View details"
2. Monitor the build/deployment progress
3. Check build logs for any errors
4. Wait for deployment to complete (usually 2-5 minutes)

**Expected Result**: Build completes successfully, site status shows "Active".

### Step 9: Test Live Site
1. Click the deployment URL from Cloudflare (e.g., `https://project-name.pages.dev`)
2. Verify Astro site loads correctly
3. Navigate to different pages and blog posts
4. Check that all content from WordPress is displayed

**Expected Result**: Live Astro site accessible and displaying migrated WordPress content.

### Step 10: Test CMS Admin Interface
1. Navigate to `https://your-site.pages.dev/admin/`
2. Verify Decap CMS interface loads
3. Check that login options are available
4. Note: Full authentication requires GitHub OAuth setup

**Expected Result**: CMS admin interface loads without errors.

### Step 11: Verify Auto-Deploy Setup
1. In Cloudflare Pages project settings
2. Verify "Build configuration" shows:
   - **Framework preset**: Astro (auto-detected)
   - **Build command**: `npm install && npm run build`
   - **Build output directory**: `dist`
   - **Root directory**: (empty)
3. Check "Git integration" shows connected GitHub repository

**Expected Result**: Auto-deploy configured correctly for future changes.

### Step 12: Test Custom Domain (if configured)
1. If custom domain was provided, check DNS settings in Cloudflare
2. Verify domain points to Cloudflare Pages
3. Test custom domain URL
4. Check SSL certificate status

**Expected Result**: Custom domain works with automatic HTTPS.

## Advanced Verification

### Performance Testing
1. Test site loading speed using browser dev tools
2. Check Lighthouse score for performance
3. Verify images and assets load quickly

**Expected Results**:
- First Contentful Paint < 2 seconds
- Lighthouse Performance score > 90
- All resources load successfully

### SEO and Meta Tags
1. View page source of live site
2. Check that meta tags are present
3. Verify Open Graph tags for social sharing
4. Test site in social media preview tools

**Expected Results**:
- Proper `<title>` tags on all pages
- Meta descriptions present
- Open Graph tags for better social sharing

### Mobile Responsiveness
1. Test site on mobile devices or browser dev tools
2. Verify responsive design works correctly
3. Check touch interactions and navigation

**Expected Results**:
- Site displays correctly on mobile
- Navigation is touch-friendly
- Content scales appropriately

## Verification Checklist

- [ ] Migration completed without errors
- [ ] GitHub repository created with complete project
- [ ] Cloudflare Pages project created and connected
- [ ] Site builds successfully in Cloudflare
- [ ] Live site accessible and displays content correctly
- [ ] CMS admin interface loads properly
- [ ] Auto-deploy configuration is correct
- [ ] Custom domain works (if configured)
- [ ] Performance metrics are acceptable
- [ ] Site is mobile-responsive

## Results Display Verification

Check that the final results display shows:
- [ ] **Blog Posts**: Count > 0
- [ ] **Pages**: Count >= 0  
- [ ] **Media Files**: "⏭️ Skipped" (since disabled)
- [ ] **Files Created**: Count > 10
- [ ] **GitHub Status**: "✅ Pushed" or files count
- [ ] **Deployment**: "✅ Live" with "Cloudflare" delta

## Common Issues & Solutions

**Issue**: Cloudflare deployment fails with "Invalid API token"
- **Solution**: Verify token has `Cloudflare Pages:Edit` permissions
- **Check**: Ensure Account ID is correct (copy from dashboard)

**Issue**: GitHub repository creation succeeds but Cloudflare deployment fails
- **Solution**: Check that GitHub repository is public or Cloudflare has access
- **Debug**: Verify repository exists and is accessible

**Issue**: Cloudflare build fails with "Command not found: npm"
- **Solution**: This shouldn't happen with default Astro preset, check build logs
- **Debug**: Verify Node.js version is supported (18+)

**Issue**: Site deploys but shows 404 errors
- **Solution**: Check build output directory is set to `dist`
- **Debug**: Verify Astro build completed successfully

**Issue**: Custom domain setup fails
- **Solution**: Ensure domain DNS is managed by Cloudflare
- **Check**: Domain must be added to your Cloudflare account first

## Cleanup

After testing:
1. **Delete test GitHub repository** (if desired)
2. **Remove Cloudflare Pages project**:
   - Go to project settings
   - Click "Delete project"
   - Confirm deletion
3. **Revoke API token** (if it was created specifically for testing)

## Success Criteria

✅ **Test Passes If**:
- Complete migration pipeline succeeds without errors
- Cloudflare Pages project is created and configured correctly
- Site builds successfully and is accessible at live URL
- Auto-deploy is configured for future GitHub pushes
- All content displays correctly on live site
- CMS admin interface is accessible

❌ **Test Fails If**:
- Any step in the migration pipeline fails
- Cloudflare deployment fails or site is not accessible
- Content is missing or displays incorrectly
- Build configuration is incorrect
- Auto-deploy is not working

## Performance Benchmarks

**Expected Performance**:
- **Migration Time**: 3-7 minutes (depending on content size)
- **Cloudflare Build Time**: 2-5 minutes (for typical Astro site)
- **Site Loading Speed**: < 2 seconds first load
- **Lighthouse Performance**: > 90
- **Core Web Vitals**: All "Good" ratings

## Next Steps After Successful Test

1. **Configure GitHub OAuth** for Decap CMS authentication
2. **Set up custom domain** with proper DNS
3. **Configure preview deployments** for branch testing
4. **Enable Cloudflare Analytics** for site monitoring
5. **Set up branch protection rules** in GitHub
6. **Document the process** for client handoff

This test validates the complete 7-agent architecture including the new DeployAgent, ensuring clients get a fully deployed, live website ready for immediate use.
