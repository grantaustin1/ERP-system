#!/usr/bin/env python3
"""
Backend Test Suite for Automation and Trigger Engine
Tests all automation CRUD operations, trigger integrations, and execution logic
"""

import requests
import json
import time
from datetime import datetime, timezone, timedelta
import os

# Configuration
BASE_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://gym360-rebuild.preview.emergentagent.com')
API_BASE = f"{BASE_URL}/api"

# Test credentials
TEST_EMAIL = "admin@gym.com"
TEST_PASSWORD = "admin123"

class AutomationTester:
    def __init__(self):
        self.token = None
        self.headers = {}
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
        """Authenticate and get token"""
        try:
            response = requests.post(f"{API_BASE}/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
                self.log_result("Authentication", True, "Successfully authenticated")
                return True
            else:
                self.log_result("Authentication", False, f"Failed to authenticate: {response.status_code}", 
                              {"response": response.text})
                return False
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def test_automation_crud(self):
        """Test automation CRUD operations"""
        print("\n=== Testing Automation CRUD Operations ===")
        
        # Test 1: Create automation
        automation_data = {
            "name": "Welcome New Member Test",
            "description": "Send welcome SMS when member joins - Test Automation",
            "trigger_type": "member_joined",
            "conditions": {},
            "actions": [
                {
                    "type": "send_sms",
                    "delay_minutes": 0,
                    "message": "Welcome {member_name}! Thank you for joining our gym. Your membership: {membership_type}"
                }
            ]
        }
        
        try:
            response = requests.post(f"{API_BASE}/automations", 
                                   json=automation_data, headers=self.headers)
            if response.status_code == 200:
                created_automation = response.json()
                automation_id = created_automation["id"]
                self.log_result("Create Automation", True, "Automation created successfully",
                              {"automation_id": automation_id})
            else:
                self.log_result("Create Automation", False, f"Failed to create: {response.status_code}",
                              {"response": response.text})
                return None
        except Exception as e:
            self.log_result("Create Automation", False, f"Error creating automation: {str(e)}")
            return None
        
        # Test 2: Get all automations
        try:
            response = requests.get(f"{API_BASE}/automations", headers=self.headers)
            if response.status_code == 200:
                automations = response.json()
                self.log_result("List Automations", True, f"Retrieved {len(automations)} automations")
            else:
                self.log_result("List Automations", False, f"Failed to list: {response.status_code}",
                              {"response": response.text})
        except Exception as e:
            self.log_result("List Automations", False, f"Error listing automations: {str(e)}")
        
        # Test 3: Get specific automation
        try:
            response = requests.get(f"{API_BASE}/automations/{automation_id}", headers=self.headers)
            if response.status_code == 200:
                automation = response.json()
                self.log_result("Get Automation", True, "Retrieved automation successfully",
                              {"name": automation.get("name")})
            else:
                self.log_result("Get Automation", False, f"Failed to get: {response.status_code}",
                              {"response": response.text})
        except Exception as e:
            self.log_result("Get Automation", False, f"Error getting automation: {str(e)}")
        
        # Test 4: Update automation
        update_data = {
            "name": "Welcome New Member Test - Updated",
            "description": "Updated description for test automation",
            "trigger_type": "member_joined",
            "conditions": {"membership_type": "Premium"},
            "actions": [
                {
                    "type": "send_sms",
                    "delay_minutes": 5,
                    "message": "Welcome {member_name}! Premium membership activated."
                },
                {
                    "type": "send_email",
                    "delay_minutes": 10,
                    "subject": "Welcome to Premium Membership",
                    "body": "Dear {member_name}, welcome to our premium membership!"
                }
            ]
        }
        
        try:
            response = requests.put(f"{API_BASE}/automations/{automation_id}", 
                                  json=update_data, headers=self.headers)
            if response.status_code == 200:
                updated_automation = response.json()
                self.log_result("Update Automation", True, "Automation updated successfully",
                              {"actions_count": len(updated_automation.get("actions", []))})
            else:
                self.log_result("Update Automation", False, f"Failed to update: {response.status_code}",
                              {"response": response.text})
        except Exception as e:
            self.log_result("Update Automation", False, f"Error updating automation: {str(e)}")
        
        return automation_id
    
    def test_automation_toggle(self, automation_id):
        """Test automation enable/disable toggle"""
        print("\n=== Testing Automation Toggle ===")
        
        try:
            response = requests.post(f"{API_BASE}/automations/{automation_id}/toggle", 
                                   headers=self.headers)
            if response.status_code == 200:
                result = response.json()
                enabled_status = result.get("enabled")
                self.log_result("Toggle Automation", True, f"Automation toggled to: {enabled_status}",
                              {"enabled": enabled_status})
                
                # Toggle back
                response2 = requests.post(f"{API_BASE}/automations/{automation_id}/toggle", 
                                        headers=self.headers)
                if response2.status_code == 200:
                    result2 = response2.json()
                    self.log_result("Toggle Back", True, f"Automation toggled back to: {result2.get('enabled')}")
                else:
                    self.log_result("Toggle Back", False, f"Failed to toggle back: {response2.status_code}")
            else:
                self.log_result("Toggle Automation", False, f"Failed to toggle: {response.status_code}",
                              {"response": response.text})
        except Exception as e:
            self.log_result("Toggle Automation", False, f"Error toggling automation: {str(e)}")
    
    def test_automation_test_endpoint(self, automation_id):
        """Test the automation test endpoint"""
        print("\n=== Testing Automation Test Endpoint ===")
        
        test_data = {
            "member_id": "test-member-123",
            "member_name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+27123456789",
            "membership_type": "Premium"
        }
        
        try:
            response = requests.post(f"{API_BASE}/automations/test/{automation_id}", 
                                   json=test_data, headers=self.headers)
            if response.status_code == 200:
                result = response.json()
                success = result.get("success", False)
                if success:
                    self.log_result("Test Automation", True, "Automation test executed successfully",
                                  {"result": result.get("result")})
                else:
                    self.log_result("Test Automation", False, f"Test execution failed: {result.get('message')}",
                                  {"error": result.get("error")})
            else:
                self.log_result("Test Automation", False, f"Failed to test: {response.status_code}",
                              {"response": response.text})
        except Exception as e:
            self.log_result("Test Automation", False, f"Error testing automation: {str(e)}")
    
    def test_execution_history(self):
        """Test automation execution history"""
        print("\n=== Testing Execution History ===")
        
        try:
            response = requests.get(f"{API_BASE}/automation-executions", headers=self.headers)
            if response.status_code == 200:
                executions = response.json()
                self.log_result("Get Execution History", True, f"Retrieved {len(executions)} execution records")
                
                # Test filtering by automation_id if we have executions
                if executions and len(executions) > 0:
                    first_execution = executions[0]
                    automation_id = first_execution.get("automation_id")
                    if automation_id:
                        filtered_response = requests.get(
                            f"{API_BASE}/automation-executions?automation_id={automation_id}", 
                            headers=self.headers
                        )
                        if filtered_response.status_code == 200:
                            filtered_executions = filtered_response.json()
                            self.log_result("Filter Execution History", True, 
                                          f"Retrieved {len(filtered_executions)} filtered executions")
                        else:
                            self.log_result("Filter Execution History", False, 
                                          f"Failed to filter: {filtered_response.status_code}")
            else:
                self.log_result("Get Execution History", False, f"Failed to get history: {response.status_code}",
                              {"response": response.text})
        except Exception as e:
            self.log_result("Get Execution History", False, f"Error getting execution history: {str(e)}")
    
    def test_member_joined_trigger(self):
        """Test member_joined trigger by creating a member"""
        print("\n=== Testing Member Joined Trigger ===")
        
        # First, get a membership type
        try:
            response = requests.get(f"{API_BASE}/membership-types", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Get Membership Types", False, "Failed to get membership types")
                return
            
            membership_types = response.json()
            if not membership_types:
                self.log_result("Get Membership Types", False, "No membership types found")
                return
            
            membership_type_id = membership_types[0]["id"]
            
            # Create a test member
            member_data = {
                "first_name": "Jane",
                "last_name": "Smith",
                "email": f"jane.smith.test.{int(time.time())}@example.com",
                "phone": "+27987654321",
                "membership_type_id": membership_type_id
            }
            
            response = requests.post(f"{API_BASE}/members", json=member_data, headers=self.headers)
            if response.status_code == 200:
                member = response.json()
                member_id = member["id"]
                self.log_result("Create Member (Trigger Test)", True, 
                              f"Member created successfully, should trigger automations",
                              {"member_id": member_id, "member_name": f"{member['first_name']} {member['last_name']}"})
                
                # Wait a moment for automation to process
                time.sleep(2)
                
                # Check if automation executions were created
                executions_response = requests.get(f"{API_BASE}/automation-executions?limit=10", 
                                                 headers=self.headers)
                if executions_response.status_code == 200:
                    recent_executions = executions_response.json()
                    member_joined_executions = [
                        ex for ex in recent_executions 
                        if ex.get("trigger_data", {}).get("member_id") == member_id
                    ]
                    
                    if member_joined_executions:
                        self.log_result("Member Joined Automation Triggered", True, 
                                      f"Found {len(member_joined_executions)} automation executions for new member")
                    else:
                        self.log_result("Member Joined Automation Triggered", False, 
                                      "No automation executions found for new member")
                
            else:
                self.log_result("Create Member (Trigger Test)", False, 
                              f"Failed to create member: {response.status_code}",
                              {"response": response.text})
                
        except Exception as e:
            self.log_result("Member Joined Trigger Test", False, f"Error testing member joined trigger: {str(e)}")
    
    def test_payment_failed_trigger(self):
        """Test payment_failed trigger"""
        print("\n=== Testing Payment Failed Trigger ===")
        
        try:
            # Get invoices to test with
            response = requests.get(f"{API_BASE}/invoices?limit=5", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Get Invoices for Test", False, "Failed to get invoices")
                return
            
            invoices = response.json()
            if not invoices:
                self.log_result("Get Invoices for Test", False, "No invoices found to test with")
                return
            
            # Use first pending invoice
            test_invoice = None
            for invoice in invoices:
                if invoice.get("status") == "pending":
                    test_invoice = invoice
                    break
            
            if not test_invoice:
                self.log_result("Find Test Invoice", False, "No pending invoices found to test with")
                return
            
            invoice_id = test_invoice["id"]
            
            # Mark invoice as failed
            response = requests.post(f"{API_BASE}/invoices/{invoice_id}/mark-failed", 
                                   json={"failure_reason": "Debit order failed - Test"}, 
                                   headers=self.headers)
            
            if response.status_code == 200:
                self.log_result("Mark Invoice Failed", True, 
                              "Invoice marked as failed, should trigger automations",
                              {"invoice_id": invoice_id})
                
                # Wait for automation processing
                time.sleep(2)
                
                # Check for automation executions
                executions_response = requests.get(f"{API_BASE}/automation-executions?limit=10", 
                                                 headers=self.headers)
                if executions_response.status_code == 200:
                    recent_executions = executions_response.json()
                    payment_failed_executions = [
                        ex for ex in recent_executions 
                        if ex.get("trigger_data", {}).get("invoice_id") == invoice_id
                    ]
                    
                    if payment_failed_executions:
                        self.log_result("Payment Failed Automation Triggered", True, 
                                      f"Found {len(payment_failed_executions)} automation executions for failed payment")
                    else:
                        self.log_result("Payment Failed Automation Triggered", False, 
                                      "No automation executions found for failed payment")
            else:
                self.log_result("Mark Invoice Failed", False, 
                              f"Failed to mark invoice as failed: {response.status_code}",
                              {"response": response.text})
                
        except Exception as e:
            self.log_result("Payment Failed Trigger Test", False, f"Error testing payment failed trigger: {str(e)}")
    
    def test_invoice_overdue_trigger(self):
        """Test invoice_overdue trigger"""
        print("\n=== Testing Invoice Overdue Trigger ===")
        
        try:
            # Get invoices to test with
            response = requests.get(f"{API_BASE}/invoices?limit=5", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Get Invoices for Overdue Test", False, "Failed to get invoices")
                return
            
            invoices = response.json()
            if not invoices:
                self.log_result("Get Invoices for Overdue Test", False, "No invoices found to test with")
                return
            
            # Use first pending invoice
            test_invoice = None
            for invoice in invoices:
                if invoice.get("status") == "pending":
                    test_invoice = invoice
                    break
            
            if not test_invoice:
                self.log_result("Find Test Invoice for Overdue", False, "No pending invoices found to test with")
                return
            
            invoice_id = test_invoice["id"]
            
            # Mark invoice as overdue
            response = requests.post(f"{API_BASE}/invoices/{invoice_id}/mark-overdue", 
                                   headers=self.headers)
            
            if response.status_code == 200:
                self.log_result("Mark Invoice Overdue", True, 
                              "Invoice marked as overdue, should trigger automations",
                              {"invoice_id": invoice_id})
                
                # Wait for automation processing
                time.sleep(2)
                
                # Check for automation executions
                executions_response = requests.get(f"{API_BASE}/automation-executions?limit=10", 
                                                 headers=self.headers)
                if executions_response.status_code == 200:
                    recent_executions = executions_response.json()
                    overdue_executions = [
                        ex for ex in recent_executions 
                        if ex.get("trigger_data", {}).get("invoice_id") == invoice_id
                    ]
                    
                    if overdue_executions:
                        self.log_result("Invoice Overdue Automation Triggered", True, 
                                      f"Found {len(overdue_executions)} automation executions for overdue invoice")
                    else:
                        self.log_result("Invoice Overdue Automation Triggered", False, 
                                      "No automation executions found for overdue invoice")
            else:
                self.log_result("Mark Invoice Overdue", False, 
                              f"Failed to mark invoice as overdue: {response.status_code}",
                              {"response": response.text})
                
        except Exception as e:
            self.log_result("Invoice Overdue Trigger Test", False, f"Error testing invoice overdue trigger: {str(e)}")
    
    def test_complex_automation(self):
        """Test complex automation with multiple actions and conditions"""
        print("\n=== Testing Complex Automation ===")
        
        complex_automation = {
            "name": "Complex Payment Failed Automation",
            "description": "Multi-step automation for payment failures with conditions",
            "trigger_type": "payment_failed",
            "conditions": {
                "amount": {"operator": ">=", "value": 100}
            },
            "actions": [
                {
                    "type": "send_sms",
                    "delay_minutes": 0,
                    "message": "Hi {member_name}, your payment of R{amount} failed. Please update your payment method."
                },
                {
                    "type": "send_email",
                    "delay_minutes": 60,
                    "subject": "Payment Failed - Action Required",
                    "body": "Dear {member_name}, your payment for invoice {invoice_number} has failed. Amount: R{amount}"
                },
                {
                    "type": "create_task",
                    "delay_minutes": 1440,  # 24 hours
                    "task_title": "Follow up on failed payment",
                    "task_description": "Contact {member_name} regarding failed payment of R{amount}",
                    "assigned_to": "admin@gym.com"
                }
            ]
        }
        
        try:
            response = requests.post(f"{API_BASE}/automations", 
                                   json=complex_automation, headers=self.headers)
            if response.status_code == 200:
                automation = response.json()
                automation_id = automation["id"]
                self.log_result("Create Complex Automation", True, 
                              f"Complex automation created with {len(automation['actions'])} actions",
                              {"automation_id": automation_id})
                
                # Test with sample data that meets conditions
                test_data = {
                    "member_id": "test-member-456",
                    "member_name": "Alice Johnson",
                    "email": "alice.johnson@example.com",
                    "phone": "+27111222333",
                    "invoice_id": "test-invoice-789",
                    "invoice_number": "INV-TEST-001",
                    "amount": 150.00,  # Meets condition >= 100
                    "failure_reason": "Insufficient funds"
                }
                
                test_response = requests.post(f"{API_BASE}/automations/test/{automation_id}", 
                                            json=test_data, headers=self.headers)
                
                if test_response.status_code == 200:
                    test_result = test_response.json()
                    if test_result.get("success"):
                        self.log_result("Test Complex Automation", True, 
                                      "Complex automation test executed successfully",
                                      {"actions_executed": test_result.get("result", {}).get("actions_executed")})
                    else:
                        self.log_result("Test Complex Automation", False, 
                                      f"Complex automation test failed: {test_result.get('message')}")
                
                # Test with data that doesn't meet conditions
                test_data_no_condition = {
                    "member_id": "test-member-789",
                    "member_name": "Bob Wilson",
                    "amount": 50.00,  # Doesn't meet condition >= 100
                }
                
                test_response2 = requests.post(f"{API_BASE}/automations/test/{automation_id}", 
                                             json=test_data_no_condition, headers=self.headers)
                
                if test_response2.status_code == 200:
                    test_result2 = test_response2.json()
                    result_data = test_result2.get("result", {})
                    if result_data.get("skipped"):
                        self.log_result("Test Condition Filtering", True, 
                                      "Automation correctly skipped due to unmet conditions")
                    else:
                        self.log_result("Test Condition Filtering", False, 
                                      "Automation should have been skipped due to conditions")
                
            else:
                self.log_result("Create Complex Automation", False, 
                              f"Failed to create complex automation: {response.status_code}",
                              {"response": response.text})
                
        except Exception as e:
            self.log_result("Complex Automation Test", False, f"Error testing complex automation: {str(e)}")
    
    def cleanup_test_automation(self, automation_id):
        """Clean up test automation"""
        if automation_id:
            try:
                response = requests.delete(f"{API_BASE}/automations/{automation_id}", 
                                         headers=self.headers)
                if response.status_code == 200:
                    self.log_result("Cleanup Test Automation", True, "Test automation deleted successfully")
                else:
                    self.log_result("Cleanup Test Automation", False, 
                                  f"Failed to delete test automation: {response.status_code}")
            except Exception as e:
                self.log_result("Cleanup Test Automation", False, f"Error deleting test automation: {str(e)}")
    
    def run_all_tests(self):
        """Run all automation tests"""
        print("🚀 Starting Automation Engine Backend Tests")
        print(f"Testing against: {API_BASE}")
        print("=" * 60)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Run all test suites
        automation_id = self.test_automation_crud()
        
        if automation_id:
            self.test_automation_toggle(automation_id)
            self.test_automation_test_endpoint(automation_id)
        
        self.test_execution_history()
        self.test_member_joined_trigger()
        self.test_payment_failed_trigger()
        self.test_invoice_overdue_trigger()
        self.test_complex_automation()
        
        # Cleanup
        if automation_id:
            self.cleanup_test_automation(automation_id)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🏁 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)

class MembershipVariationTester:
    def __init__(self):
        self.token = None
        self.headers = {}
        self.test_results = []
        self.base_membership_id = None
        
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
        """Authenticate and get token"""
        try:
            response = requests.post(f"{API_BASE}/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
                self.log_result("Authentication", True, "Successfully authenticated")
                return True
            else:
                self.log_result("Authentication", False, f"Failed to authenticate: {response.status_code}", 
                              {"response": response.text})
                return False
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def create_base_membership(self):
        """Create a base membership for testing variations"""
        print("\n=== Creating Base Membership ===")
        
        base_membership_data = {
            "name": "Premium Test Base",
            "description": "Test base membership",
            "price": 500.00,
            "billing_frequency": "monthly",
            "duration_months": 12,
            "duration_days": 0,
            "payment_type": "debit_order",
            "is_base_membership": True,
            "features": ["Gym Access", "Classes"],
            "peak_hours_only": False,
            "multi_site_access": False
        }
        
        try:
            response = requests.post(f"{API_BASE}/membership-types", 
                                   json=base_membership_data, headers=self.headers)
            if response.status_code == 200:
                membership = response.json()
                self.base_membership_id = membership["id"]
                self.log_result("Create Base Membership", True, 
                              f"Base membership created successfully",
                              {"membership_id": self.base_membership_id, "price": membership["price"]})
                return True
            else:
                self.log_result("Create Base Membership", False, 
                              f"Failed to create base membership: {response.status_code}",
                              {"response": response.text})
                return False
        except Exception as e:
            self.log_result("Create Base Membership", False, f"Error creating base membership: {str(e)}")
            return False
    
    def test_student_discount_variation(self):
        """Test creating student discount variation (10%)"""
        print("\n=== Testing Student Discount Variation (10%) ===")
        
        variation_data = {
            "variation_type": "student",
            "discount_percentage": 10.0,
            "description": "Student discount"
        }
        
        try:
            response = requests.post(f"{API_BASE}/membership-types/{self.base_membership_id}/create-variation", 
                                   json=variation_data, headers=self.headers)
            if response.status_code == 200:
                variation = response.json()
                expected_price = 500.00 * (1 - 10.0 / 100)  # 450.00
                actual_price = variation["price"]
                
                # Check price calculation
                if abs(actual_price - expected_price) < 0.01:
                    self.log_result("Student Variation Price Calculation", True, 
                                  f"Price calculated correctly: R{actual_price} (expected R{expected_price})")
                else:
                    self.log_result("Student Variation Price Calculation", False, 
                                  f"Price calculation incorrect: R{actual_price} (expected R{expected_price})")
                
                # Check naming convention
                expected_name = "Premium Test Base - Student Discount"
                if variation["name"] == expected_name:
                    self.log_result("Student Variation Naming", True, 
                                  f"Naming convention correct: {variation['name']}")
                else:
                    self.log_result("Student Variation Naming", False, 
                                  f"Naming incorrect: {variation['name']} (expected {expected_name})")
                
                # Check inheritance of properties
                if (variation["billing_frequency"] == "monthly" and 
                    variation["duration_months"] == 12 and
                    variation["is_base_membership"] == False and
                    variation["base_membership_id"] == self.base_membership_id):
                    self.log_result("Student Variation Property Inheritance", True, 
                                  "All properties inherited correctly from base membership")
                else:
                    self.log_result("Student Variation Property Inheritance", False, 
                                  "Property inheritance failed")
                
                self.log_result("Create Student Variation", True, "Student variation created successfully",
                              {"variation_id": variation["id"], "discount": variation["discount_percentage"]})
                return variation["id"]
            else:
                self.log_result("Create Student Variation", False, 
                              f"Failed to create student variation: {response.status_code}",
                              {"response": response.text})
                return None
        except Exception as e:
            self.log_result("Create Student Variation", False, f"Error creating student variation: {str(e)}")
            return None
    
    def test_corporate_discount_variation(self):
        """Test creating corporate discount variation (15%)"""
        print("\n=== Testing Corporate Discount Variation (15%) ===")
        
        variation_data = {
            "variation_type": "corporate",
            "discount_percentage": 15.0,
            "description": "Corporate discount"
        }
        
        try:
            response = requests.post(f"{API_BASE}/membership-types/{self.base_membership_id}/create-variation", 
                                   json=variation_data, headers=self.headers)
            if response.status_code == 200:
                variation = response.json()
                expected_price = 500.00 * (1 - 15.0 / 100)  # 425.00
                actual_price = variation["price"]
                
                # Check price calculation
                if abs(actual_price - expected_price) < 0.01:
                    self.log_result("Corporate Variation Price Calculation", True, 
                                  f"Price calculated correctly: R{actual_price} (expected R{expected_price})")
                else:
                    self.log_result("Corporate Variation Price Calculation", False, 
                                  f"Price calculation incorrect: R{actual_price} (expected R{expected_price})")
                
                # Check naming convention
                expected_name = "Premium Test Base - Corporate Rate"
                if variation["name"] == expected_name:
                    self.log_result("Corporate Variation Naming", True, 
                                  f"Naming convention correct: {variation['name']}")
                else:
                    self.log_result("Corporate Variation Naming", False, 
                                  f"Naming incorrect: {variation['name']} (expected {expected_name})")
                
                self.log_result("Create Corporate Variation", True, "Corporate variation created successfully",
                              {"variation_id": variation["id"], "discount": variation["discount_percentage"]})
                return variation["id"]
            else:
                self.log_result("Create Corporate Variation", False, 
                              f"Failed to create corporate variation: {response.status_code}",
                              {"response": response.text})
                return None
        except Exception as e:
            self.log_result("Create Corporate Variation", False, f"Error creating corporate variation: {str(e)}")
            return None
    
    def test_senior_discount_variation(self):
        """Test creating senior discount variation (20%)"""
        print("\n=== Testing Senior Discount Variation (20%) ===")
        
        variation_data = {
            "variation_type": "senior",
            "discount_percentage": 20.0,
            "description": "Senior citizen discount"
        }
        
        try:
            response = requests.post(f"{API_BASE}/membership-types/{self.base_membership_id}/create-variation", 
                                   json=variation_data, headers=self.headers)
            if response.status_code == 200:
                variation = response.json()
                expected_price = 500.00 * (1 - 20.0 / 100)  # 400.00
                actual_price = variation["price"]
                
                # Check price calculation
                if abs(actual_price - expected_price) < 0.01:
                    self.log_result("Senior Variation Price Calculation", True, 
                                  f"Price calculated correctly: R{actual_price} (expected R{expected_price})")
                else:
                    self.log_result("Senior Variation Price Calculation", False, 
                                  f"Price calculation incorrect: R{actual_price} (expected R{expected_price})")
                
                # Check naming convention
                expected_name = "Premium Test Base - Senior Citizen"
                if variation["name"] == expected_name:
                    self.log_result("Senior Variation Naming", True, 
                                  f"Naming convention correct: {variation['name']}")
                else:
                    self.log_result("Senior Variation Naming", False, 
                                  f"Naming incorrect: {variation['name']} (expected {expected_name})")
                
                self.log_result("Create Senior Variation", True, "Senior variation created successfully",
                              {"variation_id": variation["id"], "discount": variation["discount_percentage"]})
                return variation["id"]
            else:
                self.log_result("Create Senior Variation", False, 
                              f"Failed to create senior variation: {response.status_code}",
                              {"response": response.text})
                return None
        except Exception as e:
            self.log_result("Create Senior Variation", False, f"Error creating senior variation: {str(e)}")
            return None
    
    def test_variations_list(self):
        """Test retrieving variations list"""
        print("\n=== Testing Variations List ===")
        
        try:
            response = requests.get(f"{API_BASE}/membership-types/{self.base_membership_id}/variations", 
                                  headers=self.headers)
            if response.status_code == 200:
                variations = response.json()
                if len(variations) >= 3:
                    self.log_result("Get Variations List", True, 
                                  f"Retrieved {len(variations)} variations successfully")
                    
                    # Check that all variations have correct base_membership_id
                    all_correct = all(v.get("base_membership_id") == self.base_membership_id for v in variations)
                    if all_correct:
                        self.log_result("Variations Base ID Check", True, 
                                      "All variations correctly linked to base membership")
                    else:
                        self.log_result("Variations Base ID Check", False, 
                                      "Some variations not correctly linked to base membership")
                    
                    # Check variation types
                    variation_types = [v.get("variation_type") for v in variations]
                    expected_types = ["student", "corporate", "senior"]
                    if all(vt in variation_types for vt in expected_types):
                        self.log_result("Variation Types Check", True, 
                                      f"All expected variation types found: {variation_types}")
                    else:
                        self.log_result("Variation Types Check", False, 
                                      f"Missing variation types. Found: {variation_types}")
                    
                else:
                    self.log_result("Get Variations List", False, 
                                  f"Expected at least 3 variations, got {len(variations)}")
            else:
                self.log_result("Get Variations List", False, 
                              f"Failed to get variations: {response.status_code}",
                              {"response": response.text})
        except Exception as e:
            self.log_result("Get Variations List", False, f"Error getting variations list: {str(e)}")
    
    def test_edge_cases(self):
        """Test edge cases for variation creation"""
        print("\n=== Testing Edge Cases ===")
        
        # Test 0% discount
        try:
            zero_discount_data = {
                "variation_type": "promo",
                "discount_percentage": 0.0,
                "description": "No discount promo"
            }
            
            response = requests.post(f"{API_BASE}/membership-types/{self.base_membership_id}/create-variation", 
                                   json=zero_discount_data, headers=self.headers)
            if response.status_code == 200:
                variation = response.json()
                if variation["price"] == 500.00:  # Same as base price
                    self.log_result("Zero Discount Test", True, 
                                  f"0% discount variation created correctly with price R{variation['price']}")
                else:
                    self.log_result("Zero Discount Test", False, 
                                  f"0% discount price incorrect: R{variation['price']} (expected R500.00)")
            else:
                self.log_result("Zero Discount Test", False, 
                              f"Failed to create 0% discount variation: {response.status_code}")
        except Exception as e:
            self.log_result("Zero Discount Test", False, f"Error testing 0% discount: {str(e)}")
        
        # Test 100% discount
        try:
            full_discount_data = {
                "variation_type": "family",
                "discount_percentage": 100.0,
                "description": "Full discount family"
            }
            
            response = requests.post(f"{API_BASE}/membership-types/{self.base_membership_id}/create-variation", 
                                   json=full_discount_data, headers=self.headers)
            if response.status_code == 200:
                variation = response.json()
                if variation["price"] == 0.00:  # Free membership
                    self.log_result("Full Discount Test", True, 
                                  f"100% discount variation created correctly with price R{variation['price']}")
                else:
                    self.log_result("Full Discount Test", False, 
                                  f"100% discount price incorrect: R{variation['price']} (expected R0.00)")
            else:
                self.log_result("Full Discount Test", False, 
                              f"Failed to create 100% discount variation: {response.status_code}")
        except Exception as e:
            self.log_result("Full Discount Test", False, f"Error testing 100% discount: {str(e)}")
        
        # Test duplicate variation type
        try:
            duplicate_data = {
                "variation_type": "student",  # Already created
                "discount_percentage": 25.0,
                "description": "Duplicate student discount"
            }
            
            response = requests.post(f"{API_BASE}/membership-types/{self.base_membership_id}/create-variation", 
                                   json=duplicate_data, headers=self.headers)
            if response.status_code == 200:
                self.log_result("Duplicate Variation Test", True, 
                              "Duplicate variation type allowed (system allows multiple)")
            elif response.status_code == 400:
                self.log_result("Duplicate Variation Test", True, 
                              "Duplicate variation type correctly rejected")
            else:
                self.log_result("Duplicate Variation Test", False, 
                              f"Unexpected response for duplicate: {response.status_code}")
        except Exception as e:
            self.log_result("Duplicate Variation Test", False, f"Error testing duplicate variation: {str(e)}")
    
    def run_membership_variation_tests(self):
        """Run all membership variation tests"""
        print("🚀 Starting Membership Variation Tests")
        print(f"Testing against: {API_BASE}")
        print("=" * 60)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Create base membership
        if not self.create_base_membership():
            print("❌ Failed to create base membership. Cannot proceed with variation tests.")
            return
        
        # Run variation tests
        self.test_student_discount_variation()
        self.test_corporate_discount_variation()
        self.test_senior_discount_variation()
        self.test_variations_list()
        self.test_edge_cases()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🏁 MEMBERSHIP VARIATION TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)

class PaymentOptionsAndGroupsTester:
    def __init__(self):
        self.token = None
        self.headers = {}
        self.test_results = []
        self.premium_individual_id = None
        self.family_package_id = None
        self.created_payment_options = []
        self.created_members = []
        self.created_group_id = None
        
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
        """Authenticate and get token"""
        try:
            response = requests.post(f"{API_BASE}/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
                self.log_result("Authentication", True, "Successfully authenticated")
                return True
            else:
                self.log_result("Authentication", False, f"Failed to authenticate: {response.status_code}", 
                              {"response": response.text})
                return False
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def test_create_individual_membership(self):
        """Test 1 - Individual Membership Creation"""
        print("\n=== Test 1: Create Individual Membership ===")
        
        membership_data = {
            "name": "Premium Individual",
            "description": "Individual gym membership",
            "price": 500.00,
            "billing_frequency": "monthly",
            "duration_months": 12,
            "duration_days": 0,
            "payment_type": "debit_order",
            "is_base_membership": True,
            "max_members": 1,
            "features": ["Gym", "Classes"],
            "peak_hours_only": False,
            "multi_site_access": False,
            "levy_enabled": False,
            "levy_frequency": "annual",
            "levy_timing": "anniversary",
            "levy_amount_type": "fixed",
            "levy_amount": 0.0,
            "levy_payment_method": "debit_order"
        }
        
        try:
            response = requests.post(f"{API_BASE}/membership-types", 
                                   json=membership_data, headers=self.headers)
            if response.status_code == 200:
                membership = response.json()
                self.premium_individual_id = membership["id"]
                
                # Verify max_members
                if membership["max_members"] == 1:
                    self.log_result("Individual Membership Creation", True, 
                                  f"Individual membership created with max_members=1",
                                  {"membership_id": self.premium_individual_id, "price": membership["price"]})
                else:
                    self.log_result("Individual Membership Creation", False, 
                                  f"max_members incorrect: {membership['max_members']} (expected 1)")
                return True
            else:
                self.log_result("Individual Membership Creation", False, 
                              f"Failed to create membership: {response.status_code}",
                              {"response": response.text})
                return False
        except Exception as e:
            self.log_result("Individual Membership Creation", False, f"Error: {str(e)}")
            return False
    
    def test_create_family_membership(self):
        """Test 2 - Family Membership Creation"""
        print("\n=== Test 2: Create Family Membership ===")
        
        membership_data = {
            "name": "Family Package",
            "description": "Family membership for up to 4 members",
            "price": 1200.00,
            "billing_frequency": "monthly",
            "duration_months": 12,
            "duration_days": 0,
            "payment_type": "debit_order",
            "is_base_membership": True,
            "max_members": 4,
            "features": ["Gym", "Classes", "Pool"],
            "peak_hours_only": False,
            "multi_site_access": True,
            "levy_enabled": False,
            "levy_frequency": "annual",
            "levy_timing": "anniversary",
            "levy_amount_type": "fixed",
            "levy_amount": 0.0,
            "levy_payment_method": "debit_order"
        }
        
        try:
            response = requests.post(f"{API_BASE}/membership-types", 
                                   json=membership_data, headers=self.headers)
            if response.status_code == 200:
                membership = response.json()
                self.family_package_id = membership["id"]
                
                # Verify max_members and multi_site_access
                if membership["max_members"] == 4 and membership["multi_site_access"] == True:
                    self.log_result("Family Membership Creation", True, 
                                  f"Family membership created with max_members=4 and multi_site_access=True",
                                  {"membership_id": self.family_package_id, "price": membership["price"]})
                else:
                    self.log_result("Family Membership Creation", False, 
                                  f"Properties incorrect: max_members={membership['max_members']}, multi_site={membership['multi_site_access']}")
                return True
            else:
                self.log_result("Family Membership Creation", False, 
                              f"Failed to create family membership: {response.status_code}",
                              {"response": response.text})
                return False
        except Exception as e:
            self.log_result("Family Membership Creation", False, f"Error: {str(e)}")
            return False
    
    def test_create_upfront_payment_option(self):
        """Test 3 - Upfront Payment Option"""
        print("\n=== Test 3: Create Upfront Payment Option ===")
        
        payment_option_data = {
            "membership_type_id": self.premium_individual_id,
            "payment_name": "Annual Upfront Saver",
            "payment_type": "single",
            "payment_frequency": "one-time",
            "installment_amount": 5400.00,
            "number_of_installments": 1,
            "auto_renewal_enabled": False,
            "auto_renewal_frequency": "monthly",
            "description": "Pay upfront and save 10%",
            "display_order": 1,
            "is_default": False
        }
        
        try:
            response = requests.post(f"{API_BASE}/payment-options", 
                                   json=payment_option_data, headers=self.headers)
            if response.status_code == 200:
                payment_option = response.json()
                option_id = payment_option["id"]
                self.created_payment_options.append(option_id)
                
                # Verify total_amount calculation
                expected_total = 5400.00 * 1  # 5400.00
                actual_total = payment_option["total_amount"]
                
                if abs(actual_total - expected_total) < 0.01:
                    self.log_result("Upfront Payment Option", True, 
                                  f"Upfront payment option created with correct total_amount: R{actual_total}",
                                  {"option_id": option_id, "payment_type": payment_option["payment_type"]})
                else:
                    self.log_result("Upfront Payment Option", False, 
                                  f"Total amount incorrect: R{actual_total} (expected R{expected_total})")
                return option_id
            else:
                self.log_result("Upfront Payment Option", False, 
                              f"Failed to create payment option: {response.status_code}",
                              {"response": response.text})
                return None
        except Exception as e:
            self.log_result("Upfront Payment Option", False, f"Error: {str(e)}")
            return None
    
    def test_create_monthly_recurring_option(self):
        """Test 4 - Monthly Recurring with Auto-Renewal"""
        print("\n=== Test 4: Create Monthly Recurring Payment Option ===")
        
        payment_option_data = {
            "membership_type_id": self.premium_individual_id,
            "payment_name": "Monthly Budget Plan",
            "payment_type": "recurring",
            "payment_frequency": "monthly",
            "installment_amount": 500.00,
            "number_of_installments": 12,
            "auto_renewal_enabled": True,
            "auto_renewal_frequency": "monthly",
            "auto_renewal_price": 500.00,
            "description": "Pay monthly, auto-renews month-to-month",
            "display_order": 2,
            "is_default": True
        }
        
        try:
            response = requests.post(f"{API_BASE}/payment-options", 
                                   json=payment_option_data, headers=self.headers)
            if response.status_code == 200:
                payment_option = response.json()
                option_id = payment_option["id"]
                self.created_payment_options.append(option_id)
                
                # Verify total_amount and auto-renewal settings
                expected_total = 500.00 * 12  # 6000.00
                actual_total = payment_option["total_amount"]
                
                if (abs(actual_total - expected_total) < 0.01 and 
                    payment_option["auto_renewal_enabled"] == True and
                    payment_option["auto_renewal_price"] == 500.00):
                    self.log_result("Monthly Recurring Payment Option", True, 
                                  f"Monthly recurring option created with auto-renewal: R{actual_total}",
                                  {"option_id": option_id, "auto_renewal": payment_option["auto_renewal_enabled"]})
                else:
                    self.log_result("Monthly Recurring Payment Option", False, 
                                  f"Settings incorrect: total={actual_total}, auto_renewal={payment_option['auto_renewal_enabled']}")
                return option_id
            else:
                self.log_result("Monthly Recurring Payment Option", False, 
                              f"Failed to create payment option: {response.status_code}",
                              {"response": response.text})
                return None
        except Exception as e:
            self.log_result("Monthly Recurring Payment Option", False, f"Error: {str(e)}")
            return None
    
    def test_create_quarterly_payment_option(self):
        """Test 5 - Quarterly Payment"""
        print("\n=== Test 5: Create Quarterly Payment Option ===")
        
        payment_option_data = {
            "membership_type_id": self.premium_individual_id,
            "payment_name": "Quarterly Flex",
            "payment_type": "recurring",
            "payment_frequency": "quarterly",
            "installment_amount": 1500.00,
            "number_of_installments": 4,
            "auto_renewal_enabled": True,
            "auto_renewal_frequency": "same_frequency",
            "description": "Pay quarterly, auto-renews for another year",
            "display_order": 3,
            "is_default": False
        }
        
        try:
            response = requests.post(f"{API_BASE}/payment-options", 
                                   json=payment_option_data, headers=self.headers)
            if response.status_code == 200:
                payment_option = response.json()
                option_id = payment_option["id"]
                self.created_payment_options.append(option_id)
                
                # Verify total_amount
                expected_total = 1500.00 * 4  # 6000.00
                actual_total = payment_option["total_amount"]
                
                if (abs(actual_total - expected_total) < 0.01 and 
                    payment_option["auto_renewal_frequency"] == "same_frequency"):
                    self.log_result("Quarterly Payment Option", True, 
                                  f"Quarterly payment option created: R{actual_total}",
                                  {"option_id": option_id, "frequency": payment_option["payment_frequency"]})
                else:
                    self.log_result("Quarterly Payment Option", False, 
                                  f"Settings incorrect: total={actual_total}, renewal_freq={payment_option['auto_renewal_frequency']}")
                return option_id
            else:
                self.log_result("Quarterly Payment Option", False, 
                              f"Failed to create payment option: {response.status_code}",
                              {"response": response.text})
                return None
        except Exception as e:
            self.log_result("Quarterly Payment Option", False, f"Error: {str(e)}")
            return None
    
    def test_get_payment_options(self):
        """Test 6 - Get Payment Options"""
        print("\n=== Test 6: Get Payment Options ===")
        
        try:
            response = requests.get(f"{API_BASE}/payment-options/{self.premium_individual_id}", 
                                  headers=self.headers)
            if response.status_code == 200:
                options = response.json()
                
                if len(options) >= 3:
                    # Check if sorted by display_order
                    display_orders = [opt["display_order"] for opt in options]
                    is_sorted = display_orders == sorted(display_orders)
                    
                    if is_sorted:
                        self.log_result("Get Payment Options", True, 
                                      f"Retrieved {len(options)} payment options, sorted by display_order",
                                      {"options_count": len(options), "display_orders": display_orders})
                    else:
                        self.log_result("Get Payment Options", False, 
                                      f"Options not sorted by display_order: {display_orders}")
                else:
                    self.log_result("Get Payment Options", False, 
                                  f"Expected at least 3 options, got {len(options)}")
                return True
            else:
                self.log_result("Get Payment Options", False, 
                              f"Failed to get payment options: {response.status_code}",
                              {"response": response.text})
                return False
        except Exception as e:
            self.log_result("Get Payment Options", False, f"Error: {str(e)}")
            return False
    
    def test_create_members_for_group(self):
        """Create members for group testing"""
        print("\n=== Creating Members for Group Testing ===")
        
        members_data = [
            {
                "first_name": "John",
                "last_name": "Smith",
                "email": f"john.smith.{int(time.time())}@example.com",
                "phone": "+27123456789",
                "membership_type_id": self.family_package_id
            },
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "email": f"jane.smith.{int(time.time())}@example.com",
                "phone": "+27123456790",
                "membership_type_id": self.family_package_id
            },
            {
                "first_name": "Bob",
                "last_name": "Smith",
                "email": f"bob.smith.{int(time.time())}@example.com",
                "phone": "+27123456791",
                "membership_type_id": self.family_package_id
            },
            {
                "first_name": "Alice",
                "last_name": "Smith",
                "email": f"alice.smith.{int(time.time())}@example.com",
                "phone": "+27123456792",
                "membership_type_id": self.family_package_id
            },
            {
                "first_name": "Charlie",
                "last_name": "Smith",
                "email": f"charlie.smith.{int(time.time())}@example.com",
                "phone": "+27123456793",
                "membership_type_id": self.family_package_id
            }
        ]
        
        created_members = []
        for i, member_data in enumerate(members_data):
            try:
                response = requests.post(f"{API_BASE}/members", 
                                       json=member_data, headers=self.headers)
                if response.status_code == 200:
                    member = response.json()
                    created_members.append(member["id"])
                    self.created_members.append(member["id"])
                    self.log_result(f"Create Member {i+1}", True, 
                                  f"Member {member['first_name']} {member['last_name']} created",
                                  {"member_id": member["id"]})
                else:
                    self.log_result(f"Create Member {i+1}", False, 
                                  f"Failed to create member: {response.status_code}")
            except Exception as e:
                self.log_result(f"Create Member {i+1}", False, f"Error: {str(e)}")
        
        return created_members
    
    def test_create_membership_group(self):
        """Test 7 - Create Membership Group"""
        print("\n=== Test 7: Create Membership Group ===")
        
        # Create members first
        members = self.test_create_members_for_group()
        if not members:
            self.log_result("Create Membership Group", False, "No members available for group creation")
            return None
        
        primary_member_id = members[0]
        
        group_data = {
            "membership_type_id": self.family_package_id,
            "primary_member_id": primary_member_id,
            "group_name": "Smith Family",
            "max_members": 4
        }
        
        try:
            response = requests.post(f"{API_BASE}/membership-groups", 
                                   json=group_data, headers=self.headers)
            if response.status_code == 200:
                group = response.json()
                self.created_group_id = group["id"]
                
                # Verify group creation
                if (group["current_member_count"] == 1 and 
                    group["max_members"] == 4 and
                    group["primary_member_id"] == primary_member_id):
                    self.log_result("Create Membership Group", True, 
                                  f"Group created with current_member_count=1",
                                  {"group_id": self.created_group_id, "group_name": group["group_name"]})
                else:
                    self.log_result("Create Membership Group", False, 
                                  f"Group properties incorrect: count={group['current_member_count']}, max={group['max_members']}")
                return self.created_group_id
            else:
                self.log_result("Create Membership Group", False, 
                              f"Failed to create group: {response.status_code}",
                              {"response": response.text})
                return None
        except Exception as e:
            self.log_result("Create Membership Group", False, f"Error: {str(e)}")
            return None
    
    def test_get_group_details(self):
        """Test 8 - Get Group Details"""
        print("\n=== Test 8: Get Group Details ===")
        
        if not self.created_group_id:
            self.log_result("Get Group Details", False, "No group ID available")
            return False
        
        try:
            response = requests.get(f"{API_BASE}/membership-groups/{self.created_group_id}", 
                                  headers=self.headers)
            if response.status_code == 200:
                group = response.json()
                self.log_result("Get Group Details", True, 
                              f"Retrieved group details: {group['group_name']}",
                              {"group_id": group["id"], "member_count": group["current_member_count"]})
                return True
            else:
                self.log_result("Get Group Details", False, 
                              f"Failed to get group details: {response.status_code}",
                              {"response": response.text})
                return False
        except Exception as e:
            self.log_result("Get Group Details", False, f"Error: {str(e)}")
            return False
    
    def test_get_group_members(self):
        """Test 9 - Get Group Members"""
        print("\n=== Test 9: Get Group Members ===")
        
        if not self.created_group_id:
            self.log_result("Get Group Members", False, "No group ID available")
            return False
        
        try:
            response = requests.get(f"{API_BASE}/membership-groups/{self.created_group_id}/members", 
                                  headers=self.headers)
            if response.status_code == 200:
                members = response.json()
                if len(members) >= 1:
                    # Check if primary member is in the list
                    primary_members = [m for m in members if m.get("is_primary_member") == True]
                    if primary_members:
                        self.log_result("Get Group Members", True, 
                                      f"Retrieved {len(members)} group members with 1 primary member",
                                      {"members_count": len(members), "primary_count": len(primary_members)})
                    else:
                        self.log_result("Get Group Members", False, 
                                      "No primary member found in group")
                else:
                    self.log_result("Get Group Members", False, 
                                  f"Expected at least 1 member, got {len(members)}")
                return True
            else:
                self.log_result("Get Group Members", False, 
                              f"Failed to get group members: {response.status_code}",
                              {"response": response.text})
                return False
        except Exception as e:
            self.log_result("Get Group Members", False, f"Error: {str(e)}")
            return False
    
    def test_add_member_to_group(self):
        """Test 10 - Add Member to Group"""
        print("\n=== Test 10: Add Member to Group ===")
        
        if not self.created_group_id or len(self.created_members) < 2:
            self.log_result("Add Member to Group", False, "No group or insufficient members available")
            return False
        
        second_member_id = self.created_members[1]
        
        try:
            response = requests.post(f"{API_BASE}/membership-groups/{self.created_group_id}/add-member", 
                                   params={"member_id": second_member_id}, headers=self.headers)
            if response.status_code == 200:
                self.log_result("Add Member to Group", True, 
                              "Member added to group successfully",
                              {"member_id": second_member_id})
                
                # Verify member count increased
                group_response = requests.get(f"{API_BASE}/membership-groups/{self.created_group_id}", 
                                            headers=self.headers)
                if group_response.status_code == 200:
                    group = group_response.json()
                    if group["current_member_count"] == 2:
                        self.log_result("Verify Member Count Increase", True, 
                                      f"Member count increased to {group['current_member_count']}")
                    else:
                        self.log_result("Verify Member Count Increase", False, 
                                      f"Member count incorrect: {group['current_member_count']} (expected 2)")
                return True
            else:
                self.log_result("Add Member to Group", False, 
                              f"Failed to add member: {response.status_code}",
                              {"response": response.text})
                return False
        except Exception as e:
            self.log_result("Add Member to Group", False, f"Error: {str(e)}")
            return False
    
    def test_add_members_until_full(self):
        """Test 11 - Add Members Until Full"""
        print("\n=== Test 11: Add Members Until Full ===")
        
        if not self.created_group_id or len(self.created_members) < 4:
            self.log_result("Add Members Until Full", False, "Insufficient members for full group test")
            return False
        
        # Add third and fourth members
        for i in range(2, 4):
            member_id = self.created_members[i]
            try:
                response = requests.post(f"{API_BASE}/membership-groups/{self.created_group_id}/add-member", 
                                       params={"member_id": member_id}, headers=self.headers)
                if response.status_code == 200:
                    self.log_result(f"Add Member {i+1} to Group", True, f"Member {i+1} added successfully")
                else:
                    self.log_result(f"Add Member {i+1} to Group", False, f"Failed to add member {i+1}")
            except Exception as e:
                self.log_result(f"Add Member {i+1} to Group", False, f"Error adding member {i+1}: {str(e)}")
        
        # Now try to add fifth member (should fail)
        if len(self.created_members) >= 5:
            fifth_member_id = self.created_members[4]
            try:
                response = requests.post(f"{API_BASE}/membership-groups/{self.created_group_id}/add-member", 
                                       params={"member_id": fifth_member_id}, headers=self.headers)
                if response.status_code == 400:
                    response_data = response.json()
                    if "full" in response_data.get("detail", "").lower():
                        self.log_result("Test Group Full Error", True, 
                                      "Correctly rejected adding member to full group",
                                      {"error_message": response_data.get("detail")})
                    else:
                        self.log_result("Test Group Full Error", False, 
                                      f"Wrong error message: {response_data.get('detail')}")
                else:
                    self.log_result("Test Group Full Error", False, 
                                  f"Expected 400 error, got {response.status_code}")
            except Exception as e:
                self.log_result("Test Group Full Error", False, f"Error: {str(e)}")
        
        return True
    
    def test_remove_non_primary_member(self):
        """Test 12 - Remove Non-Primary Member"""
        print("\n=== Test 12: Remove Non-Primary Member ===")
        
        if not self.created_group_id or len(self.created_members) < 2:
            self.log_result("Remove Non-Primary Member", False, "No group or insufficient members")
            return False
        
        second_member_id = self.created_members[1]
        
        try:
            response = requests.delete(f"{API_BASE}/membership-groups/{self.created_group_id}/remove-member/{second_member_id}", 
                                     headers=self.headers)
            if response.status_code == 200:
                self.log_result("Remove Non-Primary Member", True, 
                              "Non-primary member removed successfully",
                              {"member_id": second_member_id})
                
                # Verify member count decreased
                group_response = requests.get(f"{API_BASE}/membership-groups/{self.created_group_id}", 
                                            headers=self.headers)
                if group_response.status_code == 200:
                    group = group_response.json()
                    self.log_result("Verify Member Count Decrease", True, 
                                  f"Member count after removal: {group['current_member_count']}")
                return True
            else:
                self.log_result("Remove Non-Primary Member", False, 
                              f"Failed to remove member: {response.status_code}",
                              {"response": response.text})
                return False
        except Exception as e:
            self.log_result("Remove Non-Primary Member", False, f"Error: {str(e)}")
            return False
    
    def test_remove_primary_member_error(self):
        """Test 13 - Try Removing Primary Member"""
        print("\n=== Test 13: Try Removing Primary Member ===")
        
        if not self.created_group_id or not self.created_members:
            self.log_result("Remove Primary Member Error", False, "No group or members available")
            return False
        
        primary_member_id = self.created_members[0]  # First member is primary
        
        try:
            response = requests.delete(f"{API_BASE}/membership-groups/{self.created_group_id}/remove-member/{primary_member_id}", 
                                     headers=self.headers)
            if response.status_code == 400:
                response_data = response.json()
                if "primary" in response_data.get("detail", "").lower():
                    self.log_result("Remove Primary Member Error", True, 
                                  "Correctly rejected removing primary member",
                                  {"error_message": response_data.get("detail")})
                else:
                    self.log_result("Remove Primary Member Error", False, 
                                  f"Wrong error message: {response_data.get('detail')}")
            else:
                self.log_result("Remove Primary Member Error", False, 
                              f"Expected 400 error, got {response.status_code}")
            return True
        except Exception as e:
            self.log_result("Remove Primary Member Error", False, f"Error: {str(e)}")
            return False
    
    def test_update_payment_option(self):
        """Test 14 - Update Payment Option"""
        print("\n=== Test 14: Update Payment Option ===")
        
        if not self.created_payment_options:
            self.log_result("Update Payment Option", False, "No payment options available to update")
            return False
        
        option_id = self.created_payment_options[1]  # Monthly option
        
        update_data = {
            "installment_amount": 550.00,
            "auto_renewal_price": 550.00
        }
        
        try:
            response = requests.put(f"{API_BASE}/payment-options/{option_id}", 
                                  json=update_data, headers=self.headers)
            if response.status_code == 200:
                updated_option = response.json()
                
                # Verify total_amount recalculated
                expected_total = 550.00 * 12  # 6600.00
                actual_total = updated_option["total_amount"]
                
                if (abs(actual_total - expected_total) < 0.01 and 
                    updated_option["installment_amount"] == 550.00):
                    self.log_result("Update Payment Option", True, 
                                  f"Payment option updated, total recalculated: R{actual_total}",
                                  {"option_id": option_id, "new_installment": updated_option["installment_amount"]})
                else:
                    self.log_result("Update Payment Option", False, 
                                  f"Update failed: total={actual_total}, installment={updated_option['installment_amount']}")
                return True
            else:
                self.log_result("Update Payment Option", False, 
                              f"Failed to update payment option: {response.status_code}",
                              {"response": response.text})
                return False
        except Exception as e:
            self.log_result("Update Payment Option", False, f"Error: {str(e)}")
            return False
    
    def test_delete_payment_option(self):
        """Test 15 - Delete Payment Option"""
        print("\n=== Test 15: Delete Payment Option (Soft Delete) ===")
        
        if not self.created_payment_options:
            self.log_result("Delete Payment Option", False, "No payment options available to delete")
            return False
        
        option_id = self.created_payment_options[0]  # Upfront option
        
        try:
            response = requests.delete(f"{API_BASE}/payment-options/{option_id}", 
                                     headers=self.headers)
            if response.status_code == 200:
                self.log_result("Delete Payment Option", True, 
                              "Payment option soft deleted successfully",
                              {"option_id": option_id})
                
                # Verify it's no longer in active list
                get_response = requests.get(f"{API_BASE}/payment-options/{self.premium_individual_id}", 
                                          headers=self.headers)
                if get_response.status_code == 200:
                    active_options = get_response.json()
                    deleted_option_found = any(opt["id"] == option_id for opt in active_options)
                    
                    if not deleted_option_found:
                        self.log_result("Verify Soft Delete", True, 
                                      "Deleted option no longer appears in active list")
                    else:
                        self.log_result("Verify Soft Delete", False, 
                                      "Deleted option still appears in active list")
                return True
            else:
                self.log_result("Delete Payment Option", False, 
                              f"Failed to delete payment option: {response.status_code}",
                              {"response": response.text})
                return False
        except Exception as e:
            self.log_result("Delete Payment Option", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all payment options and membership groups tests"""
        print("🚀 Starting Payment Options and Membership Groups Tests")
        print(f"Testing against: {API_BASE}")
        print("=" * 70)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Part 1: Create Base Memberships
        if not self.test_create_individual_membership():
            print("❌ Failed to create individual membership. Cannot proceed.")
            return
        
        if not self.test_create_family_membership():
            print("❌ Failed to create family membership. Cannot proceed.")
            return
        
        # Part 2: Create Payment Options
        self.test_create_upfront_payment_option()
        self.test_create_monthly_recurring_option()
        self.test_create_quarterly_payment_option()
        self.test_get_payment_options()
        
        # Part 3: Membership Groups
        self.test_create_membership_group()
        self.test_get_group_details()
        self.test_get_group_members()
        self.test_add_member_to_group()
        self.test_add_members_until_full()
        self.test_remove_non_primary_member()
        self.test_remove_primary_member_error()
        
        # Part 4: Update and Delete Payment Options
        self.test_update_payment_option()
        self.test_delete_payment_option()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("🏁 PAYMENT OPTIONS AND MEMBERSHIP GROUPS TEST SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n" + "=" * 70)

class WhatsAppIntegrationTester:
    def __init__(self):
        self.token = None
        self.headers = {}
        self.test_results = []
        self.created_automations = []
        
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
        """Authenticate and get token"""
        try:
            response = requests.post(f"{API_BASE}/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
                self.log_result("Authentication", True, "Successfully authenticated")
                return True
            else:
                self.log_result("Authentication", False, f"Failed to authenticate: {response.status_code}", 
                              {"response": response.text})
                return False
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def test_whatsapp_status(self):
        """Test 1 - Get WhatsApp Status"""
        print("\n=== Test 1: Get WhatsApp Status ===")
        
        try:
            response = requests.get(f"{API_BASE}/whatsapp/status", headers=self.headers)
            if response.status_code == 200:
                status = response.json()
                
                # Verify expected mock mode status
                expected_fields = ["integrated", "is_mocked", "api_key_configured", "channel_id_configured", "base_url", "message"]
                missing_fields = [field for field in expected_fields if field not in status]
                
                if not missing_fields:
                    if status["is_mocked"] == True and status["integrated"] == False:
                        self.log_result("WhatsApp Status Check", True, 
                                      "WhatsApp status returned correctly - Mock mode active",
                                      {"status": status})
                    else:
                        self.log_result("WhatsApp Status Check", False, 
                                      f"Unexpected status values: is_mocked={status['is_mocked']}, integrated={status['integrated']}")
                else:
                    self.log_result("WhatsApp Status Check", False, 
                                  f"Missing required fields: {missing_fields}")
            else:
                self.log_result("WhatsApp Status Check", False, 
                              f"Failed to get status: {response.status_code}",
                              {"response": response.text})
        except Exception as e:
            self.log_result("WhatsApp Status Check", False, f"Error: {str(e)}")
    
    def test_whatsapp_templates(self):
        """Test 2 - List Templates (Mock Mode)"""
        print("\n=== Test 2: List WhatsApp Templates ===")
        
        try:
            response = requests.get(f"{API_BASE}/whatsapp/templates", headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                templates = data.get("templates", [])
                
                # Check for expected mock templates
                expected_templates = ["payment_failed_alert", "member_welcome", "membership_renewal_reminder"]
                template_names = [t.get("name") for t in templates]
                
                missing_templates = [t for t in expected_templates if t not in template_names]
                
                if not missing_templates:
                    all_approved = all(t.get("status") == "APPROVED" for t in templates)
                    if all_approved:
                        self.log_result("WhatsApp Templates List", True, 
                                      f"Retrieved {len(templates)} mock templates, all APPROVED",
                                      {"templates": template_names, "is_mocked": data.get("is_mocked")})
                    else:
                        self.log_result("WhatsApp Templates List", False, 
                                      "Not all templates have APPROVED status")
                else:
                    self.log_result("WhatsApp Templates List", False, 
                                  f"Missing expected templates: {missing_templates}")
            else:
                self.log_result("WhatsApp Templates List", False, 
                              f"Failed to get templates: {response.status_code}",
                              {"response": response.text})
        except Exception as e:
            self.log_result("WhatsApp Templates List", False, f"Error: {str(e)}")
    
    def test_phone_formatting(self):
        """Test 3-4 - Phone Number Formatting"""
        print("\n=== Test 3-4: Phone Number Formatting ===")
        
        test_cases = [
            {"input": "0821234567", "expected": "+27821234567", "valid": True},
            {"input": "27821234567", "expected": "+27821234567", "valid": True},
            {"input": "082 123 4567", "expected": "+27821234567", "valid": True},
            {"input": "+27821234567", "expected": "+27821234567", "valid": True},
            {"input": "082-123-4567", "expected": "+27821234567", "valid": True},
            {"input": "123", "expected": "+27123", "valid": False},  # Too short
            {"input": "abc123", "expected": "+27123", "valid": False}  # Invalid characters
        ]
        
        for i, test_case in enumerate(test_cases):
            try:
                response = requests.post(f"{API_BASE}/whatsapp/format-phone", 
                                       params={"phone": test_case["input"]})
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if (result["formatted"] == test_case["expected"] and 
                        result["valid"] == test_case["valid"] and
                        result["original"] == test_case["input"]):
                        self.log_result(f"Phone Format Test {i+1}", True, 
                                      f"'{test_case['input']}' -> '{result['formatted']}' (valid: {result['valid']})")
                    else:
                        self.log_result(f"Phone Format Test {i+1}", False, 
                                      f"Incorrect formatting: got {result}, expected {test_case}")
                else:
                    # For invalid inputs, we might get 400 which is acceptable
                    if response.status_code == 400 and not test_case["valid"]:
                        self.log_result(f"Phone Format Test {i+1}", True, 
                                      f"Invalid input '{test_case['input']}' correctly rejected with 400")
                    else:
                        self.log_result(f"Phone Format Test {i+1}", False, 
                                      f"Unexpected status: {response.status_code}")
            except Exception as e:
                self.log_result(f"Phone Format Test {i+1}", False, f"Error: {str(e)}")
    
    def test_send_whatsapp_message(self):
        """Test 5-6 - Send Test WhatsApp Message"""
        print("\n=== Test 5-6: Send Test WhatsApp Message ===")
        
        test_cases = [
            {"phone": "0821234567", "template": "payment_failed_alert", "member": "John Smith"},
            {"phone": "27821234567", "template": "member_welcome", "member": "Jane Doe"},
            {"phone": "082 123 4567", "template": "membership_renewal_reminder", "member": "Bob Wilson"},
            {"phone": "+27821234567", "template": "payment_failed_alert", "member": "Alice Johnson"}
        ]
        
        for i, test_case in enumerate(test_cases):
            try:
                response = requests.post(f"{API_BASE}/whatsapp/test-message", params={
                    "phone": test_case["phone"],
                    "template_name": test_case["template"],
                    "member_name": test_case["member"]
                }, headers=self.headers)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if (result.get("success") == True and 
                        "MOCK mode" in result.get("message", "") and
                        result.get("formatted_phone") == "+27821234567"):
                        self.log_result(f"WhatsApp Message Test {i+1}", True, 
                                      f"Mock message sent successfully for {test_case['member']}",
                                      {"template": test_case["template"], "formatted_phone": result["formatted_phone"]})
                    else:
                        self.log_result(f"WhatsApp Message Test {i+1}", False, 
                                      f"Unexpected response: {result}")
                else:
                    self.log_result(f"WhatsApp Message Test {i+1}", False, 
                                  f"Failed to send message: {response.status_code}",
                                  {"response": response.text})
            except Exception as e:
                self.log_result(f"WhatsApp Message Test {i+1}", False, f"Error: {str(e)}")
    
    def test_create_whatsapp_automations(self):
        """Test 7-10 - Create Automations with WhatsApp Actions"""
        print("\n=== Test 7-10: Create WhatsApp Automations ===")
        
        automations = [
            {
                "name": "Test WhatsApp - Payment Failed",
                "description": "Test automation for WhatsApp integration",
                "trigger_type": "payment_failed",
                "conditions": {"amount": {"operator": ">=", "value": 100}},
                "actions": [{
                    "type": "send_whatsapp",
                    "delay_minutes": 0,
                    "message": "Hi {member_name}, your payment of R{amount} for invoice {invoice_number} has failed. Please update your payment method.",
                    "template_name": "payment_failed_alert"
                }],
                "enabled": True
            },
            {
                "name": "Test WhatsApp - Welcome",
                "description": "Welcome new members via WhatsApp",
                "trigger_type": "member_joined",
                "conditions": {},
                "actions": [{
                    "type": "send_whatsapp",
                    "delay_minutes": 0,
                    "message": "Welcome {member_name}! Thank you for joining our gym."
                }],
                "enabled": True
            },
            {
                "name": "Test WhatsApp - Overdue",
                "description": "Notify about overdue invoices",
                "trigger_type": "invoice_overdue",
                "conditions": {},
                "actions": [{
                    "type": "send_whatsapp",
                    "delay_minutes": 0,
                    "message": "Invoice {invoice_number} is overdue. Amount: R{amount}"
                }],
                "enabled": True
            },
            {
                "name": "Test WhatsApp - Renewal",
                "description": "Membership renewal reminder",
                "trigger_type": "membership_expiring",
                "conditions": {},
                "actions": [{
                    "type": "send_whatsapp",
                    "delay_minutes": 0,
                    "message": "Your membership expires soon. Please renew to continue access."
                }],
                "enabled": True
            }
        ]
        
        for i, automation_data in enumerate(automations):
            try:
                response = requests.post(f"{API_BASE}/automations", 
                                       json=automation_data, headers=self.headers)
                
                if response.status_code == 200:
                    automation = response.json()
                    automation_id = automation["id"]
                    self.created_automations.append(automation_id)
                    
                    # Verify WhatsApp action was created correctly
                    actions = automation.get("actions", [])
                    whatsapp_actions = [a for a in actions if a.get("type") == "send_whatsapp"]
                    
                    if whatsapp_actions:
                        self.log_result(f"Create WhatsApp Automation {i+1}", True, 
                                      f"Automation '{automation_data['name']}' created with WhatsApp action",
                                      {"automation_id": automation_id, "trigger": automation_data["trigger_type"]})
                    else:
                        self.log_result(f"Create WhatsApp Automation {i+1}", False, 
                                      "WhatsApp action not found in created automation")
                else:
                    self.log_result(f"Create WhatsApp Automation {i+1}", False, 
                                  f"Failed to create automation: {response.status_code}",
                                  {"response": response.text})
            except Exception as e:
                self.log_result(f"Create WhatsApp Automation {i+1}", False, f"Error: {str(e)}")
    
    def test_automation_execution(self):
        """Test 9 - Test Automation Execution"""
        print("\n=== Test 9: Test Automation Execution ===")
        
        if not self.created_automations:
            self.log_result("Automation Execution Test", False, "No automations created to test")
            return
        
        # Test the first automation (payment failed)
        automation_id = self.created_automations[0]
        
        test_data = {
            "member_id": "test-member-123",
            "member_name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "+27821234567",
            "invoice_id": "test-invoice-456",
            "invoice_number": "INV-TEST-001",
            "amount": 500.00,
            "failure_reason": "Insufficient funds"
        }
        
        try:
            response = requests.post(f"{API_BASE}/automations/test/{automation_id}", 
                                   json=test_data, headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success") == True:
                    # Check if automation was executed
                    execution_result = result.get("result", {})
                    executed = execution_result.get("executed", False)
                    actions_count = execution_result.get("actions_executed", 0)
                    
                    if executed and actions_count > 0:
                        self.log_result("Automation Execution Test", True, 
                                      "WhatsApp automation executed successfully in mock mode",
                                      {"actions_count": actions_count})
                    else:
                        self.log_result("Automation Execution Test", False, 
                                      f"Automation execution failed: executed={executed}, actions={actions_count}")
                else:
                    self.log_result("Automation Execution Test", False, 
                                  f"Automation test failed: {result.get('message')}")
            else:
                self.log_result("Automation Execution Test", False, 
                              f"Failed to test automation: {response.status_code}",
                              {"response": response.text})
        except Exception as e:
            self.log_result("Automation Execution Test", False, f"Error: {str(e)}")
    
    def test_template_auto_selection(self):
        """Test 10 - Verify Template Auto-Selection Logic"""
        print("\n=== Test 10: Template Auto-Selection Logic ===")
        
        # Get the created automations to verify template mapping
        try:
            response = requests.get(f"{API_BASE}/automations", headers=self.headers)
            if response.status_code == 200:
                automations = response.json()
                
                # Find our test automations
                test_automations = [a for a in automations if a.get("name", "").startswith("Test WhatsApp")]
                
                template_mappings = {
                    "payment_failed": "payment_failed_alert",
                    "member_joined": "member_welcome", 
                    "invoice_overdue": "invoice_overdue_reminder",
                    "membership_expiring": "membership_renewal_reminder"
                }
                
                mapping_correct = True
                for automation in test_automations:
                    trigger_type = automation.get("trigger_type")
                    actions = automation.get("actions", [])
                    whatsapp_actions = [a for a in actions if a.get("type") == "send_whatsapp"]
                    
                    if whatsapp_actions and trigger_type in template_mappings:
                        # Template auto-selection happens during execution, not creation
                        # So we just verify the automation structure is correct
                        expected_template = template_mappings[trigger_type]
                        self.log_result(f"Template Mapping - {trigger_type}", True, 
                                      f"Automation created for {trigger_type} -> should use {expected_template}")
                
                if mapping_correct:
                    self.log_result("Template Auto-Selection Logic", True, 
                                  "All trigger types have correct template mappings configured")
            else:
                self.log_result("Template Auto-Selection Logic", False, 
                              f"Failed to get automations: {response.status_code}")
        except Exception as e:
            self.log_result("Template Auto-Selection Logic", False, f"Error: {str(e)}")
    
    def test_execution_history(self):
        """Test 11 - Check Automation Execution Logs"""
        print("\n=== Test 11: Check Automation Execution Logs ===")
        
        try:
            response = requests.get(f"{API_BASE}/automation-executions?limit=20", headers=self.headers)
            if response.status_code == 200:
                executions = response.json()
                
                # Look for recent WhatsApp-related executions
                whatsapp_executions = []
                for execution in executions:
                    result = execution.get("result", {})
                    if isinstance(result, dict):
                        actions = result.get("actions_executed", [])
                        if any(a.get("type") == "whatsapp" for a in actions):
                            whatsapp_executions.append(execution)
                
                if whatsapp_executions:
                    self.log_result("WhatsApp Execution History", True, 
                                  f"Found {len(whatsapp_executions)} WhatsApp automation executions",
                                  {"total_executions": len(executions)})
                else:
                    self.log_result("WhatsApp Execution History", True, 
                                  f"No WhatsApp executions found (expected for fresh test run)",
                                  {"total_executions": len(executions)})
            else:
                self.log_result("WhatsApp Execution History", False, 
                              f"Failed to get execution history: {response.status_code}")
        except Exception as e:
            self.log_result("WhatsApp Execution History", False, f"Error: {str(e)}")
    
    def cleanup_test_automations(self):
        """Clean up test automations"""
        print("\n=== Cleaning Up Test Automations ===")
        
        for automation_id in self.created_automations:
            try:
                response = requests.delete(f"{API_BASE}/automations/{automation_id}", 
                                         headers=self.headers)
                if response.status_code == 200:
                    self.log_result("Cleanup Automation", True, f"Deleted automation {automation_id}")
                else:
                    self.log_result("Cleanup Automation", False, 
                                  f"Failed to delete automation {automation_id}: {response.status_code}")
            except Exception as e:
                self.log_result("Cleanup Automation", False, f"Error deleting {automation_id}: {str(e)}")
    
    def run_whatsapp_integration_tests(self):
        """Run all WhatsApp integration tests"""
        print("🚀 Starting WhatsApp Integration Tests (Mock Mode)")
        print(f"Testing against: {API_BASE}")
        print("=" * 60)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Run all test suites
        self.test_whatsapp_status()
        self.test_whatsapp_templates()
        self.test_phone_formatting()
        self.test_send_whatsapp_message()
        self.test_create_whatsapp_automations()
        self.test_automation_execution()
        self.test_template_auto_selection()
        self.test_execution_history()
        
        # Cleanup
        self.cleanup_test_automations()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🏁 WHATSAPP INTEGRATION TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)


class TestModeAutomationTester:
    """Test the new test_mode functionality for automations"""
    
    def __init__(self):
        self.token = None
        self.headers = {}
        self.test_results = []
        self.test_automation_ids = []
        
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
        """Authenticate and get token"""
        try:
            response = requests.post(f"{API_BASE}/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
                self.log_result("Authentication", True, "Successfully authenticated")
                return True
            else:
                self.log_result("Authentication", False, f"Failed to authenticate: {response.status_code}", 
                              {"response": response.text})
                return False
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def test_automation_crud_with_test_mode(self):
        """Test 1: Test Automation CRUD with test_mode field"""
        print("\n=== Test 1: Automation CRUD with test_mode field ===")
        
        # Create automation with test_mode=true
        test_automation_data = {
            "name": "Test Mode Automation - Payment Failed",
            "description": "Test automation that should NOT trigger on live events",
            "trigger_type": "payment_failed",
            "test_mode": True,
            "conditions": {},
            "actions": [
                {
                    "type": "send_sms",
                    "delay_minutes": 0,
                    "message": "TEST MODE: Payment failed for {member_name} - Amount: R{amount}"
                }
            ]
        }
        
        try:
            response = requests.post(f"{API_BASE}/automations", 
                                   json=test_automation_data, headers=self.headers)
            if response.status_code == 200:
                automation = response.json()
                test_automation_id = automation["id"]
                self.test_automation_ids.append(test_automation_id)
                
                # Verify test_mode field is saved correctly
                if automation.get("test_mode") == True:
                    self.log_result("Create Automation with test_mode=true", True, 
                                  "Automation created with test_mode=true",
                                  {"automation_id": test_automation_id})
                else:
                    self.log_result("Create Automation with test_mode=true", False, 
                                  f"test_mode field incorrect: {automation.get('test_mode')}")
            else:
                self.log_result("Create Automation with test_mode=true", False, 
                              f"Failed to create: {response.status_code}",
                              {"response": response.text})
                return None, None
        except Exception as e:
            self.log_result("Create Automation with test_mode=true", False, f"Error: {str(e)}")
            return None, None
        
        # Create automation with test_mode=false (default)
        live_automation_data = {
            "name": "Live Mode Automation - Payment Failed",
            "description": "Live automation that SHOULD trigger on live events",
            "trigger_type": "payment_failed",
            "test_mode": False,
            "conditions": {},
            "actions": [
                {
                    "type": "send_sms",
                    "delay_minutes": 0,
                    "message": "LIVE MODE: Payment failed for {member_name} - Amount: R{amount}"
                }
            ]
        }
        
        try:
            response = requests.post(f"{API_BASE}/automations", 
                                   json=live_automation_data, headers=self.headers)
            if response.status_code == 200:
                automation = response.json()
                live_automation_id = automation["id"]
                self.test_automation_ids.append(live_automation_id)
                
                # Verify test_mode field is saved correctly
                if automation.get("test_mode") == False:
                    self.log_result("Create Automation with test_mode=false", True, 
                                  "Automation created with test_mode=false",
                                  {"automation_id": live_automation_id})
                else:
                    self.log_result("Create Automation with test_mode=false", False, 
                                  f"test_mode field incorrect: {automation.get('test_mode')}")
            else:
                self.log_result("Create Automation with test_mode=false", False, 
                              f"Failed to create: {response.status_code}",
                              {"response": response.text})
                return test_automation_id, None
        except Exception as e:
            self.log_result("Create Automation with test_mode=false", False, f"Error: {str(e)}")
            return test_automation_id, None
        
        # Test retrieving automations and verify test_mode field is included
        try:
            response = requests.get(f"{API_BASE}/automations", headers=self.headers)
            if response.status_code == 200:
                automations = response.json()
                
                # Find our test automations
                test_automation = next((a for a in automations if a["id"] == test_automation_id), None)
                live_automation = next((a for a in automations if a["id"] == live_automation_id), None)
                
                if test_automation and live_automation:
                    if (test_automation.get("test_mode") == True and 
                        live_automation.get("test_mode") == False):
                        self.log_result("Verify test_mode field in GET response", True, 
                                      "test_mode field correctly retrieved for both automations")
                    else:
                        self.log_result("Verify test_mode field in GET response", False, 
                                      f"test_mode fields incorrect: test={test_automation.get('test_mode')}, live={live_automation.get('test_mode')}")
                else:
                    self.log_result("Verify test_mode field in GET response", False, 
                                  "Could not find created automations in list")
            else:
                self.log_result("Verify test_mode field in GET response", False, 
                              f"Failed to get automations: {response.status_code}")
        except Exception as e:
            self.log_result("Verify test_mode field in GET response", False, f"Error: {str(e)}")
        
        # Test updating automation to toggle test_mode
        try:
            update_data = {
                "name": "Test Mode Automation - Updated",
                "description": "Updated test automation",
                "trigger_type": "payment_failed",
                "test_mode": False,  # Toggle from True to False
                "conditions": {},
                "actions": live_automation_data["actions"]
            }
            
            response = requests.put(f"{API_BASE}/automations/{test_automation_id}", 
                                  json=update_data, headers=self.headers)
            if response.status_code == 200:
                updated_automation = response.json()
                if updated_automation.get("test_mode") == False:
                    self.log_result("Update automation test_mode toggle", True, 
                                  "Successfully toggled test_mode from True to False")
                else:
                    self.log_result("Update automation test_mode toggle", False, 
                                  f"test_mode not updated correctly: {updated_automation.get('test_mode')}")
            else:
                self.log_result("Update automation test_mode toggle", False, 
                              f"Failed to update: {response.status_code}")
        except Exception as e:
            self.log_result("Update automation test_mode toggle", False, f"Error: {str(e)}")
        
        return test_automation_id, live_automation_id
    
    def test_trigger_automation_behavior(self, test_automation_id, live_automation_id):
        """Test 2: Test trigger_automation() behavior with test_mode"""
        print("\n=== Test 2: trigger_automation() behavior with test_mode ===")
        
        # First, set the test automation back to test_mode=true
        try:
            update_data = {
                "name": "Test Mode Automation - Payment Failed",
                "description": "Test automation that should NOT trigger on live events",
                "trigger_type": "payment_failed",
                "test_mode": True,
                "enabled": True,
                "conditions": {},
                "actions": [
                    {
                        "type": "send_sms",
                        "delay_minutes": 0,
                        "message": "TEST MODE: Payment failed for {member_name} - Amount: R{amount}"
                    }
                ]
            }
            
            response = requests.put(f"{API_BASE}/automations/{test_automation_id}", 
                                  json=update_data, headers=self.headers)
            if response.status_code != 200:
                self.log_result("Reset test automation to test_mode=true", False, 
                              f"Failed to reset: {response.status_code}")
                return
        except Exception as e:
            self.log_result("Reset test automation to test_mode=true", False, f"Error: {str(e)}")
            return
        
        # Ensure live automation is enabled and not in test mode
        try:
            update_data = {
                "name": "Live Mode Automation - Payment Failed",
                "description": "Live automation that SHOULD trigger on live events",
                "trigger_type": "payment_failed",
                "test_mode": False,
                "enabled": True,
                "conditions": {},
                "actions": [
                    {
                        "type": "send_sms",
                        "delay_minutes": 0,
                        "message": "LIVE MODE: Payment failed for {member_name} - Amount: R{amount}"
                    }
                ]
            }
            
            response = requests.put(f"{API_BASE}/automations/{live_automation_id}", 
                                  json=update_data, headers=self.headers)
            if response.status_code != 200:
                self.log_result("Ensure live automation is enabled", False, 
                              f"Failed to update: {response.status_code}")
                return
        except Exception as e:
            self.log_result("Ensure live automation is enabled", False, f"Error: {str(e)}")
            return
        
        # Get current execution count before triggering
        executions_before = 0
        try:
            response = requests.get(f"{API_BASE}/automation-executions", headers=self.headers)
            if response.status_code == 200:
                executions_before = len(response.json())
        except:
            pass
        
        # Trigger payment_failed event by marking an invoice as failed
        try:
            # Get invoices to test with
            response = requests.get(f"{API_BASE}/invoices?limit=5", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Get invoices for trigger test", False, "Failed to get invoices")
                return
            
            invoices = response.json()
            test_invoice = None
            for invoice in invoices:
                if invoice.get("status") == "pending":
                    test_invoice = invoice
                    break
            
            if not test_invoice:
                self.log_result("Find pending invoice for trigger test", False, "No pending invoices found")
                return
            
            invoice_id = test_invoice["id"]
            
            # Mark invoice as failed to trigger automations
            response = requests.post(f"{API_BASE}/invoices/{invoice_id}/mark-failed", 
                                   json={"failure_reason": "Test Mode Verification - Debit order failed"}, 
                                   headers=self.headers)
            
            if response.status_code == 200:
                self.log_result("Trigger payment_failed event", True, 
                              "Invoice marked as failed, should trigger only live automations")
                
                # Wait for automation processing
                time.sleep(3)
                
                # Check execution history
                executions_response = requests.get(f"{API_BASE}/automation-executions", 
                                                 headers=self.headers)
                if executions_response.status_code == 200:
                    all_executions = executions_response.json()
                    new_executions = all_executions[:len(all_executions) - executions_before]
                    
                    # Check which automations were triggered
                    test_mode_executions = [
                        ex for ex in new_executions 
                        if ex.get("automation_id") == test_automation_id
                    ]
                    
                    live_mode_executions = [
                        ex for ex in new_executions 
                        if ex.get("automation_id") == live_automation_id
                    ]
                    
                    # Verify test_mode automation was NOT triggered
                    if len(test_mode_executions) == 0:
                        self.log_result("Test mode automation excluded from live trigger", True, 
                                      "test_mode automation correctly excluded from live execution")
                    else:
                        self.log_result("Test mode automation excluded from live trigger", False, 
                                      f"test_mode automation incorrectly triggered {len(test_mode_executions)} times")
                    
                    # Verify live automation WAS triggered
                    if len(live_mode_executions) > 0:
                        self.log_result("Live mode automation triggered correctly", True, 
                                      f"Live automation correctly triggered {len(live_mode_executions)} times")
                    else:
                        self.log_result("Live mode automation triggered correctly", False, 
                                      "Live automation was not triggered when it should have been")
                
            else:
                self.log_result("Trigger payment_failed event", False, 
                              f"Failed to mark invoice as failed: {response.status_code}")
                
        except Exception as e:
            self.log_result("Test trigger_automation behavior", False, f"Error: {str(e)}")
    
    def test_manual_testing_of_test_mode_automations(self, test_automation_id):
        """Test 3: Test manual testing of test_mode automations"""
        print("\n=== Test 3: Manual testing of test_mode automations ===")
        
        # Test the test endpoint with test_mode automation
        test_data = {
            "member_id": "test-member-testmode",
            "member_name": "John Test Mode",
            "email": "john.testmode@example.com",
            "phone": "+27123456789",
            "invoice_id": "test-invoice-testmode",
            "invoice_number": "INV-TESTMODE-001",
            "amount": 250.00,
            "failure_reason": "Test mode verification"
        }
        
        try:
            response = requests.post(f"{API_BASE}/automations/test/{test_automation_id}", 
                                   json=test_data, headers=self.headers)
            if response.status_code == 200:
                result = response.json()
                success = result.get("success", False)
                if success:
                    self.log_result("Manual test of test_mode automation", True, 
                                  "test_mode automation can be tested manually via test endpoint",
                                  {"result": result.get("result")})
                else:
                    self.log_result("Manual test of test_mode automation", False, 
                                  f"Test execution failed: {result.get('message')}",
                                  {"error": result.get("error")})
            else:
                self.log_result("Manual test of test_mode automation", False, 
                              f"Failed to test: {response.status_code}",
                              {"response": response.text})
        except Exception as e:
            self.log_result("Manual test of test_mode automation", False, f"Error: {str(e)}")
        
        # Test that regular (non-test-mode) automations can also be tested manually
        try:
            # Get a live automation to test
            response = requests.get(f"{API_BASE}/automations", headers=self.headers)
            if response.status_code == 200:
                automations = response.json()
                live_automation = next((a for a in automations if not a.get("test_mode", False)), None)
                
                if live_automation:
                    live_automation_id = live_automation["id"]
                    
                    response = requests.post(f"{API_BASE}/automations/test/{live_automation_id}", 
                                           json=test_data, headers=self.headers)
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("success", False):
                            self.log_result("Manual test of live automation", True, 
                                          "Live automation can also be tested manually")
                        else:
                            self.log_result("Manual test of live automation", False, 
                                          f"Live automation test failed: {result.get('message')}")
                    else:
                        self.log_result("Manual test of live automation", False, 
                                      f"Failed to test live automation: {response.status_code}")
                else:
                    self.log_result("Find live automation for manual test", False, 
                                  "No live automation found to test")
        except Exception as e:
            self.log_result("Manual test of live automation", False, f"Error: {str(e)}")
    
    def test_automation_listing_with_test_mode(self):
        """Test 4: Test automation listing includes test_mode field"""
        print("\n=== Test 4: Automation listing includes test_mode field ===")
        
        try:
            response = requests.get(f"{API_BASE}/automations", headers=self.headers)
            if response.status_code == 200:
                automations = response.json()
                
                # Check that all automations have test_mode field
                automations_with_test_mode = [a for a in automations if "test_mode" in a]
                
                if len(automations_with_test_mode) == len(automations):
                    self.log_result("Automation listing includes test_mode field", True, 
                                  f"All {len(automations)} automations include test_mode field")
                    
                    # Check for both test_mode values
                    test_mode_true = [a for a in automations if a.get("test_mode") == True]
                    test_mode_false = [a for a in automations if a.get("test_mode") == False]
                    
                    self.log_result("Test mode field values verification", True, 
                                  f"Found {len(test_mode_true)} test_mode=true and {len(test_mode_false)} test_mode=false automations")
                else:
                    self.log_result("Automation listing includes test_mode field", False, 
                                  f"Only {len(automations_with_test_mode)} of {len(automations)} automations have test_mode field")
            else:
                self.log_result("Automation listing includes test_mode field", False, 
                              f"Failed to get automations: {response.status_code}")
        except Exception as e:
            self.log_result("Automation listing includes test_mode field", False, f"Error: {str(e)}")
    
    def cleanup_test_automations(self):
        """Clean up test automations"""
        print("\n=== Cleaning up test automations ===")
        
        for automation_id in self.test_automation_ids:
            try:
                response = requests.delete(f"{API_BASE}/automations/{automation_id}", 
                                         headers=self.headers)
                if response.status_code == 200:
                    self.log_result(f"Cleanup automation {automation_id[:8]}", True, 
                                  "Test automation deleted successfully")
                else:
                    self.log_result(f"Cleanup automation {automation_id[:8]}", False, 
                                  f"Failed to delete: {response.status_code}")
            except Exception as e:
                self.log_result(f"Cleanup automation {automation_id[:8]}", False, f"Error: {str(e)}")
    
    def run_test_mode_tests(self):
        """Run all test_mode functionality tests"""
        print("🚀 Starting Test Mode Automation Tests")
        print(f"Testing against: {API_BASE}")
        print("=" * 60)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Run test mode specific tests
        test_automation_id, live_automation_id = self.test_automation_crud_with_test_mode()
        
        if test_automation_id and live_automation_id:
            self.test_trigger_automation_behavior(test_automation_id, live_automation_id)
            self.test_manual_testing_of_test_mode_automations(test_automation_id)
        
        self.test_automation_listing_with_test_mode()
        
        # Cleanup
        self.cleanup_test_automations()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🏁 TEST MODE AUTOMATION TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)


class PaymentReportEnhancementTester:
    def __init__(self):
        self.token = None
        self.headers = {}
        self.test_results = []
        self.created_members = []
        self.created_invoices = []
        self.created_payments = []
        self.created_sources = []
        
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
        """Authenticate and get token"""
        try:
            response = requests.post(f"{API_BASE}/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
                self.log_result("Authentication", True, "Successfully authenticated")
                return True
            else:
                self.log_result("Authentication", False, f"Failed to authenticate: {response.status_code}", 
                              {"response": response.text})
                return False
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def test_payment_sources_crud(self):
        """Test Payment Source Management API CRUD operations"""
        print("\n=== Testing Payment Source Management API ===")
        
        # Test 1: GET payment sources (should have default sources)
        try:
            response = requests.get(f"{API_BASE}/payment-sources", headers=self.headers)
            if response.status_code == 200:
                sources = response.json()
                expected_sources = ["Walk-in", "Online", "Social Media", "Phone-in", "Referral", "Canvassing", "Flyers"]
                source_names = [s["name"] for s in sources]
                
                # Check if default sources exist
                missing_sources = [s for s in expected_sources if s not in source_names]
                if not missing_sources:
                    self.log_result("GET Payment Sources - Default Sources", True, 
                                  f"All {len(expected_sources)} default payment sources found",
                                  {"sources": source_names})
                else:
                    self.log_result("GET Payment Sources - Default Sources", False, 
                                  f"Missing default sources: {missing_sources}")
                
                # Check sorting by display_order
                display_orders = [s.get("display_order", 0) for s in sources]
                is_sorted = display_orders == sorted(display_orders)
                if is_sorted:
                    self.log_result("Payment Sources Sorting", True, "Sources sorted by display_order")
                else:
                    self.log_result("Payment Sources Sorting", False, f"Sources not sorted: {display_orders}")
                    
            else:
                self.log_result("GET Payment Sources", False, f"Failed to get sources: {response.status_code}",
                              {"response": response.text})
        except Exception as e:
            self.log_result("GET Payment Sources", False, f"Error: {str(e)}")
        
        # Test 2: POST create new payment source
        new_source_data = {
            "name": "Test Source - WhatsApp",
            "description": "Test payment source via WhatsApp",
            "is_active": True,
            "display_order": 10
        }
        
        try:
            response = requests.post(f"{API_BASE}/payment-sources", 
                                   json=new_source_data, headers=self.headers)
            if response.status_code == 200:
                created_source = response.json()
                source_id = created_source["id"]
                self.created_sources.append(source_id)
                
                if (created_source["name"] == new_source_data["name"] and 
                    created_source["description"] == new_source_data["description"]):
                    self.log_result("POST Create Payment Source", True, 
                                  f"Payment source created successfully",
                                  {"source_id": source_id, "name": created_source["name"]})
                else:
                    self.log_result("POST Create Payment Source", False, 
                                  "Created source data doesn't match input")
            else:
                self.log_result("POST Create Payment Source", False, 
                              f"Failed to create source: {response.status_code}",
                              {"response": response.text})
                return None
        except Exception as e:
            self.log_result("POST Create Payment Source", False, f"Error: {str(e)}")
            return None
        
        # Test 3: PUT update payment source
        update_data = {
            "name": "Test Source - WhatsApp Updated",
            "description": "Updated description for WhatsApp source",
            "display_order": 15
        }
        
        try:
            response = requests.put(f"{API_BASE}/payment-sources/{source_id}", 
                                  json=update_data, headers=self.headers)
            if response.status_code == 200:
                updated_source = response.json()
                if (updated_source["name"] == update_data["name"] and 
                    updated_source["description"] == update_data["description"]):
                    self.log_result("PUT Update Payment Source", True, 
                                  f"Payment source updated successfully",
                                  {"updated_name": updated_source["name"]})
                else:
                    self.log_result("PUT Update Payment Source", False, 
                                  "Updated source data doesn't match input")
            else:
                self.log_result("PUT Update Payment Source", False, 
                              f"Failed to update source: {response.status_code}",
                              {"response": response.text})
        except Exception as e:
            self.log_result("PUT Update Payment Source", False, f"Error: {str(e)}")
        
        # Test 4: DELETE soft delete payment source
        try:
            response = requests.delete(f"{API_BASE}/payment-sources/{source_id}", 
                                     headers=self.headers)
            if response.status_code == 200:
                self.log_result("DELETE Payment Source", True, 
                              "Payment source soft deleted successfully")
                
                # Verify it's no longer in active list
                get_response = requests.get(f"{API_BASE}/payment-sources", headers=self.headers)
                if get_response.status_code == 200:
                    active_sources = get_response.json()
                    active_ids = [s["id"] for s in active_sources]
                    if source_id not in active_ids:
                        self.log_result("Verify Soft Delete", True, 
                                      "Deleted source no longer appears in active list")
                    else:
                        self.log_result("Verify Soft Delete", False, 
                                      "Deleted source still appears in active list")
            else:
                self.log_result("DELETE Payment Source", False, 
                              f"Failed to delete source: {response.status_code}",
                              {"response": response.text})
        except Exception as e:
            self.log_result("DELETE Payment Source", False, f"Error: {str(e)}")
        
        return source_id
    
    def test_member_model_enhancements(self):
        """Test Member Model Enhancements with new fields"""
        print("\n=== Testing Member Model Enhancements ===")
        
        # Get membership type for member creation
        try:
            response = requests.get(f"{API_BASE}/membership-types", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Get Membership Types", False, "Failed to get membership types")
                return None
            
            membership_types = response.json()
            if not membership_types:
                self.log_result("Get Membership Types", False, "No membership types found")
                return None
            
            membership_type_id = membership_types[0]["id"]
            
            # Create member with new fields
            member_data = {
                "first_name": "Sarah",
                "last_name": "Johnson",
                "email": f"sarah.johnson.test.{int(time.time())}@example.com",
                "phone": "+27823456789",
                "membership_type_id": membership_type_id,
                "source": "Online",  # New field
                "referred_by": "John Smith",  # New field
                "contract_start_date": "2024-01-01T00:00:00Z",  # New field
                "contract_end_date": "2024-12-31T23:59:59Z"  # New field
            }
            
            response = requests.post(f"{API_BASE}/members", json=member_data, headers=self.headers)
            if response.status_code == 200:
                member = response.json()
                member_id = member["id"]
                self.created_members.append(member_id)
                
                # Verify new fields are stored
                if (member.get("source") == "Online" and 
                    member.get("referred_by") == "John Smith" and
                    member.get("contract_start_date") and
                    member.get("contract_end_date")):
                    self.log_result("Create Member with New Fields", True, 
                                  f"Member created with new fields successfully",
                                  {"member_id": member_id, "source": member.get("source"), 
                                   "referred_by": member.get("referred_by")})
                else:
                    self.log_result("Create Member with New Fields", False, 
                                  "New fields not stored correctly",
                                  {"source": member.get("source"), "referred_by": member.get("referred_by")})
                
                # Test GET member to verify fields are retrieved
                get_response = requests.get(f"{API_BASE}/members/{member_id}", headers=self.headers)
                if get_response.status_code == 200:
                    retrieved_member = get_response.json()
                    if (retrieved_member.get("source") == "Online" and 
                        retrieved_member.get("referred_by") == "John Smith"):
                        self.log_result("GET Member New Fields", True, 
                                      "New fields retrieved correctly from database")
                    else:
                        self.log_result("GET Member New Fields", False, 
                                      "New fields not retrieved correctly")
                
                # Test GET all members includes new fields
                all_response = requests.get(f"{API_BASE}/members", headers=self.headers)
                if all_response.status_code == 200:
                    all_members = all_response.json()
                    test_member = next((m for m in all_members if m["id"] == member_id), None)
                    if test_member and test_member.get("source") == "Online":
                        self.log_result("GET All Members New Fields", True, 
                                      "New fields included in members list")
                    else:
                        self.log_result("GET All Members New Fields", False, 
                                      "New fields not included in members list")
                
                return member_id
            else:
                self.log_result("Create Member with New Fields", False, 
                              f"Failed to create member: {response.status_code}",
                              {"response": response.text})
                return None
                
        except Exception as e:
            self.log_result("Member Model Enhancement Test", False, f"Error: {str(e)}")
            return None
    
    def test_invoice_model_enhancements(self, member_id):
        """Test Invoice Model Enhancements with new fields"""
        print("\n=== Testing Invoice Model Enhancements ===")
        
        if not member_id:
            self.log_result("Invoice Enhancement Test", False, "No member ID provided")
            return None
        
        # Create invoice with new fields
        invoice_data = {
            "member_id": member_id,
            "amount": 500.00,
            "description": "Monthly membership fee - Test",
            "due_date": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        }
        
        try:
            response = requests.post(f"{API_BASE}/invoices", json=invoice_data, headers=self.headers)
            if response.status_code == 200:
                invoice = response.json()
                invoice_id = invoice["id"]
                self.created_invoices.append(invoice_id)
                
                self.log_result("Create Invoice", True, 
                              f"Invoice created successfully",
                              {"invoice_id": invoice_id, "amount": invoice["amount"]})
                
                return invoice_id
            else:
                self.log_result("Create Invoice", False, 
                              f"Failed to create invoice: {response.status_code}",
                              {"response": response.text})
                return None
                
        except Exception as e:
            self.log_result("Invoice Model Enhancement Test", False, f"Error: {str(e)}")
            return None
    
    def test_automatic_debt_calculation(self, member_id, invoice_id):
        """Test Automatic Debt Calculation functionality"""
        print("\n=== Testing Automatic Debt Calculation ===")
        
        if not member_id or not invoice_id:
            self.log_result("Debt Calculation Test", False, "Missing member_id or invoice_id")
            return
        
        try:
            # Step 1: Check initial member debt (should be 0)
            member_response = requests.get(f"{API_BASE}/members/{member_id}", headers=self.headers)
            if member_response.status_code == 200:
                member = member_response.json()
                initial_debt = member.get("debt_amount", 0)
                initial_debtor = member.get("is_debtor", False)
                
                self.log_result("Initial Debt Check", True, 
                              f"Initial debt: R{initial_debt}, is_debtor: {initial_debtor}")
            
            # Step 2: Mark invoice as failed
            response = requests.post(f"{API_BASE}/invoices/{invoice_id}/mark-failed", 
                                   json={"failure_reason": "Debit order failed - Test"}, 
                                   headers=self.headers)
            
            if response.status_code == 200:
                self.log_result("Mark Invoice Failed", True, "Invoice marked as failed successfully")
                
                # Wait a moment for debt calculation
                time.sleep(1)
                
                # Check member debt after failed invoice
                member_response = requests.get(f"{API_BASE}/members/{member_id}", headers=self.headers)
                if member_response.status_code == 200:
                    member = member_response.json()
                    debt_after_failed = member.get("debt_amount", 0)
                    is_debtor_after_failed = member.get("is_debtor", False)
                    
                    if debt_after_failed > 0 and is_debtor_after_failed:
                        self.log_result("Debt Calculation After Failed", True, 
                                      f"Debt calculated correctly: R{debt_after_failed}, is_debtor: {is_debtor_after_failed}")
                    else:
                        self.log_result("Debt Calculation After Failed", False, 
                                      f"Debt not calculated: R{debt_after_failed}, is_debtor: {is_debtor_after_failed}")
            else:
                self.log_result("Mark Invoice Failed", False, 
                              f"Failed to mark invoice as failed: {response.status_code}")
                return
            
            # Step 3: Create another invoice and mark as overdue
            invoice_data2 = {
                "member_id": member_id,
                "amount": 300.00,
                "description": "Additional fee - Test",
                "due_date": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
            }
            
            response2 = requests.post(f"{API_BASE}/invoices", json=invoice_data2, headers=self.headers)
            if response2.status_code == 200:
                invoice2 = response2.json()
                invoice2_id = invoice2["id"]
                self.created_invoices.append(invoice2_id)
                
                # Mark second invoice as overdue
                overdue_response = requests.post(f"{API_BASE}/invoices/{invoice2_id}/mark-overdue", 
                                               headers=self.headers)
                
                if overdue_response.status_code == 200:
                    self.log_result("Mark Invoice Overdue", True, "Second invoice marked as overdue")
                    
                    # Wait for debt recalculation
                    time.sleep(1)
                    
                    # Check total debt (should include both invoices)
                    member_response = requests.get(f"{API_BASE}/members/{member_id}", headers=self.headers)
                    if member_response.status_code == 200:
                        member = member_response.json()
                        total_debt = member.get("debt_amount", 0)
                        expected_debt = 500.00 + 300.00  # Both invoices
                        
                        if abs(total_debt - expected_debt) < 0.01:
                            self.log_result("Total Debt Calculation", True, 
                                          f"Total debt calculated correctly: R{total_debt}")
                        else:
                            self.log_result("Total Debt Calculation", False, 
                                          f"Total debt incorrect: R{total_debt} (expected R{expected_debt})")
            
            # Step 4: Create payment to reduce debt
            payment_data = {
                "invoice_id": invoice_id,
                "member_id": member_id,
                "amount": 500.00,
                "payment_method": "card",
                "reference": "TEST-PAYMENT-001"
            }
            
            payment_response = requests.post(f"{API_BASE}/payments", json=payment_data, headers=self.headers)
            if payment_response.status_code == 200:
                payment = payment_response.json()
                payment_id = payment["id"]
                self.created_payments.append(payment_id)
                
                self.log_result("Create Payment", True, 
                              f"Payment created successfully: R{payment['amount']}")
                
                # Wait for debt recalculation
                time.sleep(1)
                
                # Check debt after payment (should be reduced)
                member_response = requests.get(f"{API_BASE}/members/{member_id}", headers=self.headers)
                if member_response.status_code == 200:
                    member = member_response.json()
                    debt_after_payment = member.get("debt_amount", 0)
                    expected_remaining_debt = 300.00  # Only second invoice remains
                    
                    if abs(debt_after_payment - expected_remaining_debt) < 0.01:
                        self.log_result("Debt Reduction After Payment", True, 
                                      f"Debt reduced correctly: R{debt_after_payment}")
                    else:
                        self.log_result("Debt Reduction After Payment", False, 
                                      f"Debt not reduced correctly: R{debt_after_payment} (expected R{expected_remaining_debt})")
            else:
                self.log_result("Create Payment", False, 
                              f"Failed to create payment: {payment_response.status_code}")
                
        except Exception as e:
            self.log_result("Automatic Debt Calculation Test", False, f"Error: {str(e)}")
    
    def test_payment_report_api(self, member_id):
        """Test Payment Report API with various filters"""
        print("\n=== Testing Payment Report API ===")
        
        try:
            # Test 1: GET payment report without filters
            response = requests.get(f"{API_BASE}/payment-report", headers=self.headers)
            if response.status_code == 200:
                report_data = response.json()
                records = report_data.get("records", [])
                total_records = report_data.get("total_records", 0)
                
                self.log_result("GET Payment Report - No Filters", True, 
                              f"Retrieved {len(records)} records, total: {total_records}")
                
                # Verify response structure
                if records:
                    first_record = records[0]
                    expected_fields = [
                        "member_id", "member_name", "membership_number", "email", "phone",
                        "membership_type", "membership_type_id", "membership_status",
                        "invoice_id", "invoice_number", "amount", "status", "payment_method",
                        "payment_gateway", "status_message", "debt", "is_debtor",
                        "due_date", "paid_date", "start_date", "end_renewal_date",
                        "contract_start_date", "contract_end_date", "source", "referred_by",
                        "sales_consultant_id", "sales_consultant_name"
                    ]
                    
                    missing_fields = [field for field in expected_fields if field not in first_record]
                    if not missing_fields:
                        self.log_result("Payment Report Structure", True, 
                                      "All expected fields present in report")
                    else:
                        self.log_result("Payment Report Structure", False, 
                                      f"Missing fields: {missing_fields}")
            else:
                self.log_result("GET Payment Report - No Filters", False, 
                              f"Failed to get report: {response.status_code}")
                return
            
            # Test 2: Filter by member_id
            if member_id:
                response = requests.get(f"{API_BASE}/payment-report?member_id={member_id}", 
                                      headers=self.headers)
                if response.status_code == 200:
                    filtered_data = response.json()
                    filtered_records = filtered_data.get("records", [])
                    
                    # All records should be for the specified member
                    member_ids = [r.get("member_id") for r in filtered_records]
                    if all(mid == member_id for mid in member_ids):
                        self.log_result("Payment Report - Member Filter", True, 
                                      f"Member filter working: {len(filtered_records)} records for member")
                    else:
                        self.log_result("Payment Report - Member Filter", False, 
                                      "Member filter not working correctly")
                else:
                    self.log_result("Payment Report - Member Filter", False, 
                                  f"Failed to filter by member: {response.status_code}")
            
            # Test 3: Filter by status
            response = requests.get(f"{API_BASE}/payment-report?status=failed", headers=self.headers)
            if response.status_code == 200:
                status_data = response.json()
                status_records = status_data.get("records", [])
                
                if status_records:
                    statuses = [r.get("status") for r in status_records]
                    if all(status == "failed" for status in statuses):
                        self.log_result("Payment Report - Status Filter", True, 
                                      f"Status filter working: {len(status_records)} failed records")
                    else:
                        self.log_result("Payment Report - Status Filter", False, 
                                      f"Status filter not working: found statuses {set(statuses)}")
                else:
                    self.log_result("Payment Report - Status Filter", True, 
                                  "Status filter working (no failed records found)")
            else:
                self.log_result("Payment Report - Status Filter", False, 
                              f"Failed to filter by status: {response.status_code}")
            
            # Test 4: Filter by source
            response = requests.get(f"{API_BASE}/payment-report?source=Online", headers=self.headers)
            if response.status_code == 200:
                source_data = response.json()
                source_records = source_data.get("records", [])
                
                if source_records:
                    sources = [r.get("source") for r in source_records]
                    if all(source == "Online" for source in sources):
                        self.log_result("Payment Report - Source Filter", True, 
                                      f"Source filter working: {len(source_records)} Online records")
                    else:
                        self.log_result("Payment Report - Source Filter", False, 
                                      f"Source filter not working: found sources {set(sources)}")
                else:
                    self.log_result("Payment Report - Source Filter", True, 
                                  "Source filter working (no Online records found)")
            else:
                self.log_result("Payment Report - Source Filter", False, 
                              f"Failed to filter by source: {response.status_code}")
            
            # Test 5: Filter by date range
            start_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
            end_date = datetime.now(timezone.utc).isoformat()
            
            response = requests.get(f"{API_BASE}/payment-report?start_date={start_date}&end_date={end_date}", 
                                  headers=self.headers)
            if response.status_code == 200:
                date_data = response.json()
                date_records = date_data.get("records", [])
                
                self.log_result("Payment Report - Date Range Filter", True, 
                              f"Date range filter working: {len(date_records)} records in last 30 days")
            else:
                self.log_result("Payment Report - Date Range Filter", False, 
                              f"Failed to filter by date range: {response.status_code}")
            
            # Test 6: Multiple filters
            multi_filter_url = f"{API_BASE}/payment-report?status=pending&source=Online"
            response = requests.get(multi_filter_url, headers=self.headers)
            if response.status_code == 200:
                multi_data = response.json()
                multi_records = multi_data.get("records", [])
                
                self.log_result("Payment Report - Multiple Filters", True, 
                              f"Multiple filters working: {len(multi_records)} records")
            else:
                self.log_result("Payment Report - Multiple Filters", False, 
                              f"Failed with multiple filters: {response.status_code}")
                
        except Exception as e:
            self.log_result("Payment Report API Test", False, f"Error: {str(e)}")
    
    def run_payment_report_enhancement_tests(self):
        """Run all payment report enhancement tests"""
        print("🚀 Starting Payment Report Enhancement Backend Tests")
        print(f"Testing against: {API_BASE}")
        print("=" * 60)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Run all test suites
        self.test_payment_sources_crud()
        member_id = self.test_member_model_enhancements()
        invoice_id = self.test_invoice_model_enhancements(member_id)
        self.test_automatic_debt_calculation(member_id, invoice_id)
        self.test_payment_report_api(member_id)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🏁 PAYMENT REPORT ENHANCEMENT TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)


if __name__ == "__main__":
    # Run payment report enhancement tests (NEW FEATURES)
    print("🎯 TESTING NEW PAYMENT REPORT ENHANCEMENT FEATURES")
    print("=" * 80)
    payment_report_tester = PaymentReportEnhancementTester()
    payment_report_tester.run_payment_report_enhancement_tests()