#!/usr/bin/env python3
"""
Backend Test Suite - ERP360 Gym Management System API Testing
Focus on testing the 3 API fixes and critical endpoints
"""

import requests
import json
import time
import os
from datetime import datetime, timezone, timedelta

# Configuration
BASE_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://gym-rbac-erp.preview.emergentagent.com')
API_BASE = f"{BASE_URL}/api"

# Test credentials
ADMIN_EMAIL = "admin@gym.com"
ADMIN_PASSWORD = "admin123"

class ERP360APITestRunner:
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
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def authenticate(self):
        """Authenticate as admin"""
        try:
            # Authenticate as admin
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
                self.log_result("Admin Authentication", False, f"Failed to authenticate admin: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    # ===================== PRIORITY 1: TEST THE 3 API FIXES =====================
    
    def test_lead_creation_with_json_body(self):
        """Test POST /api/sales/leads with JSON body - Fix #1"""
        print("\n=== Testing Lead Creation with JSON Body (FIX #1) ===")
        
        try:
            # Test 1: Create lead with JSON body
            lead_data = {
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane@test.com",
                "phone": "+27111222333",
                "source": "website"
            }
            
            response = requests.post(
                f"{API_BASE}/sales/leads",
                json=lead_data,
                headers=self.admin_headers
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                
                # Verify response structure (API returns {success: true, lead: {...}})
                if "success" not in data or "lead" not in data:
                    self.log_result("Lead Creation - Response Structure", False, "Missing 'success' or 'lead' field in response")
                    return False
                
                lead = data["lead"]
                
                # Verify lead was created with correct data
                if "id" not in lead:
                    self.log_result("Lead Creation - Lead ID", False, "Missing 'id' field in lead object")
                    return False
                
                # Verify all fields are present
                for field in ["first_name", "last_name", "email", "phone", "source"]:
                    if field not in lead:
                        self.log_result("Lead Creation - Response Fields", False, f"Missing field: {field}")
                        return False
                
                # Verify data matches input
                if lead["first_name"] != lead_data["first_name"]:
                    self.log_result("Lead Creation - Data Mismatch", False, f"first_name mismatch: {lead['first_name']} vs {lead_data['first_name']}")
                    return False
                
                if lead["email"] != lead_data["email"]:
                    self.log_result("Lead Creation - Data Mismatch", False, f"email mismatch: {lead['email']} vs {lead_data['email']}")
                    return False
                
                # CRITICAL: Verify referred_by_member_id bug is fixed (should not be required)
                # The bug was that referred_by_member_id was required but shouldn't be
                # If we can create a lead without it, the bug is fixed
                # Verify referred_by_member_id is null (not required)
                if "referred_by_member_id" in lead and lead["referred_by_member_id"] is None:
                    self.log_result("Lead Creation with JSON Body", True, f"Lead created successfully with ID: {lead['id']}, referred_by_member_id bug is FIXED (field is optional and null)")
                    return True
                else:
                    self.log_result("Lead Creation with JSON Body", True, f"Lead created successfully with ID: {lead['id']}")
                    return True
                
            else:
                error_msg = f"Failed with status {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f": {error_detail}"
                except:
                    error_msg += f": {response.text}"
                self.log_result("Lead Creation with JSON Body", False, error_msg)
                return False
            
        except Exception as e:
            self.log_result("Lead Creation with JSON Body", False, f"Error: {str(e)}")
            return False
    
    def test_payment_analytics_endpoint(self):
        """Test GET /api/reports/payment-analytics - Fix #2"""
        print("\n=== Testing Payment Analytics Endpoint (FIX #2) ===")
        
        try:
            # Test with period_months parameter
            response = requests.get(
                f"{API_BASE}/reports/payment-analytics",
                params={"period_months": 12},
                headers=self.admin_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["payment_methods", "revenue_trends", "summary"]
                
                for field in required_fields:
                    if field not in data:
                        self.log_result("Payment Analytics - Structure", False, f"Missing field: {field}")
                        return False
                
                # Verify payment_methods structure
                payment_methods = data["payment_methods"]
                if not isinstance(payment_methods, list):
                    self.log_result("Payment Analytics - Payment Methods", False, "payment_methods should be array")
                    return False
                
                # Verify revenue_trends structure
                revenue_trends = data["revenue_trends"]
                if not isinstance(revenue_trends, list):
                    self.log_result("Payment Analytics - Revenue Trends", False, "revenue_trends should be array")
                    return False
                
                # Verify summary structure
                summary = data["summary"]
                summary_fields = ["total_revenue", "total_payments", "avg_payment_amount"]
                for field in summary_fields:
                    if field not in summary:
                        self.log_result("Payment Analytics - Summary", False, f"Missing summary field: {field}")
                        return False
                
                self.log_result("Payment Analytics Endpoint", True, f"Total revenue: R{summary['total_revenue']:.2f}, Total payments: {summary['total_payments']}")
                return True
                
            else:
                error_msg = f"Failed with status {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f": {error_detail}"
                except:
                    error_msg += f": {response.text}"
                self.log_result("Payment Analytics Endpoint", False, error_msg)
                return False
            
        except Exception as e:
            self.log_result("Payment Analytics Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_retention_report_endpoint(self):
        """Test GET /api/reports/retention - Fix #3"""
        print("\n=== Testing Retention Report Endpoint (FIX #3) ===")
        
        try:
            # Test with period_months parameter
            response = requests.get(
                f"{API_BASE}/reports/retention",
                params={"period_months": 12},
                headers=self.admin_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["retention_data", "churn_rate", "cohort_analysis"]
                
                for field in required_fields:
                    if field not in data:
                        self.log_result("Retention Report - Structure", False, f"Missing field: {field}")
                        return False
                
                # Verify retention_data structure
                retention_data = data["retention_data"]
                if not isinstance(retention_data, list):
                    self.log_result("Retention Report - Retention Data", False, "retention_data should be array")
                    return False
                
                # Verify churn_rate is a number
                churn_rate = data["churn_rate"]
                if not isinstance(churn_rate, (int, float)):
                    self.log_result("Retention Report - Churn Rate", False, f"churn_rate should be number, got {type(churn_rate)}")
                    return False
                
                # Verify cohort_analysis structure
                cohort_analysis = data["cohort_analysis"]
                if not isinstance(cohort_analysis, list):
                    self.log_result("Retention Report - Cohort Analysis", False, "cohort_analysis should be array")
                    return False
                
                self.log_result("Retention Report Endpoint", True, f"Churn rate: {churn_rate}%, Retention data points: {len(retention_data)}, Cohorts: {len(cohort_analysis)}")
                return True
                
            else:
                error_msg = f"Failed with status {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f": {error_detail}"
                except:
                    error_msg += f": {response.text}"
                self.log_result("Retention Report Endpoint", False, error_msg)
                return False
            
        except Exception as e:
            self.log_result("Retention Report Endpoint", False, f"Error: {str(e)}")
            return False
    
    # ===================== PRIORITY 2: VERIFY CRITICAL ENDPOINTS =====================
    
    def test_permission_matrix_endpoint(self):
        """Test GET /api/rbac/permission-matrix - Should return all 15 roles"""
        print("\n=== Testing Permission Matrix Endpoint ===")
        
        try:
            response = requests.get(
                f"{API_BASE}/rbac/permission-matrix",
                headers=self.admin_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                if "matrix" not in data:
                    self.log_result("Permission Matrix - Structure", False, "Missing 'matrix' field")
                    return False
                
                matrix = data["matrix"]
                if not isinstance(matrix, list):
                    self.log_result("Permission Matrix - Matrix Type", False, "matrix should be array")
                    return False
                
                # Verify we have all 15 roles
                if len(matrix) != 15:
                    self.log_result("Permission Matrix - Role Count", False, f"Expected 15 roles, got {len(matrix)}")
                    return False
                
                # Verify each role has required fields
                for role in matrix:
                    required_fields = ["role", "role_display_name", "permissions", "is_custom", "is_default"]
                    for field in required_fields:
                        if field not in role:
                            self.log_result("Permission Matrix - Role Fields", False, f"Missing field: {field} in role")
                            return False
                
                self.log_result("Permission Matrix Endpoint", True, f"Retrieved all 15 roles successfully")
                return True
                
            else:
                error_msg = f"Failed with status {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f": {error_detail}"
                except:
                    error_msg += f": {response.text}"
                self.log_result("Permission Matrix Endpoint", False, error_msg)
                return False
            
        except Exception as e:
            self.log_result("Permission Matrix Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_auth_me_endpoint(self):
        """Test GET /api/auth/me - Should return current user info"""
        print("\n=== Testing Auth Me Endpoint ===")
        
        try:
            response = requests.get(
                f"{API_BASE}/auth/me",
                headers=self.admin_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["id", "email", "full_name", "role"]
                
                for field in required_fields:
                    if field not in data:
                        self.log_result("Auth Me - Structure", False, f"Missing field: {field}")
                        return False
                
                # Verify email matches admin email
                if data["email"] != ADMIN_EMAIL:
                    self.log_result("Auth Me - Email Mismatch", False, f"Expected {ADMIN_EMAIL}, got {data['email']}")
                    return False
                
                self.log_result("Auth Me Endpoint", True, f"User: {data['email']}, Role: {data['role']}")
                return True
                
            else:
                error_msg = f"Failed with status {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f": {error_detail}"
                except:
                    error_msg += f": {response.text}"
                self.log_result("Auth Me Endpoint", False, error_msg)
                return False
            
        except Exception as e:
            self.log_result("Auth Me Endpoint", False, f"Error: {str(e)}")
            return False
    
    def test_members_list_endpoint(self):
        """Test GET /api/members - Should return member list"""
        print("\n=== Testing Members List Endpoint ===")
        
        try:
            response = requests.get(
                f"{API_BASE}/members",
                headers=self.admin_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response is an array
                if not isinstance(data, list):
                    self.log_result("Members List - Type", False, "Response should be array")
                    return False
                
                # If we have members, verify structure
                if len(data) > 0:
                    member = data[0]
                    required_fields = ["id", "first_name", "last_name", "email", "phone", "membership_type_id"]
                    
                    for field in required_fields:
                        if field not in member:
                            self.log_result("Members List - Member Fields", False, f"Missing field: {field}")
                            return False
                
                self.log_result("Members List Endpoint", True, f"Retrieved {len(data)} members")
                return True
                
            else:
                error_msg = f"Failed with status {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f": {error_detail}"
                except:
                    error_msg += f": {response.text}"
                self.log_result("Members List Endpoint", False, error_msg)
                return False
            
        except Exception as e:
            self.log_result("Members List Endpoint", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all ERP360 API tests"""
        print("🚀 Starting ERP360 Gym Management System API Tests...")
        print(f"📍 Testing against: {BASE_URL}")
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return False
        
        # Run PRIORITY 1 tests (the 3 fixes)
        print("\n" + "="*80)
        print("PRIORITY 1: Testing the 3 API Fixes")
        print("="*80)
        
        priority1_tests = [
            self.test_lead_creation_with_json_body,
            self.test_payment_analytics_endpoint,
            self.test_retention_report_endpoint
        ]
        
        priority1_passed = 0
        priority1_failed = 0
        
        for test in priority1_tests:
            try:
                if test():
                    priority1_passed += 1
                else:
                    priority1_failed += 1
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {str(e)}")
                priority1_failed += 1
        
        # Run PRIORITY 2 tests (critical endpoints)
        print("\n" + "="*80)
        print("PRIORITY 2: Verifying Critical Endpoints")
        print("="*80)
        
        priority2_tests = [
            self.test_permission_matrix_endpoint,
            self.test_auth_me_endpoint,
            self.test_members_list_endpoint
        ]
        
        priority2_passed = 0
        priority2_failed = 0
        
        for test in priority2_tests:
            try:
                if test():
                    priority2_passed += 1
                else:
                    priority2_failed += 1
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {str(e)}")
                priority2_failed += 1
        
        # Print summary
        print("\n" + "="*80)
        print("📊 TEST SUMMARY")
        print("="*80)
        print(f"\nPRIORITY 1 (3 API Fixes):")
        print(f"  ✅ Passed: {priority1_passed}/3")
        print(f"  ❌ Failed: {priority1_failed}/3")
        
        print(f"\nPRIORITY 2 (Critical Endpoints):")
        print(f"  ✅ Passed: {priority2_passed}/3")
        print(f"  ❌ Failed: {priority2_failed}/3")
        
        total_passed = priority1_passed + priority2_passed
        total_failed = priority1_failed + priority2_failed
        total_tests = total_passed + total_failed
        
        print(f"\nOVERALL:")
        print(f"  ✅ Total Passed: {total_passed}/{total_tests}")
        print(f"  ❌ Total Failed: {total_failed}/{total_tests}")
        print(f"  📈 Success Rate: {(total_passed/total_tests*100):.1f}%")
        
        # Print detailed results
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        return total_failed == 0


def main():
    """Main test execution"""
    runner = ERP360APITestRunner()
    success = runner.run_all_tests()
    
    if success:
        print("\n🎉 All ERP360 API tests passed!")
        exit(0)
    else:
        print("\n💥 Some tests failed!")
        exit(1)


if __name__ == "__main__":
    main()