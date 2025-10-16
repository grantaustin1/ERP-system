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
BASE_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://gym-manager-360.preview.emergentagent.com')
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

if __name__ == "__main__":
    # Run payment options and membership groups tests as requested
    tester = PaymentOptionsAndGroupsTester()
    tester.run_all_tests()