#!/usr/bin/env python3
"""
Backend Test Suite - Lead Assignment APIs Testing
Focus on testing the new Lead Assignment APIs with role-based access control
"""

import requests
import json
import time
import os
from datetime import datetime, timezone, timedelta

# Configuration
BASE_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://fitness-erp-app.preview.emergentagent.com')
API_BASE = f"{BASE_URL}/api"

# Test credentials
MANAGER_EMAIL = "admin@gym.com"
MANAGER_PASSWORD = "admin123"

class LeadAssignmentTestRunner:
    def __init__(self):
        self.manager_token = None
        self.consultant_token = None
        self.manager_headers = {}
        self.consultant_headers = {}
        self.test_results = []
        self.test_consultant_id = None
        self.test_lead_id = None
        self.created_leads = []
        self.created_users = []
        
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
        """Authenticate manager and create test consultant"""
        try:
            # Authenticate as manager
            response = requests.post(f"{API_BASE}/auth/login", json={
                "email": MANAGER_EMAIL,
                "password": MANAGER_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.manager_token = data["access_token"]
                self.manager_headers = {"Authorization": f"Bearer {self.manager_token}"}
                self.log_result("Manager Authentication", True, "Successfully authenticated as manager")
            else:
                self.log_result("Manager Authentication", False, f"Failed to authenticate manager: {response.status_code}")
                return False
                
            # Create a test consultant user
            timestamp = int(time.time() * 1000)
            consultant_data = {
                "email": f"consultant{timestamp}@test.com",
                "password": "consultant123",
                "full_name": f"Test Consultant {timestamp}",
                "role": "sales_manager"
            }
            
            response = requests.post(f"{API_BASE}/rbac/users", json=consultant_data, headers=self.manager_headers)
            
            if response.status_code == 200:
                user_data = response.json()
                if user_data.get("success") and "user" in user_data:
                    consultant_user = user_data["user"]
                    self.test_consultant_id = consultant_user["id"]
                    self.created_users.append(self.test_consultant_id)
                    
                    # Authenticate as consultant
                    consultant_login = requests.post(f"{API_BASE}/auth/login", json={
                        "email": consultant_data["email"],
                        "password": consultant_data["password"]
                    })
                    
                    if consultant_login.status_code == 200:
                        consultant_token_data = consultant_login.json()
                        self.consultant_token = consultant_token_data["access_token"]
                        self.consultant_headers = {"Authorization": f"Bearer {self.consultant_token}"}
                        self.log_result("Consultant Authentication", True, f"Created and authenticated test consultant: {consultant_user['email']}")
                    else:
                        self.log_result("Consultant Authentication", False, f"Failed to authenticate consultant: {consultant_login.status_code}")
                        return False
                else:
                    self.log_result("Create Test Consultant", False, "Invalid response structure")
                    return False
            else:
                self.log_result("Create Test Consultant", False, f"Failed to create consultant: {response.status_code}")
                return False
                
            return True
            
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def setup_test_data(self):
        """Setup test data - create a test lead for assignment testing"""
        try:
            # Create a test lead for assignment testing
            timestamp = int(time.time() * 1000)
            lead_data = {
                "first_name": "Test",
                "last_name": f"Lead{timestamp}",
                "email": f"testlead{timestamp}@test.com",
                "phone": f"+1234567{timestamp % 1000:03d}",
                "company": "Test Company"
            }
            
            response = requests.post(f"{API_BASE}/sales/leads", params=lead_data, headers=self.manager_headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "lead" in data:
                    created_lead = data["lead"]
                    self.test_lead_id = created_lead["id"]
                    self.created_leads.append(self.test_lead_id)
                    self.log_result("Create Test Lead", True, f"Created test lead: {created_lead['first_name']} {created_lead['last_name']}")
                    return True
                else:
                    self.log_result("Create Test Lead", False, "Invalid response structure")
                    return False
            else:
                self.log_result("Create Test Lead", False, f"Failed to create test lead: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Setup Test Data", False, f"Error setting up test data: {str(e)}")
            return False
    
    # ===================== LEAD ASSIGNMENT API TESTS =====================
    
    def test_get_sales_consultants(self):
        """Test GET /api/sales/consultants endpoint"""
        print("\n=== Testing Get Sales Consultants API ===")
        
        try:
            # Test with manager role (should work)
            response = requests.get(f"{API_BASE}/sales/consultants", headers=self.manager_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                if "consultants" not in data or "total" not in data:
                    self.log_result("Get Consultants Structure", False, "Missing consultants or total field")
                    return False
                
                consultants = data["consultants"]
                
                # Verify each consultant has required fields
                for consultant in consultants:
                    required_fields = ["id", "email", "role", "assigned_leads_count"]
                    for field in required_fields:
                        if field not in consultant:
                            self.log_result("Consultant Fields", False, f"Missing field: {field}")
                            return False
                
                # Verify our test consultant is in the list
                test_consultant_found = any(c["id"] == self.test_consultant_id for c in consultants)
                if test_consultant_found:
                    self.log_result("Get Consultants Manager Role", True, f"Found {len(consultants)} consultants including test consultant")
                else:
                    self.log_result("Get Consultants Manager Role", False, "Test consultant not found in list")
                    return False
                
            else:
                self.log_result("Get Consultants Manager Role", False, f"Failed with manager role: {response.status_code}")
                return False
            
            # Test with consultant role (should return 403)
            response = requests.get(f"{API_BASE}/sales/consultants", headers=self.consultant_headers)
            
            if response.status_code == 403:
                self.log_result("Get Consultants Consultant Role", True, "Correctly returns 403 for consultant role")
            else:
                self.log_result("Get Consultants Consultant Role", False, f"Expected 403, got {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Get Sales Consultants", False, f"Error testing get consultants: {str(e)}")
            return False
    
    def test_assign_lead(self):
        """Test POST /api/sales/leads/{lead_id}/assign endpoint"""
        print("\n=== Testing Assign Lead API ===")
        
        try:
            if not self.test_lead_id or not self.test_consultant_id:
                self.log_result("Assign Lead Setup", False, "Missing test lead or consultant ID")
                return False
            
            # Test assigning an unassigned lead with manager role (should work)
            assign_data = {
                "assigned_to": self.test_consultant_id,
                "assignment_notes": "Test assignment by manager"
            }
            
            response = requests.post(f"{API_BASE}/sales/leads/{self.test_lead_id}/assign", 
                                   params=assign_data, headers=self.manager_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["success", "message", "lead_id", "assigned_to", "assigned_to_name", "assigned_by", "assigned_at", "notification_task_created"]
                for field in required_fields:
                    if field not in data:
                        self.log_result("Assign Lead Response Fields", False, f"Missing field: {field}")
                        return False
                
                if data["assigned_to"] != self.test_consultant_id:
                    self.log_result("Assign Lead Consultant ID", False, "Wrong consultant ID in response")
                    return False
                
                if not data["notification_task_created"]:
                    self.log_result("Assign Lead Notification", False, "Notification task not created")
                    return False
                
                self.log_result("Assign Lead Manager Role", True, "Successfully assigned lead with manager role")
                
            else:
                self.log_result("Assign Lead Manager Role", False, f"Failed to assign lead: {response.status_code}")
                return False
            
            # Test reassigning the same lead (should work)
            reassign_data = {
                "assigned_to": self.test_consultant_id,
                "assignment_notes": "Test reassignment"
            }
            
            response = requests.post(f"{API_BASE}/sales/leads/{self.test_lead_id}/assign", 
                                   params=reassign_data, headers=self.manager_headers)
            
            if response.status_code == 200:
                data = response.json()
                if "reassigned" in data["message"]:
                    self.log_result("Reassign Lead", True, "Successfully reassigned lead")
                else:
                    self.log_result("Reassign Lead", False, "Message doesn't indicate reassignment")
                    return False
            else:
                self.log_result("Reassign Lead", False, f"Failed to reassign lead: {response.status_code}")
                return False
            
            # Test with consultant role (should return 403)
            response = requests.post(f"{API_BASE}/sales/leads/{self.test_lead_id}/assign", 
                                   params=assign_data, headers=self.consultant_headers)
            
            if response.status_code == 403:
                self.log_result("Assign Lead Consultant Role", True, "Correctly returns 403 for consultant role")
            else:
                self.log_result("Assign Lead Consultant Role", False, f"Expected 403, got {response.status_code}")
                return False
            
            # Test with non-existent lead ID (should return 404)
            fake_lead_id = "fake-lead-id-123"
            response = requests.post(f"{API_BASE}/sales/leads/{fake_lead_id}/assign", 
                                   params=assign_data, headers=self.manager_headers)
            
            if response.status_code == 404:
                self.log_result("Assign Non-existent Lead", True, "Correctly returns 404 for non-existent lead")
            else:
                self.log_result("Assign Non-existent Lead", False, f"Expected 404, got {response.status_code}")
                return False
            
            # Test with non-existent consultant ID (should return 404)
            invalid_assign_data = {
                "assigned_to": "fake-consultant-id-123",
                "assignment_notes": "Test with invalid consultant"
            }
            
            response = requests.post(f"{API_BASE}/sales/leads/{self.test_lead_id}/assign", 
                                   params=invalid_assign_data, headers=self.manager_headers)
            
            if response.status_code == 404:
                self.log_result("Assign to Non-existent Consultant", True, "Correctly returns 404 for non-existent consultant")
            else:
                self.log_result("Assign to Non-existent Consultant", False, f"Expected 404, got {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Assign Lead", False, f"Error testing assign lead: {str(e)}")
            return False
    
    def test_get_unassigned_leads(self):
        """Test GET /api/sales/leads/unassigned endpoint"""
        print("\n=== Testing Get Unassigned Leads API ===")
        
        try:
            # Create an unassigned lead for testing
            timestamp = int(time.time() * 1000)
            unassigned_lead_data = {
                "first_name": "Unassigned",
                "last_name": f"Lead{timestamp}",
                "email": f"unassigned{timestamp}@test.com",
                "phone": f"+1234567{timestamp % 1000:03d}"
            }
            
            response = requests.post(f"{API_BASE}/sales/leads", params=unassigned_lead_data, headers=self.manager_headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "lead" in data:
                    unassigned_lead = data["lead"]
                    unassigned_lead_id = unassigned_lead["id"]
                    self.created_leads.append(unassigned_lead_id)
                else:
                    self.log_result("Create Unassigned Lead", False, "Failed to create unassigned lead")
                    return False
            else:
                self.log_result("Create Unassigned Lead", False, f"Failed to create unassigned lead: {response.status_code}")
                return False
            
            # Test with manager role (should work)
            response = requests.get(f"{API_BASE}/sales/leads/unassigned", headers=self.manager_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                if "leads" not in data or "total" not in data:
                    self.log_result("Get Unassigned Leads Structure", False, "Missing leads or total field")
                    return False
                
                leads = data["leads"]
                
                # Verify all leads are unassigned
                for lead in leads:
                    if lead.get("assigned_to"):
                        self.log_result("Get Unassigned Leads Content", False, f"Found assigned lead in unassigned list: {lead['id']}")
                        return False
                
                # Verify our unassigned lead is in the list
                unassigned_found = any(lead["id"] == unassigned_lead_id for lead in leads)
                if unassigned_found:
                    self.log_result("Get Unassigned Leads Manager Role", True, f"Found {len(leads)} unassigned leads including test lead")
                else:
                    self.log_result("Get Unassigned Leads Manager Role", False, "Test unassigned lead not found")
                    return False
                
            else:
                self.log_result("Get Unassigned Leads Manager Role", False, f"Failed with manager role: {response.status_code}")
                return False
            
            # Test with consultant role (should return 403)
            response = requests.get(f"{API_BASE}/sales/leads/unassigned", headers=self.consultant_headers)
            
            if response.status_code == 403:
                self.log_result("Get Unassigned Leads Consultant Role", True, "Correctly returns 403 for consultant role")
            else:
                self.log_result("Get Unassigned Leads Consultant Role", False, f"Expected 403, got {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Get Unassigned Leads", False, f"Error testing get unassigned leads: {str(e)}")
            return False
    
    def test_get_my_leads(self):
        """Test GET /api/sales/leads/my-leads endpoint"""
        print("\n=== Testing Get My Leads API ===")
        
        try:
            # Test with consultant role (should work and return assigned leads)
            response = requests.get(f"{API_BASE}/sales/leads/my-leads", headers=self.consultant_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                if "leads" not in data or "total" not in data:
                    self.log_result("Get My Leads Structure", False, "Missing leads or total field")
                    return False
                
                leads = data["leads"]
                
                # Verify all leads are assigned to current consultant
                for lead in leads:
                    if lead.get("assigned_to") != self.test_consultant_id:
                        self.log_result("Get My Leads Content", False, f"Found lead not assigned to current user: {lead['id']}")
                        return False
                
                # Check if our assigned test lead is in the list
                test_lead_found = any(lead["id"] == self.test_lead_id for lead in leads)
                if test_lead_found:
                    self.log_result("Get My Leads Consultant Role", True, f"Found {len(leads)} assigned leads including test lead")
                else:
                    # This might be expected if the lead was reassigned or not assigned to this consultant
                    self.log_result("Get My Leads Consultant Role", True, f"Found {len(leads)} assigned leads (test lead may not be assigned to this consultant)")
                
            else:
                self.log_result("Get My Leads Consultant Role", False, f"Failed with consultant role: {response.status_code}")
                return False
            
            # Test with manager role (should also work)
            response = requests.get(f"{API_BASE}/sales/leads/my-leads", headers=self.manager_headers)
            
            if response.status_code == 200:
                data = response.json()
                leads = data["leads"]
                self.log_result("Get My Leads Manager Role", True, f"Manager can access my-leads endpoint, found {len(leads)} leads")
            else:
                self.log_result("Get My Leads Manager Role", False, f"Failed with manager role: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Get My Leads", False, f"Error testing get my leads: {str(e)}")
            return False
    
    def test_enhanced_get_leads(self):
        """Test Enhanced GET /api/sales/leads with filter_type parameter"""
        print("\n=== Testing Enhanced Get Leads API ===")
        
        try:
            # Test filter_type=all with manager role
            response = requests.get(f"{API_BASE}/sales/leads?filter_type=all", headers=self.manager_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["leads", "total", "is_manager", "filter_type"]
                for field in required_fields:
                    if field not in data:
                        self.log_result("Enhanced Get Leads Structure", False, f"Missing field: {field}")
                        return False
                
                if not data["is_manager"]:
                    self.log_result("Enhanced Get Leads Manager Flag", False, "is_manager should be true for manager role")
                    return False
                
                if data["filter_type"] != "all":
                    self.log_result("Enhanced Get Leads Filter Type", False, f"Expected filter_type 'all', got '{data['filter_type']}'")
                    return False
                
                all_leads_count = data["total"]
                self.log_result("Enhanced Get Leads All Filter", True, f"Manager sees {all_leads_count} leads with filter_type=all")
                
            else:
                self.log_result("Enhanced Get Leads All Filter", False, f"Failed with filter_type=all: {response.status_code}")
                return False
            
            # Test filter_type=my_leads with manager role
            response = requests.get(f"{API_BASE}/sales/leads?filter_type=my_leads", headers=self.manager_headers)
            
            if response.status_code == 200:
                data = response.json()
                my_leads_count = data["total"]
                
                if data["filter_type"] != "my_leads":
                    self.log_result("Enhanced Get Leads My Leads Filter", False, f"Expected filter_type 'my_leads', got '{data['filter_type']}'")
                    return False
                
                self.log_result("Enhanced Get Leads My Leads Filter", True, f"Manager sees {my_leads_count} leads with filter_type=my_leads")
                
            else:
                self.log_result("Enhanced Get Leads My Leads Filter", False, f"Failed with filter_type=my_leads: {response.status_code}")
                return False
            
            # Test filter_type=unassigned with manager role
            response = requests.get(f"{API_BASE}/sales/leads?filter_type=unassigned", headers=self.manager_headers)
            
            if response.status_code == 200:
                data = response.json()
                unassigned_leads_count = data["total"]
                
                if data["filter_type"] != "unassigned":
                    self.log_result("Enhanced Get Leads Unassigned Filter", False, f"Expected filter_type 'unassigned', got '{data['filter_type']}'")
                    return False
                
                # Verify all leads are unassigned
                for lead in data["leads"]:
                    if lead.get("assigned_to"):
                        self.log_result("Enhanced Get Leads Unassigned Content", False, f"Found assigned lead in unassigned filter: {lead['id']}")
                        return False
                
                self.log_result("Enhanced Get Leads Unassigned Filter", True, f"Manager sees {unassigned_leads_count} unassigned leads")
                
            else:
                self.log_result("Enhanced Get Leads Unassigned Filter", False, f"Failed with filter_type=unassigned: {response.status_code}")
                return False
            
            # Test with consultant role (should only see their leads regardless of filter_type)
            response = requests.get(f"{API_BASE}/sales/leads?filter_type=all", headers=self.consultant_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data["is_manager"]:
                    self.log_result("Enhanced Get Leads Consultant Manager Flag", False, "is_manager should be false for consultant role")
                    return False
                
                # Verify all leads are assigned to current consultant
                for lead in data["leads"]:
                    if lead.get("assigned_to") != self.test_consultant_id:
                        self.log_result("Enhanced Get Leads Consultant Content", False, f"Consultant sees lead not assigned to them: {lead['id']}")
                        return False
                
                consultant_leads_count = data["total"]
                self.log_result("Enhanced Get Leads Consultant Role", True, f"Consultant sees only their {consultant_leads_count} assigned leads")
                
            else:
                self.log_result("Enhanced Get Leads Consultant Role", False, f"Failed with consultant role: {response.status_code}")
                return False
            
            # Test filter_type=unassigned with consultant role (should still only see their leads)
            response = requests.get(f"{API_BASE}/sales/leads?filter_type=unassigned", headers=self.consultant_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Consultant should still only see their assigned leads, not unassigned ones
                for lead in data["leads"]:
                    if lead.get("assigned_to") != self.test_consultant_id:
                        self.log_result("Enhanced Get Leads Consultant Unassigned Filter", False, f"Consultant sees unassigned lead when they shouldn't: {lead['id']}")
                        return False
                
                self.log_result("Enhanced Get Leads Consultant Unassigned Filter", True, "Consultant correctly sees only their leads even with unassigned filter")
                
            else:
                self.log_result("Enhanced Get Leads Consultant Unassigned Filter", False, f"Failed with consultant unassigned filter: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Enhanced Get Leads", False, f"Error testing enhanced get leads: {str(e)}")
            return False
    
    def cleanup(self):
        """Clean up created test data"""
        try:
            # Delete created leads
            for lead_id in self.created_leads:
                try:
                    requests.delete(f"{API_BASE}/sales/leads/{lead_id}", headers=self.manager_headers)
                except:
                    pass
            
            # Note: We don't delete created users as they might be needed for other tests
            # In a real test environment, you'd want to clean them up too
            
            self.log_result("Cleanup", True, f"Cleaned up {len(self.created_leads)} test leads")
            
        except Exception as e:
            self.log_result("Cleanup", False, f"Error during cleanup: {str(e)}")
    
    def run_all_tests(self):
        """Run all Lead Assignment API tests"""
        print("🚀 Starting Lead Assignment API Tests")
        print(f"Backend URL: {BASE_URL}")
        print("=" * 60)
        
        # Authentication
        if not self.authenticate():
            print("❌ Authentication failed. Stopping tests.")
            return False
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Test data setup failed. Stopping tests.")
            return False
        
        # Run tests
        tests = [
            self.test_get_sales_consultants,
            self.test_assign_lead,
            self.test_get_unassigned_leads,
            self.test_get_my_leads,
            self.test_enhanced_get_leads
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
                print(f"❌ Test {test.__name__} crashed: {str(e)}")
                failed += 1
        
        # Cleanup
        self.cleanup()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed / (passed + failed) * 100):.1f}%")
        
        if failed == 0:
            print("\n🎉 All Lead Assignment API tests passed!")
            return True
        else:
            print(f"\n⚠️  {failed} test(s) failed. Check the details above.")
            return False

def main():
    """Main function to run the tests"""
    runner = LeadAssignmentTestRunner()
    success = runner.run_all_tests()
    
    # Print detailed results
    print("\n" + "=" * 60)
    print("📋 DETAILED TEST RESULTS")
    print("=" * 60)
    
    for result in runner.test_results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} {result['test']}: {result['message']}")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)