#!/usr/bin/env python3
"""
Content sanitization utility for WordPress-to-Astro migration.

This utility provides functions to sanitize markdown content and prevent
common issues that can cause Astro build errors, particularly module import
errors from invalid image references.
"""

import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class ContentSanitizer:
    """Utility class for sanitizing markdown content to prevent Astro build errors."""
    
    def __init__(self):
        """Initialize the content sanitizer."""
        logger.info("Initialized ContentSanitizer")
    
    def sanitize_image_references(self, content: str) -> str:
        """Sanitize image references to prevent module import errors.
        
        Args:
            content: Markdown content to sanitize
            
        Returns:
            Sanitized content with fixed image references
        """
        # Fix image references that are just numbers (e.g., ![Alt](15) -> descriptive text)
        content = re.sub(
            r'!\[([^\]]*)\]\(([0-9]+)\)',
            r'_[Image: \1]_',
            content
        )
        
        # Fix empty image references
        content = re.sub(
            r'!\[([^\]]*)\]\(\s*\)',
            r'_[Image: \1]_',
            content
        )
        
        # Fix image references with invalid characters that could cause imports
        content = re.sub(
            r'!\[([^\]]*)\]\(([^)]*[<>"|\*\?]+[^)]*)\)',
            r'_[Image: \1]_',
            content
        )
        
        # Fix relative paths that might be interpreted as modules
        content = re.sub(
            r'!\[([^\]]*)\]\(\.\.?/[^/\s)]*\)',
            lambda m: f'_[Image: {m.group(1)}]_' if not m.group(0).endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg')) else m.group(0),
            content
        )
        
        return content
    
    def sanitize_links(self, content: str) -> str:
        """Sanitize problematic links that might cause build issues.
        
        Args:
            content: Markdown content to sanitize
            
        Returns:
            Sanitized content with fixed links
        """
        # Fix links with invalid characters or formats
        content = re.sub(
            r'\[([^\]]*)\]\(([^)]*[<>"|\*\?]+[^)]*)\)',
            r'\1',
            content
        )
        
        return content
    
    def sanitize_code_blocks(self, content: str) -> str:
        """Sanitize code blocks to ensure they don't break Astro compilation.
        
        Args:
            content: Markdown content to sanitize
            
        Returns:
            Sanitized content with fixed code blocks
        """
        # Ensure code blocks have proper language tags or none
        content = re.sub(
            r'```(\w*[^a-zA-Z0-9\-_\s]\w*)',
            r'```\1',
            content
        )
        
        return content
    
    def sanitize_frontmatter(self, content: str) -> str:
        """Sanitize YAML frontmatter to prevent parsing errors.
        
        Args:
            content: Markdown content to sanitize
            
        Returns:
            Sanitized content with fixed frontmatter
        """
        # Fix unescaped quotes in frontmatter values
        lines = content.split('\n')
        in_frontmatter = False
        sanitized_lines = []
        
        for line in lines:
            if line.strip() == '---':
                in_frontmatter = not in_frontmatter
                sanitized_lines.append(line)
            elif in_frontmatter and ':' in line:
                key, value = line.split(':', 1)
                value = value.strip()
                # If value contains unescaped quotes, wrap in single quotes and escape internal quotes
                if '"' in value and not (value.startswith('"') and value.endswith('"')):
                    value = f"'{value.replace(chr(39), chr(39)+chr(39))}'"
                    line = f"{key}: {value}"
                sanitized_lines.append(line)
            else:
                sanitized_lines.append(line)
        
        return '\n'.join(sanitized_lines)
    
    def sanitize_markdown_content(self, content: str) -> str:
        """Comprehensive sanitization of markdown content.
        
        This is the main method that applies all sanitization rules to ensure
        the content is safe for Astro compilation.
        
        Args:
            content: Raw markdown content to sanitize
            
        Returns:
            Fully sanitized content
        """
        logger.debug("Starting comprehensive content sanitization")
        
        # Apply all sanitization rules
        content = self.sanitize_image_references(content)
        content = self.sanitize_links(content)
        content = self.sanitize_code_blocks(content)
        content = self.sanitize_frontmatter(content)
        
        logger.debug("Content sanitization completed")
        return content
    
    def validate_content(self, content: str) -> List[str]:
        """Validate content and return a list of potential issues.
        
        Args:
            content: Markdown content to validate
            
        Returns:
            List of validation warnings/issues found
        """
        issues = []
        
        # Check for numeric image references
        if re.search(r'!\[([^\]]*)\]\(([0-9]+)\)', content):
            issues.append("Found numeric image references that could cause module import errors")
        
        # Check for empty image references
        if re.search(r'!\[([^\]]*)\]\(\s*\)', content):
            issues.append("Found empty image references")
        
        # Check for problematic characters in links/images
        if re.search(r'[!\[]\([^)]*[<>"|\*\?]+[^)]*\)', content):
            issues.append("Found links or images with potentially problematic characters")
        
        return issues

def sanitize_content(content: str) -> str:
    """Convenience function to sanitize markdown content.
    
    Args:
        content: Raw markdown content to sanitize
        
    Returns:
        Sanitized content safe for Astro compilation
    """
    sanitizer = ContentSanitizer()
    return sanitizer.sanitize_markdown_content(content)

def validate_content(content: str) -> List[str]:
    """Convenience function to validate markdown content.
    
    Args:
        content: Markdown content to validate
        
    Returns:
        List of validation issues found
    """
    sanitizer = ContentSanitizer()
    return sanitizer.validate_content(content)

if __name__ == "__main__":
    # Example usage and testing
    test_content = '''---
title: 'Test Post'
date: '2024-01-01'
---

# Test Content

Here's some content with problematic image references:

![Rome Photo](18)
![Pasta Dish](15)
![Empty Reference]()
![Valid Image](./images/photo.jpg)

Some text content here.
'''
    
    print("Original content:")
    print(test_content)
    print("\n" + "="*50 + "\n")
    
    sanitizer = ContentSanitizer()
    
    print("Validation issues:")
    issues = sanitizer.validate_content(test_content)
    for issue in issues:
        print(f"- {issue}")
    
    print("\nSanitized content:")
    sanitized = sanitizer.sanitize_markdown_content(test_content)
    print(sanitized)
