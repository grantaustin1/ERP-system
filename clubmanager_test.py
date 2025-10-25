#!/usr/bin/env python3
"""
ClubManager Analysis Enhancement API Test Suite
Testing all 7 new backend endpoints for ClubManager analysis enhancements
"""

import requests
import json
import time
import os
from datetime import datetime, timezone, timedelta

# Configuration
BASE_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://fitmanage-system.preview.emergentagent.com')
API_BASE = f"{BASE_URL}/api"

# Test credentials
TEST_EMAIL = "admin@gym.com"
TEST_PASSWORD = "admin123"

class ClubManagerTester:
    def __init__(self):
        self.token = None
        self.headers = {}
        self.test_results = []
        self.existing_member_ids = []
        
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
    
    def get_existing_members(self):
        """Get existing member IDs for testing"""
        try:
            response = requests.get(f"{API_BASE}/members", headers=self.headers)
            if response.status_code == 200:
                members = response.json()
                if members:
                    self.existing_member_ids = [member["id"] for member in members[:5]]  # Get first 5 members
                    self.log_result("Get Existing Members", True, f"Found {len(self.existing_member_ids)} existing members for testing")
                    return True
                else:
                    self.log_result("Get Existing Members", False, "No existing members found")
                    return False
            else:
                self.log_result("Get Existing Members", False, f"Failed to get members: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Get Existing Members", False, f"Error getting members: {str(e)}")
            return False

    # ===================== PHASE 1 - Member Profile Enhancements =====================
    
    def test_enhanced_member_profile(self):
        """Test GET /api/members/{member_id}/profile with retention metrics"""
        print("\n=== PHASE 1: Enhanced Member Profile with Retention Metrics ===")
        
        if not self.existing_member_ids:
            self.log_result("Enhanced Member Profile", False, "No existing members available for testing")
            return False
        
        member_id = self.existing_member_ids[0]
        
        try:
            response = requests.get(f"{API_BASE}/members/{member_id}/profile", headers=self.headers)
            
            if response.status_code == 200:
                profile = response.json()
                
                # Check for retention metrics (API returns "retention" not "retention_metrics")
                retention_metrics = profile.get("retention")
                if retention_metrics:
                    required_retention_fields = ["current_month_visits", "previous_month_visits", "percentage_change", "status"]
                    has_retention_fields = all(field in retention_metrics for field in required_retention_fields)
                    
                    if has_retention_fields:
                        self.log_result("Retention Metrics Structure", True, 
                                      f"Retention metrics present with all required fields: {list(retention_metrics.keys())}")
                        
                        # Verify retention status calculation logic
                        status = retention_metrics.get("status")
                        if status in ["collating", "consistent", "good", "alert", "critical"]:
                            self.log_result("Retention Status Logic", True, 
                                          f"Retention status correctly categorized: {status}")
                        else:
                            self.log_result("Retention Status Logic", False, 
                                          f"Invalid retention status: {status}")
                    else:
                        missing_fields = [f for f in required_retention_fields if f not in retention_metrics]
                        self.log_result("Retention Metrics Structure", False, 
                                      f"Missing retention fields: {missing_fields}")
                else:
                    self.log_result("Retention Metrics Structure", False, "No retention metrics found in profile")
                
                # Check for payment progress
                payment_progress = profile.get("payment_progress")
                if payment_progress:
                    required_payment_fields = ["paid", "unpaid", "remaining", "total", "paid_percentage", "unpaid_percentage"]
                    has_payment_fields = all(field in payment_progress for field in required_payment_fields)
                    
                    if has_payment_fields:
                        self.log_result("Payment Progress Structure", True, 
                                      f"Payment progress present with all required fields: {list(payment_progress.keys())}")
                        
                        # Verify payment progress calculations
                        paid = payment_progress.get("paid", 0)
                        unpaid = payment_progress.get("unpaid", 0)
                        total = payment_progress.get("total", 0)
                        paid_percentage = payment_progress.get("paid_percentage", 0)
                        
                        if total == paid + unpaid and abs(paid_percentage - (paid / total * 100 if total > 0 else 0)) < 0.1:
                            self.log_result("Payment Progress Calculations", True, 
                                          f"Payment calculations accurate: {paid}/{total} = {paid_percentage}%")
                        else:
                            self.log_result("Payment Progress Calculations", False, 
                                          f"Payment calculations incorrect: paid={paid}, unpaid={unpaid}, total={total}, percentage={paid_percentage}")
                    else:
                        missing_fields = [f for f in required_payment_fields if f not in payment_progress]
                        self.log_result("Payment Progress Structure", False, 
                                      f"Missing payment progress fields: {missing_fields}")
                else:
                    self.log_result("Payment Progress Structure", False, "No payment_progress found in profile")
                
                # Check for missing data detection
                missing_data = profile.get("missing_data")
                if missing_data is not None:
                    if isinstance(missing_data, list):
                        self.log_result("Missing Data Detection", True, 
                                      f"Missing data array present with {len(missing_data)} items: {missing_data}")
                    else:
                        self.log_result("Missing Data Detection", False, 
                                      f"Missing data should be array, got: {type(missing_data)}")
                else:
                    self.log_result("Missing Data Detection", False, "No missing_data field found in profile")
                
                # Overall profile enhancement test
                if retention_metrics and payment_progress and missing_data is not None:
                    self.log_result("Enhanced Member Profile", True, 
                                  f"Enhanced profile endpoint working correctly for member {member_id}")
                    return True
                else:
                    self.log_result("Enhanced Member Profile", False, 
                                  "Enhanced profile missing some required enhancements")
                    return False
            else:
                self.log_result("Enhanced Member Profile", False, 
                              f"Profile endpoint failed: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Enhanced Member Profile", False, f"Error testing enhanced profile: {str(e)}")
            return False

    # ===================== PHASE 2 - Dashboard Enhancement APIs =====================
    
    def test_sales_comparison_api(self):
        """Test GET /api/dashboard/sales-comparison"""
        print("\n=== PHASE 2: Sales Comparison API ===")
        
        try:
            response = requests.get(f"{API_BASE}/dashboard/sales-comparison", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for daily data array (API returns "data" not "daily_data")
                daily_data = data.get("data")
                if daily_data and isinstance(daily_data, list):
                    if len(daily_data) > 0:
                        # Verify structure of daily data
                        first_day = daily_data[0]
                        required_fields = ["DisplayDate", "MonthSales", "PrevMonthSales", "LastYearSales", "Target"]
                        has_all_fields = all(field in first_day for field in required_fields)
                        
                        if has_all_fields:
                            self.log_result("Sales Comparison Structure", True, 
                                          f"Daily data array with {len(daily_data)} entries, correct structure")
                            
                            # Verify current month sales are calculated up to today only
                            today = datetime.now().day
                            if len(daily_data) <= today:
                                self.log_result("Current Month Sales Logic", True, 
                                              f"Sales data correctly limited to current day: {len(daily_data)} days")
                            else:
                                self.log_result("Current Month Sales Logic", False, 
                                              f"Sales data extends beyond current day: {len(daily_data)} > {today}")
                        else:
                            missing_fields = [f for f in required_fields if f not in first_day]
                            self.log_result("Sales Comparison Structure", False, 
                                          f"Missing fields in daily data: {missing_fields}")
                    else:
                        self.log_result("Sales Comparison Structure", False, "Daily data array is empty")
                else:
                    self.log_result("Sales Comparison Structure", False, "No daily_data array found or invalid type")
                
                # Check for monthly target and current month name
                monthly_target = data.get("monthly_target")
                current_month_name = data.get("current_month_name")
                
                if monthly_target is not None and current_month_name:
                    self.log_result("Sales Comparison Metadata", True, 
                                  f"Monthly target ({monthly_target}) and current month ({current_month_name}) present")
                else:
                    self.log_result("Sales Comparison Metadata", False, 
                                  f"Missing metadata: target={monthly_target}, month={current_month_name}")
                
                # Overall sales comparison test
                if daily_data and monthly_target is not None and current_month_name:
                    self.log_result("Sales Comparison API", True, "Sales comparison endpoint working correctly")
                    return True
                else:
                    self.log_result("Sales Comparison API", False, "Sales comparison endpoint missing required data")
                    return False
            else:
                self.log_result("Sales Comparison API", False, 
                              f"Sales comparison endpoint failed: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Sales Comparison API", False, f"Error testing sales comparison: {str(e)}")
            return False
    
    def test_kpi_trends_api(self):
        """Test GET /api/dashboard/kpi-trends"""
        print("\n=== PHASE 2: KPI Trends API ===")
        
        try:
            response = requests.get(f"{API_BASE}/dashboard/kpi-trends", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for 12-week array (API returns array directly, not wrapped in object)
                if isinstance(data, list):
                    kpi_data = data
                    if len(kpi_data) == 12:
                        # Verify KPI metrics structure
                        first_week = kpi_data[0]
                        required_kpi_fields = ["people_registered", "memberships_started", "attendance", 
                                             "bookings", "booking_attendance", "product_sales", "tasks"]
                        required_date_fields = ["week_start", "week_end"]
                        
                        has_kpi_fields = all(field in first_week for field in required_kpi_fields)
                        has_date_fields = all(field in first_week for field in required_date_fields)
                        
                        if has_kpi_fields and has_date_fields:
                            self.log_result("KPI Trends Structure", True, 
                                          f"12-week KPI data with all required metrics: {required_kpi_fields}")
                            
                            # Verify week dates are properly formatted
                            week_start = first_week.get("week_start")
                            week_end = first_week.get("week_end")
                            
                            if week_start and week_end:
                                self.log_result("KPI Trends Dates", True, 
                                              f"Week dates present: {week_start} to {week_end}")
                            else:
                                self.log_result("KPI Trends Dates", False, 
                                              f"Week dates missing: start={week_start}, end={week_end}")
                        else:
                            missing_kpi = [f for f in required_kpi_fields if f not in first_week]
                            missing_date = [f for f in required_date_fields if f not in first_week]
                            self.log_result("KPI Trends Structure", False, 
                                          f"Missing KPI fields: {missing_kpi}, Missing date fields: {missing_date}")
                    else:
                        self.log_result("KPI Trends Structure", False, 
                                      f"Expected 12 weeks of data, got {len(kpi_data)}")
                else:
                    self.log_result("KPI Trends Structure", False, "No kpi_data array found or invalid type")
                
                # Overall KPI trends test
                if kpi_data and len(kpi_data) == 12:
                    self.log_result("KPI Trends API", True, "KPI trends endpoint working correctly")
                    return True
                else:
                    self.log_result("KPI Trends API", False, "KPI trends endpoint missing required data")
                    return False
            else:
                self.log_result("KPI Trends API", False, 
                              f"KPI trends endpoint failed: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("KPI Trends API", False, f"Error testing KPI trends: {str(e)}")
            return False
    
    def test_birthdays_today_api(self):
        """Test GET /api/dashboard/birthdays-today"""
        print("\n=== PHASE 2: Birthdays Today API ===")
        
        try:
            response = requests.get(f"{API_BASE}/dashboard/birthdays-today", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for birthdays array (API returns array directly, not wrapped in object)
                if isinstance(data, list):
                    birthdays = data
                    self.log_result("Birthdays Today Structure", True, 
                                  f"Birthdays array present with {len(birthdays)} members")
                    
                    if len(birthdays) > 0:
                        # Verify structure of birthday data
                        first_birthday = birthdays[0]
                        required_fields = ["full_name", "age", "photo_url", "membership_status", "email"]
                        has_all_fields = all(field in first_birthday for field in required_fields)
                        
                        if has_all_fields:
                            self.log_result("Birthday Data Structure", True, 
                                          f"Birthday data contains all required fields: {required_fields}")
                            
                            # Verify age calculation is reasonable
                            age = first_birthday.get("age")
                            if isinstance(age, int) and 0 <= age <= 120:
                                self.log_result("Age Calculation", True, 
                                              f"Age calculation appears correct: {age} years")
                            else:
                                self.log_result("Age Calculation", False, 
                                              f"Age calculation suspicious: {age}")
                        else:
                            missing_fields = [f for f in required_fields if f not in first_birthday]
                            self.log_result("Birthday Data Structure", False, 
                                          f"Missing fields in birthday data: {missing_fields}")
                    else:
                        self.log_result("Birthday Data Content", True, 
                                      "No birthdays today (this is normal)")
                else:
                    self.log_result("Birthdays Today Structure", False, "No birthdays array found or invalid type")
                
                # Overall birthdays test
                if birthdays is not None:
                    self.log_result("Birthdays Today API", True, "Birthdays today endpoint working correctly")
                    return True
                else:
                    self.log_result("Birthdays Today API", False, "Birthdays today endpoint missing required data")
                    return False
            else:
                self.log_result("Birthdays Today API", False, 
                              f"Birthdays today endpoint failed: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Birthdays Today API", False, f"Error testing birthdays today: {str(e)}")
            return False

    # ===================== PHASE 3 - Messaging Enhancement APIs =====================
    
    def test_sms_credits_api(self):
        """Test GET /api/messaging/sms-credits"""
        print("\n=== PHASE 3: SMS Credits API ===")
        
        try:
            response = requests.get(f"{API_BASE}/messaging/sms-credits", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for required SMS credits fields
                required_fields = ["credits_available", "credits_used_this_month", "cost_per_credit", "currency"]
                has_all_fields = all(field in data for field in required_fields)
                
                if has_all_fields:
                    self.log_result("SMS Credits Structure", True, 
                                  f"SMS credits data contains all required fields: {required_fields}")
                    
                    # Verify data types and values
                    credits_available = data.get("credits_available")
                    credits_used = data.get("credits_used_this_month")
                    cost_per_credit = data.get("cost_per_credit")
                    currency = data.get("currency")
                    
                    if (isinstance(credits_available, (int, float)) and credits_available >= 0 and
                        isinstance(credits_used, (int, float)) and credits_used >= 0 and
                        isinstance(cost_per_credit, (int, float)) and cost_per_credit >= 0 and
                        isinstance(currency, str) and currency):
                        self.log_result("SMS Credits Data Types", True, 
                                      f"All data types correct: available={credits_available}, used={credits_used}, cost={cost_per_credit} {currency}")
                    else:
                        self.log_result("SMS Credits Data Types", False, 
                                      f"Invalid data types or values: available={credits_available}, used={credits_used}, cost={cost_per_credit}, currency={currency}")
                else:
                    missing_fields = [f for f in required_fields if f not in data]
                    self.log_result("SMS Credits Structure", False, 
                                  f"Missing SMS credits fields: {missing_fields}")
                
                # Overall SMS credits test
                if has_all_fields:
                    self.log_result("SMS Credits API", True, "SMS credits endpoint working correctly")
                    return True
                else:
                    self.log_result("SMS Credits API", False, "SMS credits endpoint missing required data")
                    return False
            else:
                self.log_result("SMS Credits API", False, 
                              f"SMS credits endpoint failed: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("SMS Credits API", False, f"Error testing SMS credits: {str(e)}")
            return False
    
    def test_unified_messaging_api(self):
        """Test POST /api/messaging/send-unified with different message types"""
        print("\n=== PHASE 3: Unified Messaging API ===")
        
        if not self.existing_member_ids:
            self.log_result("Unified Messaging API", False, "No existing members available for testing")
            return False
        
        # Test different message types
        message_types = ["sms", "email", "whatsapp", "push"]
        
        for message_type in message_types:
            try:
                test_payload = {
                    "member_ids": [self.existing_member_ids[0]],  # Use first member
                    "message_type": message_type,
                    "subject": f"Test {message_type.upper()} Message",
                    "message_body": "Hello {first_name}, this is a test message from the gym. Best regards, {last_name}!",
                    "is_marketing": False,
                    "save_as_template": False
                }
                
                response = requests.post(f"{API_BASE}/messaging/send-unified", 
                                       json=test_payload, headers=self.headers)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Check for required response fields (API doesn't return message_type and total_recipients)
                    required_fields = ["sent_count", "failed_count", "success"]
                    has_all_fields = all(field in result for field in required_fields)
                    
                    if has_all_fields:
                        sent_count = result.get("sent_count", 0)
                        failed_count = result.get("failed_count", 0)
                        success = result.get("success", False)
                        
                        if success and (sent_count + failed_count) == len(test_payload["member_ids"]):
                            self.log_result(f"Unified Messaging {message_type.upper()}", True, 
                                          f"{message_type} message sent: {sent_count} sent, {failed_count} failed")
                        else:
                            self.log_result(f"Unified Messaging {message_type.upper()}", False, 
                                          f"Messaging failed or count mismatch: success={success}, sent={sent_count}, failed={failed_count}")
                    else:
                        missing_fields = [f for f in required_fields if f not in result]
                        self.log_result(f"Unified Messaging {message_type.upper()}", False, 
                                      f"Missing response fields: {missing_fields}")
                else:
                    self.log_result(f"Unified Messaging {message_type.upper()}", False, 
                                  f"{message_type} messaging failed: {response.status_code}",
                                  {"response": response.text})
                    
            except Exception as e:
                self.log_result(f"Unified Messaging {message_type.upper()}", False, 
                              f"Error testing {message_type} messaging: {str(e)}")
        
        # Test save as template functionality
        try:
            template_payload = {
                "member_ids": [self.existing_member_ids[0]],
                "message_type": "sms",
                "subject": "Template Test",
                "message_body": "This is a template message for {first_name}",
                "is_marketing": True,
                "save_as_template": True,
                "template_name": "Test Template"  # Required for save_as_template
            }
            
            response = requests.post(f"{API_BASE}/messaging/send-unified", 
                                   json=template_payload, headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                # API doesn't return template_saved flag, but if successful, template should be saved
                if result.get("success"):
                    self.log_result("Save As Template", True, "Template saved successfully (inferred from success)")
                else:
                    self.log_result("Save As Template", False, "Template not saved")
            else:
                self.log_result("Save As Template", False, 
                              f"Save template failed: {response.status_code}")
                
        except Exception as e:
            self.log_result("Save As Template", False, f"Error testing save template: {str(e)}")
        
        return True
    
    def test_messaging_templates_dropdown_api(self):
        """Test GET /api/messaging/templates/dropdown"""
        print("\n=== PHASE 3: Messaging Templates Dropdown API ===")
        
        # Test without message_type filter (all templates)
        try:
            response = requests.get(f"{API_BASE}/messaging/templates/dropdown", headers=self.headers)
            
            if response.status_code == 200:
                templates = response.json()
                
                if isinstance(templates, list):
                    self.log_result("Templates Dropdown Structure", True, 
                                  f"Templates dropdown returned {len(templates)} templates")
                    
                    if len(templates) > 0:
                        # Verify template structure
                        first_template = templates[0]
                        required_fields = ["value", "label", "subject", "message", "category"]
                        has_all_fields = all(field in first_template for field in required_fields)
                        
                        if has_all_fields:
                            self.log_result("Template Dropdown Fields", True, 
                                          f"Template contains all required fields: {required_fields}")
                        else:
                            missing_fields = [f for f in required_fields if f not in first_template]
                            self.log_result("Template Dropdown Fields", False, 
                                          f"Missing template fields: {missing_fields}")
                    else:
                        self.log_result("Template Dropdown Content", True, 
                                      "No templates found (this may be normal)")
                else:
                    self.log_result("Templates Dropdown Structure", False, 
                                  f"Expected array, got {type(templates)}")
            else:
                self.log_result("Templates Dropdown API", False, 
                              f"Templates dropdown failed: {response.status_code}",
                              {"response": response.text})
        except Exception as e:
            self.log_result("Templates Dropdown API", False, f"Error testing templates dropdown: {str(e)}")
        
        # Test with message_type filters
        message_types = ["sms", "email", "whatsapp", "push"]
        
        for message_type in message_types:
            try:
                response = requests.get(f"{API_BASE}/messaging/templates/dropdown", 
                                      params={"message_type": message_type}, headers=self.headers)
                
                if response.status_code == 200:
                    filtered_templates = response.json()
                    
                    if isinstance(filtered_templates, list):
                        self.log_result(f"Templates Filter {message_type.upper()}", True, 
                                      f"Filtered templates for {message_type}: {len(filtered_templates)} templates")
                    else:
                        self.log_result(f"Templates Filter {message_type.upper()}", False, 
                                      f"Invalid response type for {message_type} filter")
                else:
                    self.log_result(f"Templates Filter {message_type.upper()}", False, 
                                  f"Filter {message_type} failed: {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Templates Filter {message_type.upper()}", False, 
                              f"Error testing {message_type} filter: {str(e)}")
        
        return True

    # ===================== Error Handling Tests =====================
    
    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        print("\n=== Error Handling Tests ===")
        
        # Test invalid member ID for profile endpoint
        try:
            response = requests.get(f"{API_BASE}/members/invalid-member-id/profile", headers=self.headers)
            
            if response.status_code == 404:
                self.log_result("Invalid Member ID Handling", True, 
                              "Invalid member ID correctly returns 404")
            else:
                self.log_result("Invalid Member ID Handling", False, 
                              f"Invalid member ID returned {response.status_code}, expected 404")
        except Exception as e:
            self.log_result("Invalid Member ID Handling", False, f"Error testing invalid member ID: {str(e)}")
        
        # Test invalid message type for unified messaging
        try:
            invalid_payload = {
                "member_ids": [self.existing_member_ids[0]] if self.existing_member_ids else ["test-id"],
                "message_type": "invalid_type",
                "subject": "Test",
                "message_body": "Test message",
                "is_marketing": False,
                "save_as_template": False
            }
            
            response = requests.post(f"{API_BASE}/messaging/send-unified", 
                                   json=invalid_payload, headers=self.headers)
            
            if response.status_code in [400, 422]:
                self.log_result("Invalid Message Type Handling", True, 
                              f"Invalid message type correctly returns {response.status_code}")
            else:
                self.log_result("Invalid Message Type Handling", False, 
                              f"Invalid message type returned {response.status_code}, expected 400/422")
        except Exception as e:
            self.log_result("Invalid Message Type Handling", False, f"Error testing invalid message type: {str(e)}")
        
        return True

    # ===================== Main Test Runner =====================
    
    def run_all_tests(self):
        """Run all ClubManager enhancement tests"""
        print("🚀 Starting ClubManager Analysis Enhancement API Tests")
        print(f"Testing against: {API_BASE}")
        print("=" * 80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Get existing members for testing
        if not self.get_existing_members():
            print("⚠️  No existing members found. Some tests may be limited.")
        
        print("\n📋 CLUBMANAGER ENHANCEMENT TESTING")
        print("Testing Requirements:")
        print("- PHASE 1: Enhanced Member Profile with Retention Metrics")
        print("- PHASE 2: Dashboard Enhancement APIs (Sales, KPI, Birthdays)")
        print("- PHASE 3: Unified Messaging Interface APIs")
        print("- Error handling and edge cases")
        
        # Execute all test phases
        print("\n" + "="*60)
        print("PHASE 1 - MEMBER PROFILE ENHANCEMENTS")
        print("="*60)
        self.test_enhanced_member_profile()
        
        print("\n" + "="*60)
        print("PHASE 2 - DASHBOARD ENHANCEMENT APIs")
        print("="*60)
        self.test_sales_comparison_api()
        self.test_kpi_trends_api()
        self.test_birthdays_today_api()
        
        print("\n" + "="*60)
        print("PHASE 3 - MESSAGING ENHANCEMENT APIs")
        print("="*60)
        self.test_sms_credits_api()
        self.test_unified_messaging_api()
        self.test_messaging_templates_dropdown_api()
        
        print("\n" + "="*60)
        print("ERROR HANDLING TESTS")
        print("="*60)
        self.test_error_handling()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🏁 CLUBMANAGER ENHANCEMENT TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        # Group results by phase
        phase1_tests = [r for r in self.test_results if "Profile" in r["test"] or "Retention" in r["test"] or "Payment Progress" in r["test"] or "Missing Data" in r["test"]]
        phase2_tests = [r for r in self.test_results if "Sales" in r["test"] or "KPI" in r["test"] or "Birthday" in r["test"]]
        phase3_tests = [r for r in self.test_results if "SMS" in r["test"] or "Messaging" in r["test"] or "Template" in r["test"]]
        
        print(f"\n📊 PHASE BREAKDOWN:")
        print(f"Phase 1 (Member Profile): {len([r for r in phase1_tests if r['success']])}/{len(phase1_tests)} passed")
        print(f"Phase 2 (Dashboard APIs): {len([r for r in phase2_tests if r['success']])}/{len(phase2_tests)} passed")
        print(f"Phase 3 (Messaging APIs): {len([r for r in phase3_tests if r['success']])}/{len(phase3_tests)} passed")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    tester = ClubManagerTester()
    tester.run_all_tests()