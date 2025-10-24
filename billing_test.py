#!/usr/bin/env python3
"""
Backend Test Suite for Billing Automation & Invoice Generation System
Comprehensive testing of billing settings, invoice CRUD, PDF generation, and validation
"""

import requests
import json
import time
import os
from datetime import datetime, timezone, timedelta

# Configuration
BASE_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://fit-manager-pro.preview.emergentagent.com')
API_BASE = f"{BASE_URL}/api"

# Test credentials
TEST_EMAIL = "admin@gym.com"
TEST_PASSWORD = "admin123"

class BillingInvoiceTester:
    def __init__(self):
        self.token = None
        self.headers = {}
        self.test_results = []
        self.created_invoices = []  # Track created invoices for cleanup
        self.created_members = []  # Track created members for cleanup
        self.test_member_id = None
        
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
    
    def setup_test_member(self):
        """Create a test member for invoice testing"""
        try:
            # Get membership types
            response = requests.get(f"{API_BASE}/membership-types", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Get Membership Types", False, "Failed to get membership types")
                return False
            
            membership_types = response.json()
            if not membership_types:
                self.log_result("Get Membership Types", False, "No membership types found")
                return False
            
            membership_type_id = membership_types[0]["id"]
            
            # Create test member
            timestamp = int(time.time())
            member_data = {
                "first_name": "John",
                "last_name": "TestBilling",
                "email": f"john.testbilling.{timestamp}@example.com",
                "phone": f"082555{timestamp % 10000:04d}",
                "membership_type_id": membership_type_id
            }
            
            response = requests.post(f"{API_BASE}/members", json=member_data, headers=self.headers)
            if response.status_code == 200:
                member = response.json()
                self.test_member_id = member["id"]
                self.created_members.append(member["id"])
                self.log_result("Setup Test Member", True, f"Created test member: {self.test_member_id}")
                return True
            else:
                self.log_result("Setup Test Member", False, f"Failed to create test member: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Setup Test Member", False, f"Error creating test member: {str(e)}")
            return False
    
    def test_billing_settings_get_default(self):
        """Test GET /api/billing/settings - Should return default settings if not configured"""
        print("\n=== Testing Billing Settings GET (Default) ===")
        
        try:
            response = requests.get(f"{API_BASE}/billing/settings", headers=self.headers)
            
            if response.status_code == 200:
                settings = response.json()
                
                # Verify default settings structure
                expected_fields = [
                    "auto_email_invoices", "email_on_invoice_created", "email_on_invoice_overdue",
                    "default_tax_rate", "tax_enabled", "invoice_prefix", "invoice_number_format",
                    "company_name", "default_payment_terms_days"
                ]
                
                has_all_fields = all(field in settings for field in expected_fields)
                
                if has_all_fields:
                    self.log_result("Billing Settings GET Default", True, 
                                  f"Retrieved default billing settings with all required fields")
                    return settings
                else:
                    missing_fields = [field for field in expected_fields if field not in settings]
                    self.log_result("Billing Settings GET Default", False, 
                                  f"Missing fields in billing settings: {missing_fields}")
                    return None
            else:
                self.log_result("Billing Settings GET Default", False, 
                              f"Failed to get billing settings: {response.status_code}",
                              {"response": response.text})
                return None
                
        except Exception as e:
            self.log_result("Billing Settings GET Default", False, f"Error getting billing settings: {str(e)}")
            return None
    
    def test_billing_settings_create_update(self):
        """Test POST /api/billing/settings - Create/update billing settings with all fields"""
        print("\n=== Testing Billing Settings POST (Create/Update) ===")
        
        try:
            # Test data with all billing settings fields
            settings_data = {
                "auto_email_invoices": True,
                "email_on_invoice_created": True,
                "email_on_invoice_overdue": True,
                "email_reminder_days_before_due": [7, 3, 1],
                "default_tax_rate": 15.0,
                "tax_enabled": True,
                "tax_number": "VAT123456789",
                "invoice_prefix": "INV",
                "invoice_number_format": "{prefix}-{year}-{sequence}",
                "next_invoice_number": 1,
                "company_name": "Test Gym Ltd",
                "company_address": "123 Fitness Street, Cape Town, 8001",
                "company_phone": "+27 21 123 4567",
                "company_email": "billing@testgym.com",
                "default_payment_terms_days": 30,
                "auto_generate_membership_invoices": False,
                "days_before_renewal_to_invoice": 5
            }
            
            response = requests.post(f"{API_BASE}/billing/settings", 
                                   json=settings_data, headers=self.headers)
            
            if response.status_code == 200:
                updated_settings = response.json()
                
                # Verify all fields were saved correctly
                fields_correct = all(
                    updated_settings.get(key) == value 
                    for key, value in settings_data.items()
                )
                
                if fields_correct:
                    self.log_result("Billing Settings POST", True, 
                                  "Successfully created/updated billing settings with all fields")
                    return True
                else:
                    self.log_result("Billing Settings POST", False, 
                                  "Some billing settings fields not saved correctly")
                    return False
            else:
                self.log_result("Billing Settings POST", False, 
                              f"Failed to create/update billing settings: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Billing Settings POST", False, f"Error creating/updating billing settings: {str(e)}")
            return False
    
    def test_create_invoice_with_line_items(self):
        """Test POST /api/invoices - Create invoice with line items"""
        print("\n=== Testing Create Invoice with Line Items ===")
        
        if not self.test_member_id:
            self.log_result("Create Invoice", False, "No test member available")
            return None
        
        try:
            # Create invoice with multiple line items
            invoice_data = {
                "member_id": self.test_member_id,
                "description": "Monthly Membership and Personal Training",
                "due_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
                "line_items": [
                    {
                        "description": "Monthly Gym Membership",
                        "quantity": 1.0,
                        "unit_price": 500.00,
                        "discount_percent": 10.0,
                        "tax_percent": 15.0
                    },
                    {
                        "description": "Personal Training Sessions (4x)",
                        "quantity": 4.0,
                        "unit_price": 200.00,
                        "discount_percent": 5.0,
                        "tax_percent": 15.0
                    },
                    {
                        "description": "Nutrition Consultation",
                        "quantity": 1.0,
                        "unit_price": 300.00,
                        "discount_percent": 0.0,
                        "tax_percent": 15.0
                    }
                ],
                "notes": "Test invoice with multiple line items"
            }
            
            response = requests.post(f"{API_BASE}/invoices", 
                                   json=invoice_data, headers=self.headers)
            
            if response.status_code == 200:
                invoice = response.json()
                invoice_id = invoice.get("id")
                
                if invoice_id:
                    self.created_invoices.append(invoice_id)
                
                # Verify invoice structure and calculations
                required_fields = [
                    "id", "invoice_number", "member_id", "description", "due_date",
                    "line_items", "subtotal", "tax_total", "discount_total", "amount", "status"
                ]
                
                has_all_fields = all(field in invoice for field in required_fields)
                
                # Verify calculations
                expected_subtotal = (450.00 + 760.00 + 300.00)  # After discounts: 450 + 760 + 300
                expected_tax = expected_subtotal * 0.15  # 15% tax
                expected_total = expected_subtotal + expected_tax
                
                calculations_correct = (
                    abs(invoice.get("subtotal", 0) - expected_subtotal) < 0.01 and
                    abs(invoice.get("tax_total", 0) - expected_tax) < 0.01 and
                    abs(invoice.get("amount", 0) - expected_total) < 0.01
                )
                
                # Verify invoice number format
                invoice_number = invoice.get("invoice_number", "")
                number_format_correct = invoice_number.startswith("INV-") and len(invoice_number) >= 10
                
                if has_all_fields and calculations_correct and number_format_correct:
                    self.log_result("Create Invoice with Line Items", True, 
                                  f"Invoice created successfully: {invoice_number}, Total: R{invoice.get('amount', 0):.2f}")
                    return invoice_id
                else:
                    issues = []
                    if not has_all_fields:
                        issues.append("missing required fields")
                    if not calculations_correct:
                        issues.append("incorrect calculations")
                    if not number_format_correct:
                        issues.append("incorrect invoice number format")
                    
                    self.log_result("Create Invoice with Line Items", False, 
                                  f"Invoice creation issues: {', '.join(issues)}")
                    return None
            else:
                self.log_result("Create Invoice with Line Items", False, 
                              f"Failed to create invoice: {response.status_code}",
                              {"response": response.text})
                return None
                
        except Exception as e:
            self.log_result("Create Invoice with Line Items", False, f"Error creating invoice: {str(e)}")
            return None
    
    def test_get_invoices_list(self):
        """Test GET /api/invoices - List all invoices"""
        print("\n=== Testing Get Invoices List ===")
        
        try:
            response = requests.get(f"{API_BASE}/invoices", headers=self.headers)
            
            if response.status_code == 200:
                invoices = response.json()
                
                if isinstance(invoices, list):
                    self.log_result("Get Invoices List", True, 
                                  f"Retrieved {len(invoices)} invoices successfully")
                    return True
                else:
                    self.log_result("Get Invoices List", False, 
                                  "Response is not a list of invoices")
                    return False
            else:
                self.log_result("Get Invoices List", False, 
                              f"Failed to get invoices: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Get Invoices List", False, f"Error getting invoices: {str(e)}")
            return False
    
    def test_get_invoice_details(self, invoice_id):
        """Test GET /api/invoices/{invoice_id} - Get invoice details with line items"""
        print("\n=== Testing Get Invoice Details ===")
        
        if not invoice_id:
            self.log_result("Get Invoice Details", False, "No invoice ID provided")
            return False
        
        try:
            response = requests.get(f"{API_BASE}/invoices/{invoice_id}", headers=self.headers)
            
            if response.status_code == 200:
                invoice = response.json()
                
                # Verify detailed invoice structure
                required_fields = [
                    "id", "invoice_number", "member_id", "description", "due_date",
                    "line_items", "subtotal", "tax_total", "discount_total", "amount", 
                    "status", "created_at"
                ]
                
                has_all_fields = all(field in invoice for field in required_fields)
                
                # Verify line items structure
                line_items = invoice.get("line_items", [])
                line_items_valid = all(
                    all(field in item for field in ["description", "quantity", "unit_price", "total"])
                    for item in line_items
                )
                
                if has_all_fields and line_items_valid and len(line_items) > 0:
                    self.log_result("Get Invoice Details", True, 
                                  f"Retrieved invoice details with {len(line_items)} line items")
                    return True
                else:
                    issues = []
                    if not has_all_fields:
                        issues.append("missing required fields")
                    if not line_items_valid:
                        issues.append("invalid line items structure")
                    if len(line_items) == 0:
                        issues.append("no line items found")
                    
                    self.log_result("Get Invoice Details", False, 
                                  f"Invoice details issues: {', '.join(issues)}")
                    return False
            else:
                self.log_result("Get Invoice Details", False, 
                              f"Failed to get invoice details: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Get Invoice Details", False, f"Error getting invoice details: {str(e)}")
            return False
    
    def test_update_invoice(self, invoice_id):
        """Test PUT /api/invoices/{invoice_id} - Update invoice"""
        print("\n=== Testing Update Invoice ===")
        
        if not invoice_id:
            self.log_result("Update Invoice", False, "No invoice ID provided")
            return False
        
        try:
            # Update invoice data
            update_data = {
                "description": "UPDATED: Monthly Membership and Personal Training",
                "due_date": (datetime.now(timezone.utc) + timedelta(days=45)).isoformat(),
                "notes": "Updated invoice notes",
                "line_items": [
                    {
                        "description": "Monthly Gym Membership (Updated)",
                        "quantity": 1.0,
                        "unit_price": 550.00,  # Increased price
                        "discount_percent": 15.0,  # Increased discount
                        "tax_percent": 15.0
                    },
                    {
                        "description": "Personal Training Sessions (6x)",  # Increased quantity
                        "quantity": 6.0,
                        "unit_price": 200.00,
                        "discount_percent": 10.0,  # Increased discount
                        "tax_percent": 15.0
                    }
                ]
            }
            
            response = requests.put(f"{API_BASE}/invoices/{invoice_id}", 
                                  json=update_data, headers=self.headers)
            
            if response.status_code == 200:
                updated_invoice = response.json()
                
                # Verify updates were applied
                description_updated = "UPDATED:" in updated_invoice.get("description", "")
                line_items_updated = len(updated_invoice.get("line_items", [])) == 2
                
                # Verify recalculated totals
                has_recalculated_totals = (
                    updated_invoice.get("subtotal", 0) > 0 and
                    updated_invoice.get("tax_total", 0) > 0 and
                    updated_invoice.get("amount", 0) > 0
                )
                
                if description_updated and line_items_updated and has_recalculated_totals:
                    self.log_result("Update Invoice", True, 
                                  f"Invoice updated successfully, new total: R{updated_invoice.get('amount', 0):.2f}")
                    return True
                else:
                    self.log_result("Update Invoice", False, 
                                  "Invoice update did not apply all changes correctly")
                    return False
            else:
                self.log_result("Update Invoice", False, 
                              f"Failed to update invoice: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Update Invoice", False, f"Error updating invoice: {str(e)}")
            return False
    
    def test_invoice_pdf_generation(self, invoice_id):
        """Test GET /api/invoices/{invoice_id}/pdf - Generate PDF"""
        print("\n=== Testing Invoice PDF Generation ===")
        
        if not invoice_id:
            self.log_result("Invoice PDF Generation", False, "No invoice ID provided")
            return False
        
        try:
            response = requests.get(f"{API_BASE}/invoices/{invoice_id}/pdf", headers=self.headers)
            
            if response.status_code == 200:
                # Verify PDF response
                content_type = response.headers.get("content-type", "")
                content_length = len(response.content)
                
                is_pdf = "application/pdf" in content_type or content_length > 1000
                
                if is_pdf:
                    self.log_result("Invoice PDF Generation", True, 
                                  f"PDF generated successfully, size: {content_length} bytes")
                    return True
                else:
                    self.log_result("Invoice PDF Generation", False, 
                                  f"Response does not appear to be a valid PDF: {content_type}")
                    return False
            else:
                self.log_result("Invoice PDF Generation", False, 
                              f"Failed to generate PDF: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Invoice PDF Generation", False, f"Error generating PDF: {str(e)}")
            return False
    
    def test_void_invoice(self, invoice_id):
        """Test DELETE /api/invoices/{invoice_id} - Void invoice"""
        print("\n=== Testing Void Invoice ===")
        
        if not invoice_id:
            self.log_result("Void Invoice", False, "No invoice ID provided")
            return False
        
        try:
            # First, verify invoice is not paid (create a test scenario)
            response = requests.delete(f"{API_BASE}/invoices/{invoice_id}?reason=Testing void functionality", 
                                     headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                
                if "voided successfully" in result.get("message", "").lower():
                    self.log_result("Void Invoice", True, "Invoice voided successfully")
                    
                    # Verify invoice status changed to void
                    check_response = requests.get(f"{API_BASE}/invoices/{invoice_id}", headers=self.headers)
                    if check_response.status_code == 200:
                        invoice = check_response.json()
                        if invoice.get("status") == "void":
                            self.log_result("Void Invoice Status Check", True, "Invoice status updated to 'void'")
                        else:
                            self.log_result("Void Invoice Status Check", False, 
                                          f"Invoice status not updated correctly: {invoice.get('status')}")
                    
                    return True
                else:
                    self.log_result("Void Invoice", False, 
                                  f"Unexpected void response: {result}")
                    return False
            else:
                self.log_result("Void Invoice", False, 
                              f"Failed to void invoice: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Void Invoice", False, f"Error voiding invoice: {str(e)}")
            return False
    
    def test_validation_scenarios(self):
        """Test various validation scenarios"""
        print("\n=== Testing Validation Scenarios ===")
        
        # Test 1: Create invoice without member_id
        try:
            invalid_data = {
                "description": "Test invoice without member",
                "due_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
                "line_items": [
                    {
                        "description": "Test item",
                        "quantity": 1.0,
                        "unit_price": 100.00,
                        "discount_percent": 0.0,
                        "tax_percent": 15.0
                    }
                ]
            }
            
            response = requests.post(f"{API_BASE}/invoices", 
                                   json=invalid_data, headers=self.headers)
            
            if response.status_code in [400, 422]:  # Should fail validation
                self.log_result("Validation - No Member ID", True, 
                              "Correctly rejected invoice without member_id")
            else:
                self.log_result("Validation - No Member ID", False, 
                              f"Should have rejected invoice without member_id: {response.status_code}")
        except Exception as e:
            self.log_result("Validation - No Member ID", False, f"Error testing validation: {str(e)}")
        
        # Test 2: Create invoice without line_items
        try:
            invalid_data = {
                "member_id": self.test_member_id,
                "description": "Test invoice without line items",
                "due_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
                "line_items": []
            }
            
            response = requests.post(f"{API_BASE}/invoices", 
                                   json=invalid_data, headers=self.headers)
            
            if response.status_code in [400, 422]:  # Should fail validation
                self.log_result("Validation - No Line Items", True, 
                              "Correctly rejected invoice without line items")
            else:
                self.log_result("Validation - No Line Items", False, 
                              f"Should have rejected invoice without line items: {response.status_code}")
        except Exception as e:
            self.log_result("Validation - No Line Items", False, f"Error testing validation: {str(e)}")
        
        # Test 3: Create invoice with invalid member_id
        try:
            invalid_data = {
                "member_id": "invalid-member-id-12345",
                "description": "Test invoice with invalid member",
                "due_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
                "line_items": [
                    {
                        "description": "Test item",
                        "quantity": 1.0,
                        "unit_price": 100.00,
                        "discount_percent": 0.0,
                        "tax_percent": 15.0
                    }
                ]
            }
            
            response = requests.post(f"{API_BASE}/invoices", 
                                   json=invalid_data, headers=self.headers)
            
            if response.status_code == 404:  # Should return member not found
                self.log_result("Validation - Invalid Member ID", True, 
                              "Correctly rejected invoice with invalid member_id")
            else:
                self.log_result("Validation - Invalid Member ID", False, 
                              f"Should have rejected invalid member_id: {response.status_code}")
        except Exception as e:
            self.log_result("Validation - Invalid Member ID", False, f"Error testing validation: {str(e)}")
    
    def cleanup_test_data(self):
        """Clean up test data created during testing"""
        print("\n=== Cleaning Up Test Data ===")
        
        # Clean up created invoices (void them)
        for invoice_id in self.created_invoices:
            try:
                response = requests.delete(f"{API_BASE}/invoices/{invoice_id}?reason=Test cleanup", 
                                         headers=self.headers)
                if response.status_code == 200:
                    self.log_result("Cleanup Invoice", True, f"Voided test invoice {invoice_id}")
                else:
                    self.log_result("Cleanup Invoice", False, f"Failed to void invoice {invoice_id}")
            except Exception as e:
                self.log_result("Cleanup Invoice", False, f"Error cleaning up invoice {invoice_id}: {str(e)}")
        
        # Note: We don't delete members as they might be referenced elsewhere
        if self.created_invoices or self.created_members:
            self.log_result("Cleanup Test Data", True, 
                          f"Attempted cleanup of {len(self.created_invoices)} invoices and {len(self.created_members)} members")
    
    def run_all_tests(self):
        """Run all billing and invoice tests"""
        print("🚀 Starting Billing Automation & Invoice Generation System Tests")
        print(f"Testing against: {API_BASE}")
        print("=" * 80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Setup test data
        if not self.setup_test_member():
            print("❌ Failed to setup test member. Cannot proceed with invoice tests.")
            return
        
        # Run all test phases
        print("\n📋 COMPREHENSIVE BILLING & INVOICE TESTING")
        print("Testing Requirements:")
        print("- Authentication: admin@gym.com / admin123")
        print("- Billing Settings API (GET/POST)")
        print("- Invoice CRUD operations with line items")
        print("- Invoice calculations (subtotal, tax, discount, total)")
        print("- Invoice number generation (sequential)")
        print("- PDF generation")
        print("- Validation scenarios")
        print("- Invoice status management (void)")
        
        # Execute all test phases
        print("\n" + "="*60)
        print("PHASE 1: BILLING SETTINGS TESTING")
        print("="*60)
        self.test_billing_settings_get_default()
        self.test_billing_settings_create_update()
        
        print("\n" + "="*60)
        print("PHASE 2: INVOICE CRUD TESTING")
        print("="*60)
        invoice_id = self.test_create_invoice_with_line_items()
        self.test_get_invoices_list()
        
        if invoice_id:
            self.test_get_invoice_details(invoice_id)
            self.test_update_invoice(invoice_id)
            self.test_invoice_pdf_generation(invoice_id)
            # Note: We'll test void at the end so we don't break other tests
        
        print("\n" + "="*60)
        print("PHASE 3: VALIDATION TESTING")
        print("="*60)
        self.test_validation_scenarios()
        
        print("\n" + "="*60)
        print("PHASE 4: INVOICE STATUS MANAGEMENT")
        print("="*60)
        if invoice_id:
            self.test_void_invoice(invoice_id)
        
        # Cleanup
        self.cleanup_test_data()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🏁 BILLING & INVOICE TEST SUMMARY")
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
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    tester = BillingInvoiceTester()
    tester.run_all_tests()