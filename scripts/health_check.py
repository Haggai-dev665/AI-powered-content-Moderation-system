"""
Health Check Script for AI Content Moderation System
Verifies that all services are running and responding correctly
"""

import requests
import time
import logging
import sys
from typing import Dict, List
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HealthChecker:
    """Health checker for all services"""
    
    def __init__(self):
        self.services = {
            "gateway": "http://localhost:8000",
            "text-moderation": "http://localhost:8001", 
            "image-moderation": "http://localhost:8002"
        }
        self.timeout = 5
        
    def check_service_health(self, service_name: str, base_url: str) -> Dict:
        """Check health of a single service"""
        health_url = f"{base_url}/health"
        
        try:
            logger.info(f"Checking {service_name} at {health_url}")
            response = requests.get(health_url, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✓ {service_name} is healthy: {data.get('status', 'unknown')}")
                return {
                    "service": service_name,
                    "status": "healthy",
                    "response": data,
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                logger.error(f"✗ {service_name} returned status {response.status_code}")
                return {
                    "service": service_name,
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}",
                    "response_time": response.elapsed.total_seconds()
                }
                
        except requests.exceptions.ConnectionError:
            logger.error(f"✗ {service_name} is not reachable (connection refused)")
            return {
                "service": service_name,
                "status": "unreachable",
                "error": "Connection refused"
            }
        except requests.exceptions.Timeout:
            logger.error(f"✗ {service_name} timed out")
            return {
                "service": service_name,
                "status": "timeout",
                "error": "Request timeout"
            }
        except Exception as e:
            logger.error(f"✗ {service_name} check failed: {e}")
            return {
                "service": service_name,
                "status": "error",
                "error": str(e)
            }
    
    def test_text_moderation(self) -> Dict:
        """Test text moderation functionality"""
        url = f"{self.services['text-moderation']}/moderate"
        test_data = {"text": "This is a test message"}
        
        try:
            logger.info("Testing text moderation...")
            response = requests.post(url, json=test_data, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✓ Text moderation test passed")
                return {
                    "test": "text_moderation",
                    "status": "passed",
                    "response": data
                }
            else:
                logger.error(f"✗ Text moderation test failed: HTTP {response.status_code}")
                return {
                    "test": "text_moderation",
                    "status": "failed",
                    "error": f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"✗ Text moderation test error: {e}")
            return {
                "test": "text_moderation",
                "status": "error",
                "error": str(e)
            }
    
    def test_gateway_routing(self) -> Dict:
        """Test gateway routing functionality"""
        url = f"{self.services['gateway']}/text/moderate"
        test_data = {"text": "This is a test message"}
        
        try:
            logger.info("Testing gateway routing...")
            response = requests.post(url, json=test_data, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✓ Gateway routing test passed")
                return {
                    "test": "gateway_routing",
                    "status": "passed",
                    "response": data
                }
            else:
                logger.error(f"✗ Gateway routing test failed: HTTP {response.status_code}")
                return {
                    "test": "gateway_routing",
                    "status": "failed",
                    "error": f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"✗ Gateway routing test error: {e}")
            return {
                "test": "gateway_routing",
                "status": "error",
                "error": str(e)
            }
    
    def run_comprehensive_check(self) -> Dict:
        """Run comprehensive health check"""
        logger.info("🏥 Starting comprehensive health check")
        logger.info("=" * 50)
        
        results = {
            "timestamp": time.time(),
            "services": {},
            "tests": {},
            "overall_status": "unknown"
        }
        
        # Check all services
        healthy_services = 0
        for service_name, base_url in self.services.items():
            result = self.check_service_health(service_name, base_url)
            results["services"][service_name] = result
            if result["status"] == "healthy":
                healthy_services += 1
        
        # Run functional tests if services are healthy
        if healthy_services > 0:
            logger.info("\n🧪 Running functional tests...")
            
            # Test text moderation
            if results["services"]["text-moderation"]["status"] == "healthy":
                results["tests"]["text_moderation"] = self.test_text_moderation()
            
            # Test gateway routing
            if results["services"]["gateway"]["status"] == "healthy":
                results["tests"]["gateway_routing"] = self.test_gateway_routing()
        
        # Determine overall status
        if healthy_services == len(self.services):
            results["overall_status"] = "healthy"
        elif healthy_services > 0:
            results["overall_status"] = "partial"
        else:
            results["overall_status"] = "unhealthy"
        
        return results
    
    def print_summary(self, results: Dict):
        """Print health check summary"""
        logger.info("\n" + "=" * 50)
        logger.info("📊 HEALTH CHECK SUMMARY")
        logger.info("=" * 50)
        
        # Service status
        logger.info("🔧 Services:")
        for service_name, result in results["services"].items():
            status_icon = "✓" if result["status"] == "healthy" else "✗"
            response_time = result.get("response_time", "N/A")
            logger.info(f"  {status_icon} {service_name}: {result['status']} ({response_time}s)")
        
        # Test results
        if results["tests"]:
            logger.info("\n🧪 Tests:")
            for test_name, result in results["tests"].items():
                status_icon = "✓" if result["status"] == "passed" else "✗"
                logger.info(f"  {status_icon} {test_name}: {result['status']}")
        
        # Overall status
        status_icons = {
            "healthy": "🟢",
            "partial": "🟡", 
            "unhealthy": "🔴"
        }
        
        overall_status = results["overall_status"]
        icon = status_icons.get(overall_status, "⚪")
        
        logger.info(f"\n{icon} Overall Status: {overall_status.upper()}")
        
        if overall_status == "healthy":
            logger.info("🎉 All systems operational!")
        elif overall_status == "partial":
            logger.info("⚠️  Some services are down")
        else:
            logger.info("🚨 System is not operational")

def main():
    """Main function"""
    checker = HealthChecker()
    results = checker.run_comprehensive_check()
    checker.print_summary(results)
    
    # Save results to file
    with open("health_check_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Exit with appropriate code
    if results["overall_status"] == "healthy":
        sys.exit(0)
    elif results["overall_status"] == "partial":
        sys.exit(1)
    else:
        sys.exit(2)

if __name__ == "__main__":
    main()
