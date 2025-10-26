#!/usr/bin/env python3
"""
Backend Test Suite - Testing 3 API Fixes for ERP360 Gym Management System
1. Lead Creation with JSON Body (POST /api/sales/leads)
2. Payment Analytics Endpoint (GET /api/reports/payment-analytics)
3. Retention Report Alias (GET /api/reports/retention)
"""

import requests
import json
import os
from datetime import datetime, timezone

# Configuration
BASE_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://gym-rbac-erp.preview.emergentagent.com')
API_BASE = f"{BASE_URL}/api"

# Test credentials
ADMIN_EMAIL = "admin@gym.com"
ADMIN_PASSWORD = "admin123"

class APIFixesTestRunner:
    def __init__(self):
        self.admin_token = None
        self.admin_headers = {}
        self.test_results = []
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        print(f"   {message}")
        if details and not success:
            print(f"   Details: {json.dumps(details, indent=2)}")
    
    def authenticate(self):
        """Authenticate as admin"""
        try:
            print("\n🔐 Authenticating as admin...")
            response = requests.post(f"{API_BASE}/auth/login", json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data["access_token"]
                self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
                self.log_result("Admin Authentication", True, "Successfully authenticated as admin")
                return True
            else:
                self.log_result("Admin Authentication", False, f"Failed to authenticate: {response.status_code}", {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    # ===================== TEST 1: LEAD CREATION WITH JSON BODY =====================
    
    def test_lead_creation_json_body(self):
        """Test POST /api/sales/leads with JSON body instead of query parameters"""
        print("\n" + "="*80)
        print("TEST 1: Lead Creation with JSON Body")
        print("="*80)
        
        try:
            # Prepare test data
            lead_data = {
                "first_name": "Test",
                "last_name": "Lead",
                "email": "test.lead@example.com",
                "phone": "+27123456789",
                "source": "website"
            }
            
            print(f"\n📤 Sending POST request to {API_BASE}/sales/leads")
            print(f"   Request body: {json.dumps(lead_data, indent=2)}")
            
            # Make the request
            response = requests.post(
                f"{API_BASE}/sales/leads",
                headers={**self.admin_headers, "Content-Type": "application/json"},
                json=lead_data
            )
            
            print(f"   Response status: {response.status_code}")
            
            # Check response
            if response.status_code in [200, 201]:
                data = response.json()
                print(f"   Response data: {json.dumps(data, indent=2)}")
                
                # Verify response structure
                if "success" in data and data["success"]:
                    if "lead" in data:
                        lead = data["lead"]
                        
                        # Verify all fields are present
                        required_fields = ["id", "first_name", "last_name", "email", "phone", "source"]
                        missing_fields = [f for f in required_fields if f not in lead]
                        
                        if missing_fields:
                            self.log_result(
                                "Lead Creation - JSON Body",
                                False,
                                f"Missing fields in response: {missing_fields}",
                                {"response": data}
                            )
                            return False
                        
                        # Verify field values match
                        if (lead["first_name"] == lead_data["first_name"] and
                            lead["last_name"] == lead_data["last_name"] and
                            lead["email"] == lead_data["email"] and
                            lead["phone"] == lead_data["phone"] and
                            lead["source"] == lead_data["source"]):
                            
                            self.log_result(
                                "Lead Creation - JSON Body",
                                True,
                                f"✅ Lead created successfully with ID: {lead['id']}",
                                {"lead_id": lead["id"], "name": f"{lead['first_name']} {lead['last_name']}"}
                            )
                            return True
                        else:
                            self.log_result(
                                "Lead Creation - JSON Body",
                                False,
                                "Field values don't match request data",
                                {"expected": lead_data, "actual": lead}
                            )
                            return False
                    else:
                        self.log_result(
                            "Lead Creation - JSON Body",
                            False,
                            "Response missing 'lead' field",
                            {"response": data}
                        )
                        return False
                else:
                    self.log_result(
                        "Lead Creation - JSON Body",
                        False,
                        "Response indicates failure",
                        {"response": data}
                    )
                    return False
            else:
                self.log_result(
                    "Lead Creation - JSON Body",
                    False,
                    f"Unexpected status code: {response.status_code}",
                    {"status": response.status_code, "response": response.text}
                )
                return False
            
        except Exception as e:
            self.log_result(
                "Lead Creation - JSON Body",
                False,
                f"Exception occurred: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    # ===================== TEST 2: PAYMENT ANALYTICS ENDPOINT =====================
    
    def test_payment_analytics_endpoint(self):
        """Test GET /api/reports/payment-analytics endpoint"""
        print("\n" + "="*80)
        print("TEST 2: Payment Analytics Endpoint")
        print("="*80)
        
        try:
            # Test with default parameters
            print(f"\n📤 Sending GET request to {API_BASE}/reports/payment-analytics")
            
            response = requests.get(
                f"{API_BASE}/reports/payment-analytics",
                headers=self.admin_headers,
                params={"period_months": 12}
            )
            
            print(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Response data keys: {list(data.keys())}")
                
                # Verify response structure
                expected_sections = ["payment_methods", "revenue_trends", "success_rates"]
                missing_sections = [s for s in expected_sections if s not in data]
                
                if missing_sections:
                    self.log_result(
                        "Payment Analytics Endpoint",
                        False,
                        f"Missing sections in response: {missing_sections}",
                        {"response_keys": list(data.keys()), "expected": expected_sections}
                    )
                    return False
                
                # Verify payment_methods structure
                if "payment_methods" in data:
                    payment_methods = data["payment_methods"]
                    if isinstance(payment_methods, list):
                        print(f"   ✓ Payment methods: {len(payment_methods)} methods found")
                    else:
                        self.log_result(
                            "Payment Analytics Endpoint",
                            False,
                            "payment_methods should be an array",
                            {"type": type(payment_methods).__name__}
                        )
                        return False
                
                # Verify revenue_trends structure
                if "revenue_trends" in data:
                    revenue_trends = data["revenue_trends"]
                    if isinstance(revenue_trends, list):
                        print(f"   ✓ Revenue trends: {len(revenue_trends)} data points")
                    else:
                        self.log_result(
                            "Payment Analytics Endpoint",
                            False,
                            "revenue_trends should be an array",
                            {"type": type(revenue_trends).__name__}
                        )
                        return False
                
                # Verify success_rates structure
                if "success_rates" in data:
                    success_rates = data["success_rates"]
                    if isinstance(success_rates, dict):
                        print(f"   ✓ Success rates: {json.dumps(success_rates, indent=2)}")
                    else:
                        self.log_result(
                            "Payment Analytics Endpoint",
                            False,
                            "success_rates should be an object",
                            {"type": type(success_rates).__name__}
                        )
                        return False
                
                self.log_result(
                    "Payment Analytics Endpoint",
                    True,
                    "✅ Payment analytics endpoint working correctly",
                    {
                        "payment_methods_count": len(data.get("payment_methods", [])),
                        "revenue_trends_count": len(data.get("revenue_trends", [])),
                        "success_rates": data.get("success_rates", {})
                    }
                )
                return True
                
            else:
                self.log_result(
                    "Payment Analytics Endpoint",
                    False,
                    f"Unexpected status code: {response.status_code}",
                    {"status": response.status_code, "response": response.text}
                )
                return False
            
        except Exception as e:
            self.log_result(
                "Payment Analytics Endpoint",
                False,
                f"Exception occurred: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    # ===================== TEST 3: RETENTION REPORT ALIAS =====================
    
    def test_retention_report_alias(self):
        """Test GET /api/reports/retention endpoint (alias for retention-dashboard)"""
        print("\n" + "="*80)
        print("TEST 3: Retention Report Alias")
        print("="*80)
        
        try:
            # Test the alias endpoint
            print(f"\n📤 Sending GET request to {API_BASE}/reports/retention")
            
            response = requests.get(
                f"{API_BASE}/reports/retention",
                headers=self.admin_headers,
                params={"period_months": 12}
            )
            
            print(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Response data keys: {list(data.keys())}")
                
                # Verify response structure (should match retention-dashboard)
                expected_sections = ["period", "summary", "retention_by_cohort", "retention_trend"]
                missing_sections = [s for s in expected_sections if s not in data]
                
                if missing_sections:
                    self.log_result(
                        "Retention Report Alias",
                        False,
                        f"Missing sections in response: {missing_sections}",
                        {"response_keys": list(data.keys()), "expected": expected_sections}
                    )
                    return False
                
                # Verify period structure
                if "period" in data:
                    period = data["period"]
                    if "start_date" in period and "end_date" in period and "months" in period:
                        print(f"   ✓ Period: {period['months']} months")
                    else:
                        self.log_result(
                            "Retention Report Alias",
                            False,
                            "Period structure incomplete",
                            {"period": period}
                        )
                        return False
                
                # Verify summary structure
                if "summary" in data:
                    summary = data["summary"]
                    required_summary_fields = ["churn_rate", "retention_rate", "total_members", "active_members"]
                    missing_summary_fields = [f for f in required_summary_fields if f not in summary]
                    
                    if missing_summary_fields:
                        self.log_result(
                            "Retention Report Alias",
                            False,
                            f"Missing summary fields: {missing_summary_fields}",
                            {"summary": summary}
                        )
                        return False
                    
                    print(f"   ✓ Summary: Churn rate: {summary['churn_rate']}%, Retention rate: {summary['retention_rate']}%")
                
                # Verify retention_by_cohort structure
                if "retention_by_cohort" in data:
                    cohorts = data["retention_by_cohort"]
                    if isinstance(cohorts, list):
                        print(f"   ✓ Cohort analysis: {len(cohorts)} cohorts")
                    else:
                        self.log_result(
                            "Retention Report Alias",
                            False,
                            "retention_by_cohort should be an array",
                            {"type": type(cohorts).__name__}
                        )
                        return False
                
                # Verify retention_trend structure
                if "retention_trend" in data:
                    trends = data["retention_trend"]
                    if isinstance(trends, list):
                        print(f"   ✓ Retention trends: {len(trends)} data points")
                    else:
                        self.log_result(
                            "Retention Report Alias",
                            False,
                            "retention_trend should be an array",
                            {"type": type(trends).__name__}
                        )
                        return False
                
                self.log_result(
                    "Retention Report Alias",
                    True,
                    "✅ Retention report alias working correctly",
                    {
                        "churn_rate": data["summary"]["churn_rate"],
                        "retention_rate": data["summary"]["retention_rate"],
                        "cohorts_count": len(data.get("retention_by_cohort", [])),
                        "trends_count": len(data.get("retention_trend", []))
                    }
                )
                return True
                
            else:
                self.log_result(
                    "Retention Report Alias",
                    False,
                    f"Unexpected status code: {response.status_code}",
                    {"status": response.status_code, "response": response.text}
                )
                return False
            
        except Exception as e:
            self.log_result(
                "Retention Report Alias",
                False,
                f"Exception occurred: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    def run_all_tests(self):
        """Run all API fix tests"""
        print("\n" + "="*80)
        print("🚀 Starting API Fixes Test Suite")
        print("="*80)
        print(f"📍 Testing against: {BASE_URL}")
        print(f"🔗 API Base: {API_BASE}")
        
        # Authenticate first
        if not self.authenticate():
            print("\n❌ Authentication failed - cannot proceed with tests")
            return False
        
        # Run all tests
        tests = [
            self.test_lead_creation_json_body,
            self.test_payment_analytics_endpoint,
            self.test_retention_report_alias
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"\n❌ Test {test.__name__} crashed: {str(e)}")
                failed += 1
        
        # Print summary
        print("\n" + "="*80)
        print("📊 TEST SUMMARY")
        print("="*80)
        print(f"✅ Passed: {passed}/3")
        print(f"❌ Failed: {failed}/3")
        print(f"📈 Success Rate: {(passed/3*100):.1f}%")
        
        # Print detailed results
        print(f"\n📋 DETAILED RESULTS:")
        print("-"*80)
        for result in self.test_results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{status}: {result['test']}")
            print(f"   {result['message']}")
            if result.get("details") and not result["success"]:
                print(f"   Details: {json.dumps(result['details'], indent=2)}")
        
        return failed == 0


def main():
    """Main test execution"""
    runner = APIFixesTestRunner()
    success = runner.run_all_tests()
    
    if success:
        print("\n🎉 All API fix tests passed!")
        exit(0)
    else:
        print("\n💥 Some tests failed!")
        exit(1)


if __name__ == "__main__":
    main()
