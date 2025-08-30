#!/usr/bin/env python3
"""
Test script to verify Google Cloud Storage setup for WordPress migration
"""
import os
import sys
from google.cloud import storage

def test_gcs_setup(credentials_path, bucket_name):
    """Test GCS credentials and bucket access"""
    
    print("🔍 Testing Google Cloud Storage setup...")
    print(f"📁 Credentials: {credentials_path}")
    print(f"🪣 Bucket: {bucket_name}")
    print("=" * 50)
    
    # Check if credentials file exists
    if not os.path.exists(credentials_path):
        print(f"❌ Credentials file not found: {credentials_path}")
        return False
    
    print(f"✅ Credentials file found")
    
    try:
        # Set credentials environment variable
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        
        # Initialize client
        print("🔗 Connecting to Google Cloud Storage...")
        client = storage.Client()
        
        # Test bucket access
        print(f"🪣 Testing bucket access: {bucket_name}")
        bucket = client.bucket(bucket_name)
        
        # Check if bucket exists and we can access it
        if bucket.exists():
            print(f"✅ Bucket '{bucket_name}' exists and is accessible")
        else:
            print(f"❌ Bucket '{bucket_name}' not found or not accessible")
            return False
        
        # Test permissions by trying to list objects (won't fail if empty)
        print("🔍 Testing bucket permissions...")
        blobs = list(bucket.list_blobs(max_results=1))
        print(f"✅ Bucket permissions OK (found {len(blobs)} existing objects)")
        
        # Test upload permissions with a small test file
        print("📤 Testing upload permissions...")
        test_blob = bucket.blob("test-wp-migration.txt")
        test_content = "Test file for WordPress migration setup"
        
        test_blob.upload_from_string(test_content, content_type="text/plain")
        
        # Try to make public, fall back to signed URL if blocked
        try:
            test_blob.make_public()
            test_url = test_blob.public_url
            print(f"✅ Upload successful with public URL!")
            print(f"🔗 Test file URL: {test_url}")
        except Exception as e:
            print(f"⚠️ Public access blocked, using signed URL: {str(e)[:100]}...")
            from datetime import datetime, timedelta
            expiration = datetime.utcnow() + timedelta(days=1)
            test_url = test_blob.generate_signed_url(expiration=expiration)
            print(f"✅ Upload successful with signed URL!")
            print(f"🔗 Test file URL: {test_url[:100]}...")
        
        # Clean up test file
        test_blob.delete()
        print("🗑️ Cleaned up test file")
        
        print("\n" + "=" * 50)
        print("🎉 Google Cloud Storage setup is working perfectly!")
        print("💡 You can now run the WordPress migration with media enabled")
        return True
        
    except Exception as e:
        print(f"❌ Error testing GCS setup: {e}")
        print("\n💡 Common issues:")
        print("   • Check your credentials file path")
        print("   • Verify bucket name is correct")
        print("   • Ensure service account has Storage Admin permissions")
        print("   • Check if Cloud Storage API is enabled")
        return False

if __name__ == "__main__":
    print("🔧 Google Cloud Storage Setup Tester")
    print("=" * 50)
    
    # Get credentials from user
    credentials_path = input("Enter GCS credentials JSON path: ").strip()
    if not credentials_path:
        print("❌ No credentials path provided")
        sys.exit(1)
    
    bucket_name = input("Enter GCS bucket name: ").strip()
    if not bucket_name:
        print("❌ No bucket name provided")
        sys.exit(1)
    
    success = test_gcs_setup(credentials_path, bucket_name)
    
    if success:
        print(f"\n✅ Setup verified! Use these values in the migration tool:")
        print(f"   📁 Credentials Path: {credentials_path}")
        print(f"   🪣 Bucket Name: {bucket_name}")
        print(f"   📂 Folder: wp-migration (or leave empty)")
    else:
        print(f"\n❌ Setup failed. Fix the issues above and try again.")
