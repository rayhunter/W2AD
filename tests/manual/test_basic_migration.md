# Basic Migration Test

**Objective**: Verify that the complete WordPress-to-Astro migration pipeline works end-to-end with a simple WordPress site.

**Duration**: ~15-20 minutes

**Prerequisites**:
- Tool is running locally (`streamlit run app.py`)
- GitHub account with valid Personal Access Token
- Google Cloud Storage credentials (optional for this basic test)

## Test Steps

### Step 1: Start New Migration
1. Navigate to `http://localhost:8501`
2. Verify the WP2ASTRO+Decap interface loads correctly
3. Check that all navigation tabs are visible:
   - 1. ExtractionAgent
   - 2. TransformAgent  
   - 3. MediaAgent
   - 4. CMSConfigAgent
   - 5. ScaffoldAgent
   - 6. GitHubAgent

**Expected Result**: Clean interface with no errors, all tabs accessible.

### Step 2: Configure WordPress Source
1. Click on "1. ExtractionAgent" tab
2. Enter test WordPress site URL: `https://demo.wp-api.org/`
3. Leave username/password fields empty (public site)
4. Click "Test Connection" if available
5. Verify site info is displayed

**Expected Result**: Site connection successful, basic site information displayed.

### Step 3: Configure GitHub Integration
1. Click on "6. GitHubAgent" tab
2. Enter your GitHub username
3. Enter GitHub Personal Access Token
4. Enter a unique repository name (e.g., `wp2astro-test-[timestamp]`)
5. Choose repository visibility (public/private)

**Expected Result**: GitHub credentials accepted, ready for repository creation.

### Step 4: Configure Media Migration (Optional)
1. Click on "3. MediaAgent" tab
2. Toggle "Enable Media Migration" OFF for this basic test
3. Note: This skips GCS requirements for initial testing

**Expected Result**: Media migration disabled, can proceed without GCS credentials.

### Step 5: Start Migration
1. Return to main page
2. Click "Start Migration" button
3. Monitor progress indicators for each agent:
   - ✅ Extract
   - ✅ Transform  
   - ⏭️ Media (skipped)
   - ✅ CMS Config
   - ✅ Scaffold
   - ✅ GitHub

**Expected Result**: All enabled agents complete successfully with green checkmarks.

### Step 6: Verify Results
1. Check the results summary displays:
   - Number of posts migrated
   - Number of pages migrated
   - Project location
   - GitHub repository URL
2. Note the "View Results" section shows:
   - Posts count > 0
   - Pages count >= 0
   - Media Files: 0 (since disabled)

**Expected Result**: Migration completed with content extracted and repository created.

### Step 7: Verify GitHub Repository
1. Click the GitHub repository URL from results
2. Verify repository contains:
   - `README.md`
   - `package.json`
   - `astro.config.mjs`
   - `tsconfig.json`
   - `src/` directory with content
   - `public/admin/` directory with CMS files
3. Check that content files exist in `src/content/blog/` and `src/content/pages/`

**Expected Result**: Complete Astro project structure in GitHub repository.

### Step 8: Verify Local Project
1. Navigate to the local output directory shown in results
2. Verify project structure:
   ```
   output/generated-projects/[project-name]/
   ├── package.json
   ├── astro.config.mjs
   ├── tsconfig.json
   ├── src/
   │   ├── content/
   │   │   ├── blog/
   │   │   └── pages/
   │   ├── layouts/
   │   └── pages/
   └── public/
       └── admin/
   ```

**Expected Result**: Complete project structure locally matches GitHub repository.

### Step 9: Test Local Development Server
1. Open terminal in project directory
2. Run: `npm install`
3. Run: `npm run dev`
4. Navigate to `http://localhost:4321`
5. Verify Astro site loads with migrated content

**Expected Result**: Astro development server runs, site displays migrated WordPress content.

### Step 10: Test CMS Admin Interface
1. Navigate to `http://localhost:4321/admin/`
2. Verify Decap CMS interface loads
3. Check login options are available
4. Note: Full authentication requires deployment, but interface should load

**Expected Result**: CMS admin interface loads without errors.

## Verification Checklist

- [ ] Migration completed without errors
- [ ] All agents showed success status  
- [ ] GitHub repository created successfully
- [ ] Repository contains complete Astro project
- [ ] Local project structure is correct
- [ ] Content files contain migrated WordPress data
- [ ] Astro development server runs successfully
- [ ] CMS admin interface is accessible
- [ ] No console errors during any step

## Common Issues & Solutions

**Issue**: GitHub authentication fails
- **Solution**: Check token permissions include `public_repo` or `repo` scope

**Issue**: WordPress site connection fails  
- **Solution**: Verify URL format includes `http://` or `https://`

**Issue**: No content extracted
- **Solution**: Try a different WordPress site, ensure it has REST API enabled

**Issue**: Astro dev server fails to start
- **Solution**: Check Node.js version (requires 18+), run `npm install` again

## Test Data

**WordPress Test Sites**:
- `https://demo.wp-api.org/` - WordPress.org demo site
- `https://wpthemetestdata.wordpress.com/` - Theme test data
- Any public WordPress site with REST API enabled

**Expected Content Counts**:
- demo.wp-api.org: ~10-15 posts, 2-3 pages
- Actual counts may vary as these are live sites

## Success Criteria

✅ **Test Passes If**:
- Migration completes end-to-end without critical errors
- GitHub repository is created with complete project structure
- Astro development server runs and displays content
- Content matches source WordPress site

❌ **Test Fails If**:
- Any agent fails with unrecoverable error
- GitHub repository is not created or incomplete
- Generated Astro project has build errors
- Significant content is missing or corrupted
