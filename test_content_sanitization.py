#!/usr/bin/env python3
"""
Automated tests for content sanitization to prevent module import errors
in generated Astro projects.
"""

import pytest
import re
from content_sanitizer import ContentSanitizer, sanitize_content, validate_content


class TestContentSanitizer:
    """Test suite for ContentSanitizer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sanitizer = ContentSanitizer()
    
    def test_numeric_image_references(self):
        """Test that numeric image references are properly converted to descriptive text."""
        content = "![Rome Photo](18)\n![Pasta Dish](15)"
        result = self.sanitizer.sanitize_image_references(content)
        
        # Should not contain numeric references
        assert not re.search(r'!\[.*\]\([0-9]+\)', result)
        
        # Should contain descriptive placeholders
        assert "_[Image: Rome Photo]_" in result
        assert "_[Image: Pasta Dish]_" in result
    
    def test_empty_image_references(self):
        """Test that empty image references are properly handled."""
        content = "![Empty Reference]()\n![Another Empty](   )"
        result = self.sanitizer.sanitize_image_references(content)
        
        # Should not contain empty references
        assert not re.search(r'!\[.*\]\(\s*\)', result)
        
        # Should contain descriptive placeholders
        assert "_[Image: Empty Reference]_" in result
        assert "_[Image: Another Empty]_" in result
    
    def test_valid_image_references_preserved(self):
        """Test that valid image references are preserved."""
        content = "![Valid Image](./images/photo.jpg)\n![Another Valid](/uploads/image.png)"
        result = self.sanitizer.sanitize_image_references(content)
        
        # Valid references should be preserved
        assert "![Valid Image](./images/photo.jpg)" in result
        assert "![Another Valid](/uploads/image.png)" in result
    
    def test_problematic_characters_in_image_refs(self):
        """Test that image references with problematic characters are sanitized."""
        content = '![Test Image](<script>alert("bad")</script>)'
        result = self.sanitizer.sanitize_image_references(content)
        
        # Should be converted to descriptive text
        assert "_[Image: Test Image]_" in result
        assert "<script>" not in result
    
    def test_comprehensive_sanitization(self):
        """Test the full sanitization process."""
        problematic_content = '''---
title: 'Test Post with Issues'
date: '2024-01-01'
---

# Test Content

![Rome Photo](18)
![Pasta Dish](15)
![Empty Reference]()
![Script Injection](<script>alert('xss')</script>)
![Valid Image](./images/photo.jpg)

Some content here.
'''
        
        result = self.sanitizer.sanitize_markdown_content(problematic_content)
        
        # Check that all problematic references are fixed
        assert not re.search(r'!\[.*\]\([0-9]+\)', result)
        assert not re.search(r'!\[.*\]\(\s*\)', result)
        assert "<script>" not in result
        
        # Check that valid references are preserved
        assert "![Valid Image](./images/photo.jpg)" in result
        
        # Check that placeholders are created
        assert "_[Image: Rome Photo]_" in result
        assert "_[Image: Pasta Dish]_" in result
    
    def test_validation_detects_issues(self):
        """Test that the validation function properly detects issues."""
        problematic_content = '''![Rome Photo](18)
![Empty Reference]()
![Valid Image](./images/photo.jpg)'''
        
        issues = self.sanitizer.validate_content(problematic_content)
        
        # Should detect numeric and empty references
        assert any("numeric image references" in issue for issue in issues)
        assert any("empty image references" in issue for issue in issues)
    
    def test_validation_clean_content(self):
        """Test that validation returns no issues for clean content."""
        clean_content = '''---
title: 'Clean Post'
date: '2024-01-01'
---

# Clean Content

![Valid Image](./images/photo.jpg)
[Valid Link](https://example.com)

Some clean content here.
'''
        
        issues = self.sanitizer.validate_content(clean_content)
        assert len(issues) == 0
    
    def test_convenience_functions(self):
        """Test the convenience functions work correctly."""
        content = "![Test](15)"
        
        # Test sanitize_content function
        sanitized = sanitize_content(content)
        assert "_[Image: Test]_" in sanitized
        
        # Test validate_content function
        issues = validate_content(content)
        assert len(issues) > 0


class TestIntegrationScenarios:
    """Integration tests for real-world scenarios."""
    
    def test_wordpress_migration_scenario(self):
        """Test a realistic WordPress migration scenario."""
        # Simulate content that might come from a WordPress migration
        wp_content = '''---
title: 'A Weekend in Rome'
date: '2025-07-06T05:09:21'
slug: a-weekend-in-rome
---

## Exploring the Eternal City

Rome is a city filled with history…

![Rome Photo](18)
![Historic Building](19)
![Restaurant View](20)

The trip was amazing! Here are some more images:

![](21)
![Colosseum]()

And a valid image: ![Roman Forum](./images/roman-forum.jpg)
'''
        
        sanitizer = ContentSanitizer()
        result = sanitizer.sanitize_markdown_content(wp_content)
        
        # Verify all problematic references are fixed
        assert not re.search(r'!\[.*\]\([0-9]+\)', result)
        assert not re.search(r'!\[.*\]\(\s*\)', result)
        
        # Verify descriptive placeholders are created
        assert "_[Image: Rome Photo]_" in result
        assert "_[Image: Historic Building]_" in result
        assert "_[Image: Restaurant View]_" in result
        assert "_[Image: Colosseum]_" in result
        
        # Verify valid image is preserved
        assert "![Roman Forum](./images/roman-forum.jpg)" in result
    
    def test_batch_content_processing(self):
        """Test processing multiple content files in batch."""
        contents = [
            "![Test 1](15)",
            "![Test 2](16)\n![Test 3](17)",
            "![Valid](./image.jpg)\n![Invalid](18)"
        ]
        
        sanitizer = ContentSanitizer()
        results = [sanitizer.sanitize_markdown_content(content) for content in contents]
        
        # Verify all numeric references are removed
        for result in results:
            assert not re.search(r'!\[.*\]\([0-9]+\)', result)
        
        # Verify placeholders are created
        assert "_[Image: Test 1]_" in results[0]
        assert "_[Image: Test 2]_" in results[1]
        assert "_[Image: Test 3]_" in results[1]
        assert "_[Image: Invalid]_" in results[2]
        
        # Verify valid references are preserved
        assert "![Valid](./image.jpg)" in results[2]


def test_regression_prevention():
    """Test cases based on the actual issues found in the project."""
    
    # These are the exact problematic patterns found in the generated project
    test_cases = [
        ("![Rome Photo](18)", "_[Image: Rome Photo]_"),
        ("![Pasta Dish](15)", "_[Image: Pasta Dish]_"),
        ("![WordPress Banner](16)", "_[Image: WordPress Banner]_"),
        ("![Python Logo](17)", "_[Image: Python Logo]_"),
    ]
    
    sanitizer = ContentSanitizer()
    
    for input_content, expected_output in test_cases:
        result = sanitizer.sanitize_image_references(input_content)
        assert expected_output in result
        assert not re.search(r'!\[.*\]\([0-9]+\)', result)


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
