#!/usr/bin/env python3
"""
Test script to validate the BaseAgent implementation.

This script tests the BaseAgent functionality with the updated agents.
"""

import sys
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from base_agent import BaseAgent, BaseResult, AgentStatus, create_agent_result
from extraction_agent import ExtractionAgent
from transform_agent import TransformAgent

def test_base_agent_functionality():
    """Test basic BaseAgent functionality."""
    print("🧪 Testing BaseAgent functionality...")
    
    # Test ExtractionAgent inheritance
    print("\n1. Testing ExtractionAgent inheritance:")
    try:
        # This should fail gracefully since we're using a fake URL
        agent = ExtractionAgent("https://fake-wordpress-site.com", validate_inputs=False)
        print(f"   ✅ ExtractionAgent created: {agent}")
        print(f"   📊 Initial metrics: {agent.get_metrics()}")
        print(f"   🔧 Configuration keys: {list(agent.get_config().keys())}")
        
        # Test health check
        health = agent.health_check()
        print(f"   🏥 Health check: {health.success} - {health.message}")
        
    except Exception as e:
        print(f"   ❌ ExtractionAgent test failed: {e}")
    
    # Test TransformAgent inheritance
    print("\n2. Testing TransformAgent inheritance:")
    try:
        agent = TransformAgent(validate_inputs=False)
        print(f"   ✅ TransformAgent created: {agent}")
        print(f"   📊 Initial metrics: {agent.get_metrics()}")
        print(f"   🔧 Configuration: {agent.get_config()}")
        
        # Test health check
        health = agent.health_check()
        print(f"   🏥 Health check: {health.success} - {health.message}")
        
    except Exception as e:
        print(f"   ❌ TransformAgent test failed: {e}")
    
    # Test BaseResult utility
    print("\n3. Testing BaseResult utility:")
    result = create_agent_result(
        success=True,
        data={"test": "data"},
        message="Test result",
        operation="test"
    )
    print(f"   ✅ Created result: {result.success}, status: {result.status}")
    print(f"   📊 Result metadata: {result.metadata}")
    
    print("\n🎉 BaseAgent functionality tests completed!")

def test_metrics_tracking():
    """Test metrics tracking functionality."""
    print("\n🧪 Testing metrics tracking...")
    
    try:
        agent = TransformAgent()
        print(f"   📊 Initial metrics: {agent.get_metrics().dict()}")
        
        # Simulate some operations by calling _execute_with_metrics directly
        def dummy_operation():
            return "success"
        
        result = agent._execute_with_metrics("test_operation", dummy_operation)
        print(f"   ✅ Operation result: {result.success}")
        print(f"   ⏱️  Execution time: {result.execution_time:.4f}s")
        
        metrics = agent.get_metrics()
        print(f"   📊 Updated metrics: operations={metrics.total_operations}, avg_time={metrics.average_execution_time:.4f}s")
        
    except Exception as e:
        print(f"   ❌ Metrics test failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting BaseAgent tests...")
    
    test_base_agent_functionality()
    test_metrics_tracking()
    
    print("\n✨ All tests completed!")
