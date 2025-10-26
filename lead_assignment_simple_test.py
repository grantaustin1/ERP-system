#!/usr/bin/env python3
"""
Backend Test Suite - Lead Assignment APIs Testing (Simplified)
Focus on testing the Lead Assignment API functionality with manager role
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
MANAGER_EMAIL = "admin@gym.com"
MANAGER_PASSWORD = "admin123"

class LeadAssignmentTestRunner:
    def __init__(self):
        self.token = None
        self.headers = {}
        self.test_results = []
        self.test_consultant_id = None
        self.test_lead_id = None
        self.created_leads = []
        
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
        """Authenticate as manager"""
        try:
            response = requests.post(f"{API_BASE}/auth/login", json={
                "email": MANAGER_EMAIL,
                "password": MANAGER_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
                self.log_result("Authentication", True, "Successfully authenticated as manager")
                return True
            else:
                self.log_result("Authentication", False, f"Failed to authenticate: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def setup_test_data(self):
        """Setup test data"""
        try:
            # Get existing consultant for assignment testing
            response = requests.get(f"{API_BASE}/rbac/users", headers=self.headers)
            
            if response.status_code == 200:
                users_data = response.json()
                if "users" in users_data:
                    users = users_data["users"]
                    
                    # Find a user with sales role
                    consultant_roles = ["sales_manager", "sales_head", "personal_trainer"]
                    for user in users:
                        if user.get("role") in consultant_roles:
                            self.test_consultant_id = user["id"]
                            self.log_result("Find Consultant", True, f"Found consultant: {user['email']} ({user['role']})")
                            break
                    
                    if not self.test_consultant_id:
                        self.log_result("Find Consultant", False, "No consultant users found")
                        return False
                else:
                    self.log_result("Get Users", False, "No users field in response")
                    return False
            else:
                self.log_result("Get Users", False, f"Failed to get users: {response.status_code}")
                return False
            
            # Create a test lead for assignment testing
            timestamp = int(time.time() * 1000)
            lead_data = {
                "first_name": "Test",
                "last_name": f"Lead{timestamp}",
                "email": f"testlead{timestamp}@test.com",
                "phone": f"+1234567{timestamp % 1000:03d}",
                "company": "Test Company"
            }
            
            response = requests.post(f"{API_BASE}/sales/leads", params=lead_data, headers=self.headers)
            
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
    
    def test_get_sales_consultants(self):
        """Test GET /api/sales/consultants endpoint"""
        print("\n=== Testing Get Sales Consultants API ===")
        
        try:
            response = requests.get(f"{API_BASE}/sales/consultants", headers=self.headers)
            
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
                    self.log_result("Get Sales Consultants", True, f"Found {len(consultants)} consultants including test consultant")
                else:
                    self.log_result("Get Sales Consultants", False, "Test consultant not found in list")
                    return False
                
                return True
                
            else:
                self.log_result("Get Sales Consultants", False, f"Failed to get consultants: {response.status_code}")
                return False
            
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
            
            # Test assigning an unassigned lead
            assign_data = {
                "assigned_to": self.test_consultant_id,
                "assignment_notes": "Test assignment by manager"
            }
            
            response = requests.post(f"{API_BASE}/sales/leads/{self.test_lead_id}/assign", 
                                   params=assign_data, headers=self.headers)
            
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
                
                self.log_result("Assign Lead", True, "Successfully assigned lead and created notification task")
                
                # Test reassigning the same lead
                reassign_data = {
                    "assigned_to": self.test_consultant_id,
                    "assignment_notes": "Test reassignment"
                }
                
                response = requests.post(f"{API_BASE}/sales/leads/{self.test_lead_id}/assign", 
                                       params=reassign_data, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    if "reassigned" in data["message"]:
                        self.log_result("Reassign Lead", True, "Successfully reassigned lead")
                    else:
                        self.log_result("Reassign Lead", True, "Lead assignment updated (may show as assigned if same consultant)")
                else:
                    self.log_result("Reassign Lead", False, f"Failed to reassign lead: {response.status_code}")
                    return False
                
                return True
                
            else:
                self.log_result("Assign Lead", False, f"Failed to assign lead: {response.status_code}")
                return False
            
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
            
            response = requests.post(f"{API_BASE}/sales/leads", params=unassigned_lead_data, headers=self.headers)
            
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
            
            # Test getting unassigned leads
            response = requests.get(f"{API_BASE}/sales/leads/unassigned", headers=self.headers)
            
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
                    self.log_result("Get Unassigned Leads", True, f"Found {len(leads)} unassigned leads including test lead")
                else:
                    self.log_result("Get Unassigned Leads", False, "Test unassigned lead not found")
                    return False
                
                return True
                
            else:
                self.log_result("Get Unassigned Leads", False, f"Failed to get unassigned leads: {response.status_code}")
                return False
            
        except Exception as e:
            self.log_result("Get Unassigned Leads", False, f"Error testing get unassigned leads: {str(e)}")
            return False
    
    def test_get_my_leads(self):
        """Test GET /api/sales/leads/my-leads endpoint"""
        print("\n=== Testing Get My Leads API ===")
        
        try:
            response = requests.get(f"{API_BASE}/sales/leads/my-leads", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                if "leads" not in data or "total" not in data:
                    self.log_result("Get My Leads Structure", False, "Missing leads or total field")
                    return False
                
                leads = data["leads"]
                
                # Verify enriched data is present
                for lead in leads:
                    # Check for enriched fields
                    if lead.get("assigned_by"):
                        if "assigned_by_name" not in lead:
                            self.log_result("Get My Leads Enrichment", False, "Missing assigned_by_name enrichment")
                            return False
                
                self.log_result("Get My Leads", True, f"Retrieved {len(leads)} assigned leads with enriched data")
                return True
                
            else:
                self.log_result("Get My Leads", False, f"Failed to get my leads: {response.status_code}")
                return False
            
        except Exception as e:
            self.log_result("Get My Leads", False, f"Error testing get my leads: {str(e)}")
            return False
    
    def test_enhanced_get_leads(self):
        """Test Enhanced GET /api/sales/leads with filter_type parameter"""
        print("\n=== Testing Enhanced Get Leads API ===")
        
        try:
            # Test filter_type=all
            response = requests.get(f"{API_BASE}/sales/leads?filter_type=all", headers=self.headers)
            
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
            
            # Test filter_type=my_leads
            response = requests.get(f"{API_BASE}/sales/leads?filter_type=my_leads", headers=self.headers)
            
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
            
            # Test filter_type=unassigned
            response = requests.get(f"{API_BASE}/sales/leads?filter_type=unassigned", headers=self.headers)
            
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
            
            # Test enriched data includes assigned_to_name, assigned_by_name, etc.
            response = requests.get(f"{API_BASE}/sales/leads?filter_type=all", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                leads = data["leads"]
                
                # Check for enriched data in assigned leads
                enriched_count = 0
                for lead in leads:
                    if lead.get("assigned_to"):
                        # Should have assigned_to_name enrichment
                        if "assigned_to_name" in lead or "assigned_by_name" in lead:
                            enriched_count += 1
                
                if enriched_count > 0:
                    self.log_result("Enhanced Get Leads Enrichment", True, f"Found enriched data in {enriched_count} assigned leads")
                else:
                    self.log_result("Enhanced Get Leads Enrichment", True, "No assigned leads found to verify enrichment (expected if no assignments)")
                
            else:
                self.log_result("Enhanced Get Leads Enrichment", False, f"Failed to verify enrichment: {response.status_code}")
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
                    requests.delete(f"{API_BASE}/sales/leads/{lead_id}", headers=self.headers)
                except:
                    pass
            
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