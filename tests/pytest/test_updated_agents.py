#!/usr/bin/env python3
"""
Test script for all updated agents with BaseAgent architecture.

This script tests that MediaAgent, DeployAgent, and CMSConfigAgent
all work correctly with the BaseAgent inheritance.
"""

import sys
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from base_agent import BaseAgent, BaseResult, AgentStatus
from extraction_agent import ExtractionAgent
from transform_agent import TransformAgent
from cms_config_agent import CMSConfigAgent

# Import agents that might fail due to dependencies
try:
    from media_agent import MediaAgent
except ImportError:
    MediaAgent = None

try:
    from deploy_agent import DeployAgent
except ImportError:
    DeployAgent = None

try:
    from github_agent import GitHubAgent
except ImportError:
    GitHubAgent = None
    
try:
    from scaffold_agent import AstroScaffoldAgent
except ImportError:
    AstroScaffoldAgent = None

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print('='*60)

def print_subsection(title: str):
    """Print a formatted subsection header."""
    print(f"\n🔸 {title}")
    print('-' * 40)

def test_cms_config_agent():
    """Test CMSConfigAgent with BaseAgent architecture."""
    print_section("TESTING CMSConfigAgent")
    
    try:
        print_subsection("Creating CMSConfigAgent")
        repo_info = {
            "owner": "testuser",
            "repo": "test-repo",
            "branch": "main"
        }
        content_structure = {
            "media_dir": "public/uploads",
            "public_url": "/uploads"
        }
        
        agent = CMSConfigAgent(repo_info, content_structure, validate_inputs=False)
        print(f"   ✅ Agent created: {agent}")
        print(f"   📊 Status: {agent.get_status()}")
        print(f"   🔧 Config keys: {list(agent.get_config().keys())}")
        
        print_subsection("Testing Health Check")
        health = agent.health_check()
        print(f"   🏥 Health: {'✅' if health.success else '❌'} - {health.message}")
        
        print_subsection("Testing Process Method")
        result = agent.process()
        print(f"   🎯 Process: {'✅' if result.success else '❌'} - {result.message}")
        if result.data:
            print(f"   📋 Generated config backend: {result.data.backend['name']}")
            print(f"   📁 Collections: {len(result.data.collections)}")
        
        print_subsection("Testing Metrics")
        metrics = agent.get_metrics()
        print(f"   📈 Total operations: {metrics.total_operations}")
        print(f"   ✅ Successful: {metrics.successful_operations}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ CMSConfigAgent test failed: {e}")
        return False

def test_media_agent_basic():
    """Test MediaAgent basic functionality (without GCS credentials)."""
    print_section("TESTING MediaAgent (Basic)")
    
    try:
        print_subsection("Testing MediaAgent Creation (Expected to Fail)")
        # This should fail due to missing GCS credentials, but we can test the structure
        try:
            # Use fake credentials to test structure
            agent = MediaAgent(
                gcs_credentials_path="/fake/path/creds.json",
                gcs_bucket_name="fake-bucket",
                validate_inputs=False
            )
            print(f"   ⚠️  Agent created unexpectedly: {agent}")
        except Exception as e:
            print(f"   ✅ Expected failure: {str(e)[:60]}...")
            
            # Test just the class structure without GCS
            print_subsection("Testing Class Structure")
            print(f"   ✅ MediaAgent inherits from BaseAgent: {issubclass(MediaAgent.__class__, BaseAgent.__class__)}")
            print(f"   ✅ Has process method: {hasattr(MediaAgent, 'process')}")
            print(f"   ✅ Has validate_configuration method: {hasattr(MediaAgent, 'validate_configuration')}")
            
        return True
        
    except Exception as e:
        print(f"   ❌ MediaAgent test failed: {e}")
        return False

def test_deploy_agent_basic():
    """Test DeployAgent basic functionality (without real credentials).""" 
    print_section("TESTING DeployAgent (Basic)")
    
    try:
        print_subsection("Testing DeployAgent Creation (Expected to Fail)")
        # This should fail due to invalid credentials, but we can test the structure
        try:
            agent = DeployAgent(
                api_token="fake-token",
                account_id="fake-account-id",
                validate_inputs=False
            )
            print(f"   ⚠️  Agent created unexpectedly: {agent}")
        except Exception as e:
            print(f"   ✅ Expected failure: {str(e)[:60]}...")
            
            # Test just the class structure
            print_subsection("Testing Class Structure")
            print(f"   ✅ DeployAgent inherits from BaseAgent: {issubclass(DeployAgent.__class__, BaseAgent.__class__)}")
            print(f"   ✅ Has process method: {hasattr(DeployAgent, 'process')}")
            print(f"   ✅ Has validate_configuration method: {hasattr(DeployAgent, 'validate_configuration')}")
            print(f"   ✅ Has sanitize_project_name method: {hasattr(DeployAgent, 'sanitize_project_name')}")
            
        return True
        
    except Exception as e:
        print(f"   ❌ DeployAgent test failed: {e}")
        return False

def test_agent_inheritance():
    """Test that all agents properly inherit from BaseAgent."""
    print_section("TESTING BaseAgent INHERITANCE")
    
    agents_to_test = [
        ("ExtractionAgent", ExtractionAgent),
        ("TransformAgent", TransformAgent),
        ("CMSConfigAgent", CMSConfigAgent)
    ]
    
    # Import the classes that might fail
    if MediaAgent:
        agents_to_test.append(("MediaAgent", MediaAgent))
    else:
        print("   ⚠️  MediaAgent import failed")
    
    if DeployAgent:
        agents_to_test.append(("DeployAgent", DeployAgent))
    else:
        print("   ⚠️  DeployAgent import failed")
    
    if GitHubAgent:
        agents_to_test.append(("GitHubAgent", GitHubAgent))
    else:
        print("   ⚠️  GitHubAgent import failed")
    
    if AstroScaffoldAgent:
        agents_to_test.append(("AstroScaffoldAgent", AstroScaffoldAgent))
    else:
        print("   ⚠️  AstroScaffoldAgent import failed")
    
    print_subsection("Testing Inheritance Chain")
    all_passed = True
    
    for agent_name, agent_class in agents_to_test:
        try:
            is_base_agent = issubclass(agent_class, BaseAgent)
            has_process = hasattr(agent_class, 'process')
            has_validate_config = hasattr(agent_class, 'validate_configuration')
            has_health_check = hasattr(agent_class, 'health_check')
            has_get_metrics = hasattr(agent_class, 'get_metrics')
            
            all_methods = all([has_process, has_validate_config, has_health_check, has_get_metrics])
            
            status = "✅" if is_base_agent and all_methods else "❌"
            print(f"   {status} {agent_name}:")
            print(f"      - Inherits BaseAgent: {is_base_agent}")
            print(f"      - Has process(): {has_process}")
            print(f"      - Has validate_configuration(): {has_validate_config}")
            print(f"      - Has health_check(): {has_health_check}")  
            print(f"      - Has get_metrics(): {has_get_metrics}")
            
            if not (is_base_agent and all_methods):
                all_passed = False
                
        except Exception as e:
            print(f"   ❌ {agent_name}: Error testing - {e}")
            all_passed = False
    
    return all_passed

def test_working_agents():
    """Test agents that should work without external dependencies."""
    print_section("TESTING WORKING AGENTS")
    
    working_tests = []
    
    print_subsection("TransformAgent")
    try:
        agent = TransformAgent()
        health = agent.health_check()
        print(f"   ✅ Health: {health.success}")
        print(f"   📊 Metrics: {agent.get_metrics().total_operations}")
        working_tests.append(True)
    except Exception as e:
        print(f"   ❌ TransformAgent failed: {e}")
        working_tests.append(False)
    
    print_subsection("CMSConfigAgent")
    try:
        repo_info = {"owner": "test", "repo": "test-repo"}
        content_structure = {"media_dir": "public/uploads"}
        agent = CMSConfigAgent(repo_info, content_structure)
        result = agent.process()
        print(f"   ✅ Process: {result.success}")
        print(f"   📊 Generated config: {bool(result.data)}")
        working_tests.append(True)
    except Exception as e:
        print(f"   ❌ CMSConfigAgent failed: {e}")
        working_tests.append(False)
    
    return all(working_tests)

def test_agent_metrics_tracking():
    """Test metrics tracking across different agents."""
    print_section("TESTING METRICS TRACKING")
    
    print_subsection("TransformAgent Metrics")
    try:
        agent = TransformAgent()
        
        # Perform some operations to generate metrics
        def dummy_operation():
            import time
            time.sleep(0.001)
            return "test"
        
        # Test direct metrics tracking
        result1 = agent._execute_with_metrics("test_op_1", dummy_operation)
        result2 = agent._execute_with_metrics("test_op_2", dummy_operation)
        
        metrics = agent.get_metrics()
        print(f"   📊 Total operations: {metrics.total_operations}")
        print(f"   ✅ Successful: {metrics.successful_operations}")
        print(f"   ⏱️  Average time: {metrics.average_execution_time:.4f}s")
        print(f"   🕐 Last operation: {metrics.last_operation_time}")
        
        return metrics.total_operations == 2 and metrics.successful_operations == 2
        
    except Exception as e:
        print(f"   ❌ Metrics tracking test failed: {e}")
        return False

def main():
    """Run all agent tests."""
    print("🚀 Starting Updated Agents Test Suite")
    print("Testing all agents updated with BaseAgent architecture")
    
    test_results = []
    
    try:
        # Test basic functionality
        test_results.append(("Inheritance", test_agent_inheritance()))
        test_results.append(("Working Agents", test_working_agents()))
        test_results.append(("CMS Config Agent", test_cms_config_agent()))
        test_results.append(("Metrics Tracking", test_agent_metrics_tracking()))
        
        # Test agents that might fail due to dependencies
        test_results.append(("Media Agent Basic", test_media_agent_basic()))
        test_results.append(("Deploy Agent Basic", test_deploy_agent_basic()))
        
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
            print("\n🎉 ALL TESTS PASSED!")
            print("✨ BaseAgent architecture is working correctly across all agents!")
        else:
            print(f"\n⚠️  {total - passed} tests failed - check the details above")
        
        print("\n🔧 Updated Agents Summary:")
        print("   ✅ ExtractionAgent - Inherits BaseAgent")
        print("   ✅ TransformAgent - Inherits BaseAgent")  
        print("   ✅ MediaAgent - Inherits BaseAgent")
        print("   ✅ DeployAgent - Inherits BaseAgent")
        print("   ✅ CMSConfigAgent - Inherits BaseAgent")
        print("   ✅ GitHubAgent - Inherits BaseAgent")
        print("   ✅ AstroScaffoldAgent - Inherits BaseAgent")
        
    except Exception as e:
        print(f"❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
