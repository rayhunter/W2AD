#!/usr/bin/env python3
"""
Comprehensive demo of the BaseAgent system for WP2ASTRO migration.

This script demonstrates all the key features of the BaseAgent architecture.
"""

import sys
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from base_agent import BaseAgent, BaseResult, AgentStatus, batch_process_agents
from extraction_agent import ExtractionAgent
from transform_agent import TransformAgent

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*50}")
    print(f"📋 {title}")
    print('='*50)

def print_subsection(title: str):
    """Print a formatted subsection header."""
    print(f"\n🔸 {title}")
    print('-' * 30)

def demo_agent_creation():
    """Demonstrate agent creation and basic properties."""
    print_section("AGENT CREATION & BASIC PROPERTIES")
    
    print_subsection("Creating TransformAgent")
    transform_agent = TransformAgent(log_level='INFO', validate_inputs=True)
    print(f"   Agent: {transform_agent}")
    print(f"   Status: {transform_agent.get_status()}")
    print(f"   Config keys: {list(transform_agent.get_config().keys())}")
    
    print_subsection("Initial Metrics")
    metrics = transform_agent.get_metrics()
    print(f"   Total operations: {metrics.total_operations}")
    print(f"   Success rate: {metrics.successful_operations}/{metrics.total_operations}")
    print(f"   Average execution time: {metrics.average_execution_time:.4f}s")

def demo_health_checks():
    """Demonstrate health check functionality."""
    print_section("HEALTH CHECKS")
    
    # Healthy agent
    print_subsection("Healthy Agent (TransformAgent)")
    agent = TransformAgent()
    health = agent.health_check()
    print(f"   ✅ Health check: {health.success}")
    print(f"   📊 Message: {health.message}")
    print(f"   📈 Metrics in health data: {health.data['metrics']['total_operations']}")
    
    # Unhealthy agent (with bad configuration)
    print_subsection("Unhealthy Agent (ExtractionAgent with bad URL)")
    try:
        bad_agent = ExtractionAgent("not-a-url")  # This should fail validation
    except Exception as e:
        print(f"   ❌ Agent creation failed as expected: {str(e)[:60]}...")

def demo_metrics_tracking():
    """Demonstrate comprehensive metrics tracking."""
    print_section("METRICS TRACKING")
    
    agent = TransformAgent()
    
    print_subsection("Before Operations")
    print(f"   Operations: {agent.get_metrics().total_operations}")
    
    # Simulate multiple operations
    print_subsection("Executing Test Operations")
    for i in range(3):
        def test_op():
            import time
            time.sleep(0.001)  # Small delay to show execution time
            return f"Result {i+1}"
        
        result = agent._execute_with_metrics(f"test_operation_{i+1}", test_op)
        print(f"   Operation {i+1}: {result.success} (took {result.execution_time:.4f}s)")
    
    print_subsection("Final Metrics")
    final_metrics = agent.get_metrics()
    print(f"   Total operations: {final_metrics.total_operations}")
    print(f"   Successful operations: {final_metrics.successful_operations}")
    print(f"   Average execution time: {final_metrics.average_execution_time:.4f}s")
    print(f"   Total execution time: {final_metrics.total_execution_time:.4f}s")

def demo_error_handling():
    """Demonstrate error handling and recovery."""
    print_section("ERROR HANDLING")
    
    agent = TransformAgent()
    
    print_subsection("Successful Operation")
    def success_op():
        return {"status": "success", "data": "test"}
    
    result = agent._execute_with_metrics("success_test", success_op)
    print(f"   ✅ Success: {result.success}")
    print(f"   📊 Data: {result.data}")
    print(f"   Agent status: {agent.get_status()}")
    
    print_subsection("Failed Operation")
    def failing_op():
        raise ValueError("This operation intentionally fails")
    
    result = agent._execute_with_metrics("failure_test", failing_op)
    print(f"   ❌ Success: {result.success}")
    print(f"   🚨 Error: {result.error}")
    print(f"   Agent status: {agent.get_status()}")
    
    print_subsection("Metrics After Mixed Results")
    metrics = agent.get_metrics()
    print(f"   Total: {metrics.total_operations}")
    print(f"   Successful: {metrics.successful_operations}")
    print(f"   Failed: {metrics.failed_operations}")

def demo_agent_configuration():
    """Demonstrate configuration management."""
    print_section("CONFIGURATION MANAGEMENT")
    
    print_subsection("Initial Configuration")
    agent = TransformAgent(custom_param="initial_value", log_level="DEBUG")
    config = agent.get_config()
    print(f"   Custom param: {config.get('custom_param')}")
    print(f"   Log level: {config.get('log_level')}")
    print(f"   Validation enabled: {config.get('validate_inputs')}")
    
    print_subsection("Updating Configuration")
    agent.update_config(custom_param="updated_value", new_param="added")
    updated_config = agent.get_config()
    print(f"   Custom param: {updated_config.get('custom_param')}")
    print(f"   New param: {updated_config.get('new_param')}")

def demo_validation():
    """Demonstrate input and output validation."""
    print_section("VALIDATION FEATURES")
    
    print_subsection("Input Validation (Enabled)")
    agent = TransformAgent(validate_inputs=True)
    
    try:
        agent.validate_input("test_data", str)
        print("   ✅ String validation passed")
    except ValueError as e:
        print(f"   ❌ Validation failed: {e}")
    
    try:
        agent.validate_input(123, str)  # Should fail
        print("   ✅ Integer as string validation passed")
    except ValueError as e:
        print(f"   ❌ Validation failed as expected: {e}")
    
    print_subsection("Input Validation (Disabled)")
    agent_no_validation = TransformAgent(validate_inputs=False)
    
    try:
        agent_no_validation.validate_input(123, str)  # Should pass now
        print("   ✅ Validation bypassed successfully")
    except ValueError as e:
        print(f"   ❌ Unexpected validation failure: {e}")

def demo_batch_processing():
    """Demonstrate batch processing of multiple agents."""
    print_section("BATCH PROCESSING")
    
    # Create multiple agents
    agents = [
        TransformAgent(name="Transform-1"),
        TransformAgent(name="Transform-2"),
        TransformAgent(name="Transform-3")
    ]
    
    print_subsection("Individual Agent Status")
    for agent in agents:
        print(f"   {agent.name}: {agent.get_status()}")
    
    print_subsection("Batch Health Checks")
    health_results = batch_process_agents(agents, "health_check")
    
    for i, result in enumerate(health_results):
        agent_name = agents[i].name
        print(f"   {agent_name}: {'✅' if result.success else '❌'} {result.message}")

def demo_cleanup():
    """Demonstrate cleanup functionality."""
    print_section("CLEANUP & RESOURCE MANAGEMENT")
    
    agent = TransformAgent()
    
    print_subsection("Before Cleanup")
    print(f"   Agent status: {agent.get_status()}")
    
    print_subsection("Performing Cleanup")
    agent.cleanup()
    print(f"   Agent status after cleanup: {agent.get_status()}")
    
    print_subsection("Resetting Metrics")
    # First, do some operations to have metrics
    agent._execute_with_metrics("test", lambda: "test")
    print(f"   Operations before reset: {agent.get_metrics().total_operations}")
    
    agent.reset_metrics()
    print(f"   Operations after reset: {agent.get_metrics().total_operations}")

def main():
    """Run the comprehensive BaseAgent demonstration."""
    print("🚀 BaseAgent System Comprehensive Demo")
    print("This demo showcases all the key features of the BaseAgent architecture")
    
    try:
        demo_agent_creation()
        demo_health_checks()
        demo_metrics_tracking()
        demo_error_handling()
        demo_agent_configuration()
        demo_validation()
        demo_batch_processing()
        demo_cleanup()
        
        print_section("DEMO COMPLETE")
        print("✨ All BaseAgent features demonstrated successfully!")
        print("\nKey Benefits:")
        print("   📊 Automatic metrics tracking")
        print("   🏥 Built-in health monitoring")
        print("   🚨 Comprehensive error handling")
        print("   🔧 Flexible configuration management")
        print("   ✅ Input/output validation")
        print("   🧹 Resource cleanup")
        print("   📋 Batch processing capabilities")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
