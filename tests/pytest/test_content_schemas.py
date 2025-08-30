#!/usr/bin/env python3
"""
Test suite for Content Collection Schemas

This module provides comprehensive tests for the Pydantic models used
for type-safe handling of WordPress content during migration.

Author: AI Assistant
Date: 2025-08-28
"""

import pytest
from datetime import datetime
from typing import Dict, Any
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from content_schemas import (
    ContentStatus,
    ContentType,
    MediaType,
    BaseContent,
    WordPressPost,
    WordPressPage,
    MediaAttachment,
    ContentTaxonomy,
    ContentComment,
    ContentCollection,
    validate_wordpress_export,
    create_content_schema_mapping,
)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print('='*60)


def print_subsection(title: str):
    """Print a formatted subsection header."""
    print(f"\n🔸 {title}")
    print('-' * 40)


class TestContentSchemas:
    """Test content schema validation and functionality."""
    
    def test_base_content_creation(self):
        """Test BaseContent model creation and validation."""
        print_subsection("Testing BaseContent Creation")
        
        # Test valid content creation
        content = BaseContent(
            id=1,
            title="Test Content",
            type=ContentType.POST,
            author_name="Test Author"
        )
        
        assert content.id == 1
        assert content.title == "Test Content"
        assert content.slug == "test-content"  # Auto-generated from title
        assert content.type == ContentType.POST
        assert content.author_name == "Test Author"
        
        print("   ✅ BaseContent created successfully")
        print(f"   📝 Auto-generated slug: '{content.slug}'")
        
    def test_wordpress_post_schema(self):
        """Test WordPressPost schema validation."""
        print_subsection("Testing WordPressPost Schema")
        
        post_data = {
            "id": 1,
            "title": "My Blog Post",
            "content": "This is the post content.",
            "categories": ["Technology", "Programming"],
            "tags": ["python", "web-development"],
            "featured_image": "https://example.com/image.jpg",
            "date_created": "2023-12-01T10:00:00Z",
            "author_name": "John Doe",
            "status": "publish"
        }
        
        post = WordPressPost(**post_data)
        
        assert post.title == "My Blog Post"
        assert post.type == ContentType.POST  # Automatically set
        assert len(post.categories) == 2
        assert len(post.tags) == 2
        assert post.featured_image == "https://example.com/image.jpg"
        assert post.status == ContentStatus.PUBLISH
        
        print("   ✅ WordPressPost created successfully")
        print(f"   📂 Categories: {post.categories}")
        print(f"   🏷️  Tags: {post.tags}")
        
    def test_wordpress_page_schema(self):
        """Test WordPressPage schema validation."""
        print_subsection("Testing WordPressPage Schema")
        
        page_data = {
            "id": 2,
            "title": "About Us",
            "content": "This is the about page.",
            "template": "page-about.php",
            "is_front_page": False,
            "author_name": "Admin",
            "date_created": "2023-11-15T14:30:00Z"
        }
        
        page = WordPressPage(**page_data)
        
        assert page.title == "About Us"
        assert page.type == ContentType.PAGE  # Automatically set
        assert page.template == "page-about.php"
        assert not page.is_front_page
        
        print("   ✅ WordPressPage created successfully")
        print(f"   🎨 Template: {page.template}")
        
    def test_media_attachment_schema(self):
        """Test MediaAttachment schema validation."""
        print_subsection("Testing MediaAttachment Schema")
        
        media_data = {
            "id": 3,
            "title": "Sample Image",
            "file_url": "https://example.com/uploads/2023/12/sample.jpg",
            "mime_type": "image/jpeg",
            "file_size": 150000,
            "alt_text": "A sample image",
            "width": 1920,
            "height": 1080,
            "author_name": "Photographer"
        }
        
        media = MediaAttachment(**media_data)
        
        assert media.title == "Sample Image"
        assert media.type == ContentType.ATTACHMENT  # Automatically set
        assert media.media_type == MediaType.IMAGE  # Auto-determined from MIME type
        assert media.file_name == "sample.jpg"  # Auto-extracted from URL
        assert media.width == 1920
        assert media.height == 1080
        
        print("   ✅ MediaAttachment created successfully")
        print(f"   🖼️  Media type: {media.media_type}")
        print(f"   📁 File name: {media.file_name}")
        
    def test_content_taxonomy_schema(self):
        """Test ContentTaxonomy schema validation."""
        print_subsection("Testing ContentTaxonomy Schema")
        
        category_data = {
            "term_id": 1,
            "name": "Web Development",
            "description": "Posts about web development",
            "taxonomy": "category",
            "count": 25
        }
        
        category = ContentTaxonomy(**category_data)
        
        assert category.name == "Web Development"
        assert category.slug == "web-development"  # Auto-generated from name
        assert category.taxonomy == "category"
        assert category.count == 25
        
        print("   ✅ ContentTaxonomy created successfully")
        print(f"   🏷️  Auto-generated slug: '{category.slug}'")
        
    def test_content_comment_schema(self):
        """Test ContentComment schema validation."""
        print_subsection("Testing ContentComment Schema")
        
        comment_data = {
            "comment_id": 1,
            "post_id": 1,
            "author_name": "Jane Smith",
            "author_email": "jane@example.com",
            "content": "Great post! Thanks for sharing.",
            "date": "2023-12-01T15:30:00Z",
            "approved": True
        }
        
        comment = ContentComment(**comment_data)
        
        assert comment.comment_id == 1
        assert comment.post_id == 1
        assert comment.author_name == "Jane Smith"
        assert comment.content == "Great post! Thanks for sharing."
        assert comment.approved is True
        
        print("   ✅ ContentComment created successfully")
        print(f"   👤 Author: {comment.author_name}")
        
    def test_frontmatter_generation(self):
        """Test Astro frontmatter generation."""
        print_subsection("Testing Frontmatter Generation")
        
        post = WordPressPost(
            id=1,
            title="Test Post",
            categories=["Tech"],
            tags=["python", "astro"],
            featured_image="https://example.com/hero.jpg",
            date_created=datetime(2023, 12, 1, 10, 0, 0),
            author_name="Test Author",
            excerpt="This is a test post",
            status=ContentStatus.PUBLISH
        )
        
        frontmatter = post.to_frontmatter()
        
        assert frontmatter['title'] == "Test Post"
        assert frontmatter['categories'] == ["Tech"]
        assert frontmatter['tags'] == ["python", "astro"]
        assert frontmatter['heroImage'] == "https://example.com/hero.jpg"
        assert frontmatter['author'] == "Test Author"
        assert frontmatter['description'] == "This is a test post"
        assert frontmatter['draft'] is False
        
        print("   ✅ Frontmatter generated successfully")
        print(f"   📋 Keys: {list(frontmatter.keys())}")


class TestContentCollection:
    """Test ContentCollection functionality."""
    
    def create_sample_collection(self) -> ContentCollection:
        """Create a sample content collection for testing."""
        collection = ContentCollection()
        
        # Add sample posts
        collection.posts = [
            WordPressPost(
                id=1,
                title="First Post",
                categories=["Tech"],
                status=ContentStatus.PUBLISH
            ),
            WordPressPost(
                id=2,
                title="Draft Post",
                categories=["Tech"],
                status=ContentStatus.DRAFT
            )
        ]
        
        # Add sample pages
        collection.pages = [
            WordPressPage(
                id=3,
                title="About",
                status=ContentStatus.PUBLISH
            )
        ]
        
        # Add sample media
        collection.media = [
            MediaAttachment(
                id=4,
                title="Hero Image",
                file_url="https://example.com/hero.jpg",
                mime_type="image/jpeg",
                file_size=100000
            ),
            MediaAttachment(
                id=5,
                title="Document",
                file_url="https://example.com/doc.pdf",
                mime_type="application/pdf",
                file_size=200000
            )
        ]
        
        # Add sample categories and tags
        collection.categories = [
            ContentTaxonomy(
                term_id=1,
                name="Tech",
                taxonomy="category",
                count=2
            )
        ]
        
        collection.tags = [
            ContentTaxonomy(
                term_id=2,
                name="python",
                taxonomy="post_tag",
                count=1
            )
        ]
        
        # Add sample comments
        collection.comments = [
            ContentComment(
                comment_id=1,
                post_id=1,
                author_name="Commenter",
                content="Great post!"
            )
        ]
        
        return collection
        
    def test_collection_properties(self):
        """Test ContentCollection properties."""
        print_subsection("Testing ContentCollection Properties")
        
        collection = self.create_sample_collection()
        
        assert collection.total_content_items == 4  # 2 posts + 1 page + 2 media
        assert len(collection.published_posts) == 1  # Only one published post
        assert len(collection.published_pages) == 1  # One published page
        
        # Test filtering
        tech_posts = collection.get_posts_by_category("Tech")
        assert len(tech_posts) == 2
        
        images = collection.get_media_by_type(MediaType.IMAGE)
        assert len(images) == 1
        
        documents = collection.get_media_by_type(MediaType.DOCUMENT)
        assert len(documents) == 1
        
        print("   ✅ Collection properties working correctly")
        print(f"   📊 Total items: {collection.total_content_items}")
        print(f"   📝 Published posts: {len(collection.published_posts)}")
        
    def test_content_statistics(self):
        """Test content statistics generation."""
        print_subsection("Testing Content Statistics")
        
        collection = self.create_sample_collection()
        stats = collection.get_content_statistics()
        
        assert stats['total_posts'] == 2
        assert stats['published_posts'] == 1
        assert stats['draft_posts'] == 1
        assert stats['total_pages'] == 1
        assert stats['total_media'] == 2
        assert stats['images'] == 1
        assert stats['documents'] == 1
        assert stats['categories'] == 1
        assert stats['tags'] == 1
        assert stats['comments'] == 1
        assert stats['total_content_size'] == 300000  # 100k + 200k
        
        print("   ✅ Statistics generated correctly")
        print(f"   📈 Stats: {stats}")
        
    def test_content_validation(self):
        """Test content reference validation."""
        print_subsection("Testing Content Validation")
        
        collection = self.create_sample_collection()
        
        # Add invalid references
        collection.posts.append(
            WordPressPost(
                id=6,
                title="Invalid Post",
                featured_image="https://example.com/missing.jpg",  # Missing media
                parent_id=999  # Missing parent
            )
        )
        
        collection.comments.append(
            ContentComment(
                comment_id=2,
                post_id=999,  # Missing post
                author_name="Orphan Comment",
                content="This comment is orphaned"
            )
        )
        
        errors = collection.validate_content_references()
        
        assert 'missing_media' in errors
        assert 'missing_parents' in errors
        assert 'orphaned_comments' in errors
        assert len(errors['missing_media']) == 1
        assert len(errors['missing_parents']) == 1
        assert len(errors['orphaned_comments']) == 1
        
        print("   ✅ Validation errors detected correctly")
        print(f"   ⚠️  Validation errors: {len(errors)} types found")


class TestSchemaUtilities:
    """Test schema utility functions."""
    
    def test_schema_mapping(self):
        """Test content schema mapping utility."""
        print_subsection("Testing Schema Mapping")
        
        mapping = create_content_schema_mapping()
        
        assert mapping['post'] == WordPressPost
        assert mapping['page'] == WordPressPage
        assert mapping['attachment'] == MediaAttachment
        assert mapping['category'] == ContentTaxonomy
        assert mapping['tag'] == ContentTaxonomy
        assert mapping['comment'] == ContentComment
        
        print("   ✅ Schema mapping created correctly")
        print(f"   🗂️  Available schemas: {list(mapping.keys())}")
        
    def test_wordpress_export_validation(self):
        """Test WordPress export data validation."""
        print_subsection("Testing WordPress Export Validation")
        
        # Sample WordPress export data structure
        export_data = {
            "posts": [
                {
                    "id": 1,
                    "title": "Sample Post",
                    "post_type": "post",
                    "author_name": "Author",
                    "categories": ["Tech"]
                },
                {
                    "id": 2,
                    "title": "Sample Page",
                    "post_type": "page",
                    "author_name": "Author"
                },
                {
                    "id": 3,
                    "title": "Sample Image",
                    "post_type": "attachment",
                    "file_url": "https://example.com/image.jpg",
                    "mime_type": "image/jpeg"
                }
            ],
            "categories": [
                {
                    "term_id": 1,
                    "name": "Technology",
                    "taxonomy": "category"
                }
            ],
            "tags": [
                {
                    "term_id": 2,
                    "name": "python",
                    "taxonomy": "post_tag"
                }
            ],
            "comments": [
                {
                    "comment_id": 1,
                    "post_id": 1,
                    "author_name": "Commenter",
                    "content": "Great post!"
                }
            ]
        }
        
        try:
            collection = validate_wordpress_export(export_data)
            
            assert len(collection.posts) == 1
            assert len(collection.pages) == 1
            assert len(collection.media) == 1
            assert len(collection.categories) == 1
            assert len(collection.tags) == 1
            assert len(collection.comments) == 1
            
            print("   ✅ WordPress export validated successfully")
            print(f"   📊 Collection stats: {collection.get_content_statistics()}")
            
        except Exception as e:
            print(f"   ❌ Validation failed: {e}")
            raise


def run_schema_tests():
    """Run all schema tests."""
    print("🚀 Starting Content Schemas Test Suite")
    print("Testing Pydantic models for type-safe WordPress content handling")
    
    test_results = []
    
    try:
        # Test content schemas
        print_section("TESTING CONTENT SCHEMAS")
        
        schema_tests = TestContentSchemas()
        
        try:
            schema_tests.test_base_content_creation()
            test_results.append(("Base Content Creation", True))
        except Exception as e:
            print(f"   ❌ Base content test failed: {e}")
            import traceback
            traceback.print_exc()
            test_results.append(("Base Content Creation", False))
            
        try:
            schema_tests.test_wordpress_post_schema()
            test_results.append(("WordPress Post Schema", True))
        except Exception as e:
            print(f"   ❌ Post schema test failed: {e}")
            test_results.append(("WordPress Post Schema", False))
            
        try:
            schema_tests.test_wordpress_page_schema()
            test_results.append(("WordPress Page Schema", True))
        except Exception as e:
            print(f"   ❌ Page schema test failed: {e}")
            test_results.append(("WordPress Page Schema", False))
            
        try:
            schema_tests.test_media_attachment_schema()
            test_results.append(("Media Attachment Schema", True))
        except Exception as e:
            print(f"   ❌ Media schema test failed: {e}")
            test_results.append(("Media Attachment Schema", False))
            
        try:
            schema_tests.test_content_taxonomy_schema()
            test_results.append(("Content Taxonomy Schema", True))
        except Exception as e:
            print(f"   ❌ Taxonomy schema test failed: {e}")
            test_results.append(("Content Taxonomy Schema", False))
            
        try:
            schema_tests.test_content_comment_schema()
            test_results.append(("Content Comment Schema", True))
        except Exception as e:
            print(f"   ❌ Comment schema test failed: {e}")
            test_results.append(("Content Comment Schema", False))
            
        try:
            schema_tests.test_frontmatter_generation()
            test_results.append(("Frontmatter Generation", True))
        except Exception as e:
            print(f"   ❌ Frontmatter test failed: {e}")
            test_results.append(("Frontmatter Generation", False))
        
        # Test content collection
        print_section("TESTING CONTENT COLLECTION")
        
        collection_tests = TestContentCollection()
        
        try:
            collection_tests.test_collection_properties()
            test_results.append(("Collection Properties", True))
        except Exception as e:
            print(f"   ❌ Collection properties test failed: {e}")
            test_results.append(("Collection Properties", False))
            
        try:
            collection_tests.test_content_statistics()
            test_results.append(("Content Statistics", True))
        except Exception as e:
            print(f"   ❌ Statistics test failed: {e}")
            test_results.append(("Content Statistics", False))
            
        try:
            collection_tests.test_content_validation()
            test_results.append(("Content Validation", True))
        except Exception as e:
            print(f"   ❌ Validation test failed: {e}")
            test_results.append(("Content Validation", False))
        
        # Test utilities
        print_section("TESTING SCHEMA UTILITIES")
        
        utility_tests = TestSchemaUtilities()
        
        try:
            utility_tests.test_schema_mapping()
            test_results.append(("Schema Mapping", True))
        except Exception as e:
            print(f"   ❌ Schema mapping test failed: {e}")
            test_results.append(("Schema Mapping", False))
            
        try:
            utility_tests.test_wordpress_export_validation()
            test_results.append(("WordPress Export Validation", True))
        except Exception as e:
            print(f"   ❌ Export validation test failed: {e}")
            test_results.append(("WordPress Export Validation", False))
        
        # Print results
        print_section("TEST RESULTS SUMMARY")
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status} {test_name}")
            if result:
                passed += 1
        
        print(f"\n📊 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 ALL SCHEMA TESTS PASSED!")
            print("✨ Content schemas are working correctly!")
            print("\n🔧 Schema Features Validated:")
            print("   ✅ Pydantic model validation")
            print("   ✅ Automatic field generation (slugs, media types)")
            print("   ✅ Date parsing and formatting")
            print("   ✅ Astro frontmatter generation")
            print("   ✅ Content collection management")
            print("   ✅ Reference validation")
            print("   ✅ Statistics and filtering")
            print("   ✅ WordPress export validation")
        else:
            print(f"\n⚠️  {total - passed} tests failed - check the details above")
        
    except Exception as e:
        print(f"❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_schema_tests()
