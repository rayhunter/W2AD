# Media Migration Test

**Objective**: Verify that media files are properly downloaded from WordPress and uploaded to Google Cloud Storage with correct link updates.

**Duration**: ~20-25 minutes

**Prerequisites**:
- Tool is running locally (`streamlit run app.py`)
- Google Cloud Storage credentials file
- GCS bucket with appropriate permissions
- WordPress site with images/media

## Test Setup

### GCS Setup
1. Create a test GCS bucket or use existing
2. Ensure service account has `Storage Admin` or `Storage Object Admin` role
3. Download service account JSON credentials file
4. Note bucket name and desired folder path

### WordPress Site
Use a WordPress site with actual images. Recommended test sites:
- `https://demo.wp-api.org/` (limited media)
- Your own test WordPress site with uploaded images
- Public WordPress sites with visible images

## Test Steps

### Step 1: Configure WordPress Source
1. Navigate to "1. ExtractionAgent" tab
2. Enter WordPress site URL with media: `http://www.windsornewmedia.com`
3. Leave credentials empty if public site
4. Verify connection successful

**Expected Result**: Site connected, content preview shows posts with images.

### Step 2: Configure Media Migration
1. Click on "3. MediaAgent" tab
2. Toggle "Enable Media Migration" ON
3. Enter GCS credentials path: `/path/to/service-account.json`
4. Enter GCS bucket name: `your-test-bucket`
5. Enter GCS folder: `wp-migration-test`
6. Verify configuration accepted

**Expected Result**: All GCS fields filled, no validation errors.

### Step 3: Start Migration with Media
1. Return to main page
2. Click "Start Migration" button
3. Monitor each agent carefully:
   - ✅ Extract: Should show posts/pages with image references
   - ✅ Media: Should show "Processing media files..."
   - ✅ Transform: Should process after media migration
   - ✅ CMS Config: Standard configuration
   - ✅ Scaffold: Include updated content with new URLs
   - ✅ GitHub: Deploy complete project

**Expected Result**: All agents complete, Media agent shows successful file processing.

### Step 4: Verify Media Processing Results
1. Check migration results summary:
   - Media Files count > 0
   - Note number of files processed
2. Look for media processing logs in the interface
3. Verify no "0 media URLs extracted" messages

**Expected Result**: Media files count > 0, processing logs show successful downloads and uploads.

### Step 5: Verify GCS Bucket Contents
1. Open Google Cloud Console
2. Navigate to Storage > Buckets > your-test-bucket
3. Check the folder: `wp-migration-test/`
4. Verify uploaded images:
   - File names match original WordPress attachments
   - File sizes are reasonable
   - File types are correct (jpg, png, gif, etc.)

**Expected Result**: Media files uploaded to GCS with proper structure and naming.

### Step 6: Verify Content Link Updates
1. Navigate to generated project: `output/generated-projects/[project-name]/`
2. Open markdown files in `src/content/blog/` and `src/content/pages/`
3. Check image references in content:
   - Should contain GCS URLs: `https://storage.googleapis.com/bucket-name/...`
   - Should NOT contain original WordPress URLs
   - Image alt text should be preserved

**Expected Result**: All image URLs updated to point to GCS, no broken references.

### Step 7: Test GCS URL Access
1. Copy a GCS URL from the migrated content
2. Open the URL in a browser
3. Verify image loads correctly
4. Test multiple image URLs from different posts

**Expected Result**: All GCS URLs are accessible and display images correctly.

### Step 8: Verify Astro Site with Images
1. Navigate to project directory
2. Run: `npm install && npm run dev`
3. Open `http://localhost:4321`
4. Browse posts/pages with images
5. Verify all images load correctly
6. Check browser developer tools for any 404 errors

**Expected Result**: Astro site displays all images without errors.

### Step 9: Test Responsive Image Handling
1. In the Astro development site, open browser developer tools
2. Toggle device simulation (mobile/tablet)
3. Verify images scale appropriately
4. Check that images don't break layout

**Expected Result**: Images display correctly across different viewport sizes.

### Step 10: Verify WordPress Attachment ID Resolution
1. Look for WordPress posts that use attachment IDs (e.g., `src="123"`)
2. Check debug logs for attachment resolution messages
3. Verify these were properly resolved to full URLs
4. Confirm resolved images are included in migration

**Expected Result**: Numeric attachment IDs resolved to full URLs and migrated.

## Advanced Verification

### Test Different Media Types
Verify the migration handles various media types:
- [ ] JPEG images
- [ ] PNG images  
- [ ] GIF images
- [ ] WebP images (if supported by source)
- [ ] PDF documents
- [ ] Other media files

### Test Large Images
1. Find posts with large images (>1MB)
2. Verify these upload successfully to GCS
3. Check that upload doesn't timeout
4. Confirm large images display correctly

### Test Image Captions and Alt Text
1. Find images with captions in WordPress
2. Verify captions are preserved in migrated content
3. Check that alt text is maintained
4. Confirm accessibility attributes are intact

## Verification Checklist

- [ ] Media migration enabled successfully
- [ ] GCS credentials accepted and working
- [ ] Media files detected in WordPress content
- [ ] Files downloaded from WordPress successfully
- [ ] Files uploaded to GCS successfully
- [ ] Content links updated to GCS URLs
- [ ] Original WordPress URLs removed from content
- [ ] All GCS URLs are publicly accessible
- [ ] Images display correctly in Astro site
- [ ] No broken image links or 404 errors
- [ ] WordPress attachment IDs resolved properly
- [ ] Various media types handled correctly

## Common Issues & Solutions

**Issue**: "0 media URLs extracted"
- **Solution**: Check if WordPress site actually has images, verify site URL format
- **Debug**: Use `debug_wp_content.py` to inspect raw WordPress content

**Issue**: GCS upload fails with "403 Public access prevention"
- **Solution**: MediaAgent automatically falls back to signed URLs, this is expected
- **Verify**: Signed URLs should still work for image access

**Issue**: WordPress attachment IDs not resolving
- **Solution**: Check WordPress REST API access at `/wp-json/wp/v2/media/[id]`
- **Debug**: Use `test_attachment_resolution.py` to test specific IDs

**Issue**: Images don't display in Astro site
- **Solution**: Check browser network tab for 404s, verify GCS URLs are correct
- **Debug**: Test GCS URLs directly in browser

**Issue**: GCS authentication fails
- **Solution**: Verify service account JSON file path and permissions
- **Test**: Use `test_gcs_setup.py` to verify GCS connectivity

## Test Data

**WordPress Sites with Media**:
- `http://www.windsornewmedia.com` - Test site with various media
- `https://wordpress.org/news/` - Official WordPress blog with images
- Any WordPress site with visible images in posts

**Expected Behavior**:
- Small sites (1-10 images): Should complete quickly (< 2 minutes)
- Medium sites (10-50 images): Should complete within 5-10 minutes
- Large images (>1MB): May take longer to upload but should succeed

## Success Criteria

✅ **Test Passes If**:
- Media files successfully extracted, uploaded, and linked
- All images display correctly in generated Astro site
- GCS bucket contains all expected media files
- Content URLs properly updated to GCS locations
- No broken image links in final project

❌ **Test Fails If**:
- No media files detected when they exist in WordPress
- GCS upload fails and images are not accessible
- Content still contains original WordPress URLs
- Images display as broken in Astro site
- Significant media files are missing from migration

## Cleanup

After testing:
1. Delete test files from GCS bucket to avoid storage costs
2. Remove test GitHub repository
3. Clean up local generated projects if desired
