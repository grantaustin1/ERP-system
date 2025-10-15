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

if __name__ == "__main__":
    tester = AutomationTester()
    tester.run_all_tests()