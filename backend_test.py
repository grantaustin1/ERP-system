#!/usr/bin/env python3
"""
Backend Test Suite - Phase 2C Report Library APIs
Focus on Report Library backend APIs testing
"""

import requests
import json
import time
import os
from datetime import datetime, timezone, timedelta

# Configuration
BASE_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://fitclub-manager.preview.emergentagent.com')
API_BASE = f"{BASE_URL}/api"

# Test credentials
TEST_EMAIL = "admin@gym.com"
TEST_PASSWORD = "admin123"

class ReportLibraryTestRunner:
    def __init__(self):
        self.token = None
        self.headers = {}
        self.test_results = []
        self.created_members = []  # Track created members for cleanup
        self.created_access_logs = []  # Track created access logs for cleanup
        self.test_member_id = None
        self.test_member_id_2 = None
        
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
    
    def setup_test_members(self):
        """Create test members for dashboard testing"""
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
            
            # Create first test member
            timestamp = int(time.time() * 1000)  # Use milliseconds for more uniqueness
            member_data_1 = {
                "first_name": "Sarah",
                "last_name": f"DashboardTest{timestamp}",
                "email": f"sarah.dashboard.{timestamp}@example.com",
                "phone": f"082333{timestamp % 100000:05d}",
                "membership_type_id": membership_type_id
            }
            
            response = requests.post(f"{API_BASE}/members", json=member_data_1, headers=self.headers)
            if response.status_code == 200:
                member = response.json()
                self.test_member_id = member["id"]
                self.created_members.append(member["id"])
                self.log_result("Setup Test Member 1", True, f"Created test member 1: {self.test_member_id}")
            else:
                self.log_result("Setup Test Member 1", False, f"Failed to create test member 1: {response.status_code}",
                              {"response": response.text})
                return False
            
            # Create second test member
            member_data_2 = {
                "first_name": "Michael",
                "last_name": f"DashboardTest{timestamp}",
                "email": f"michael.dashboard.{timestamp}@example.com",
                "phone": f"082444{timestamp % 100000:05d}",
                "membership_type_id": membership_type_id
            }
            
            response = requests.post(f"{API_BASE}/members", json=member_data_2, headers=self.headers)
            if response.status_code == 200:
                member = response.json()
                self.test_member_id_2 = member["id"]
                self.created_members.append(member["id"])
                self.log_result("Setup Test Member 2", True, f"Created test member 2: {self.test_member_id_2}")
                return True
            else:
                self.log_result("Setup Test Member 2", False, f"Failed to create test member 2: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Setup Test Members", False, f"Error creating test members: {str(e)}")
            return False
    
    def test_incomplete_data_report_api(self):
        """Test Incomplete Data Report API - GET /api/reports/incomplete-data"""
        print("\n=== Testing Incomplete Data Report API ===")
        
        try:
            response = requests.get(f"{API_BASE}/reports/incomplete-data", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required structure
                required_fields = ["summary", "members"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Incomplete Data Report Structure", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify summary structure
                summary = data["summary"]
                summary_fields = [
                    "total_members", "members_with_incomplete_data", "completion_rate", 
                    "by_priority", "most_common_missing"
                ]
                missing_summary_fields = [field for field in summary_fields if field not in summary]
                
                if missing_summary_fields:
                    self.log_result("Incomplete Data Summary Structure", False, 
                                  f"Missing summary fields: {missing_summary_fields}")
                    return False
                
                # Verify priority distribution
                priority_dist = summary["by_priority"]
                priority_fields = ["critical", "high", "medium", "low"]
                missing_priority_fields = [field for field in priority_fields if field not in priority_dist]
                
                if missing_priority_fields:
                    self.log_result("Incomplete Data Priority Structure", False, 
                                  f"Missing priority fields: {missing_priority_fields}")
                    return False
                
                # Verify data types
                if not isinstance(summary["total_members"], int):
                    self.log_result("Incomplete Data Total Members Type", False, 
                                  "Total members should be integer")
                    return False
                
                if not isinstance(summary["members_with_incomplete_data"], int):
                    self.log_result("Incomplete Data Incomplete Count Type", False, 
                                  "Incomplete count should be integer")
                    return False
                
                if not isinstance(summary["completion_rate"], (int, float)):
                    self.log_result("Incomplete Data Completion Rate Type", False, 
                                  "Completion rate should be number")
                    return False
                
                # Verify members structure if members exist
                if data["members"]:
                    member = data["members"][0]
                    member_fields = [
                        "id", "first_name", "last_name", "full_name", "email", "phone",
                        "membership_status", "missing_fields", "priority", "priority_score"
                    ]
                    missing_member_fields = [field for field in member_fields if field not in member]
                    
                    if missing_member_fields:
                        self.log_result("Incomplete Data Member Structure", False, 
                                      f"Missing member fields: {missing_member_fields}")
                        return False
                    
                    # Verify priority calculation logic
                    priority = member["priority"]
                    score = member["priority_score"]
                    
                    if priority == "Critical" and score < 20:
                        self.log_result("Incomplete Data Priority Logic", False, 
                                      f"Critical priority should have score ≥20, got {score}")
                        return False
                    elif priority == "High" and (score < 10 or score >= 20):
                        self.log_result("Incomplete Data Priority Logic", False, 
                                      f"High priority should have score 10-19, got {score}")
                        return False
                    elif priority == "Medium" and (score < 5 or score >= 10):
                        self.log_result("Incomplete Data Priority Logic", False, 
                                      f"Medium priority should have score 5-9, got {score}")
                        return False
                    elif priority == "Low" and score >= 5:
                        self.log_result("Incomplete Data Priority Logic", False, 
                                      f"Low priority should have score <5, got {score}")
                        return False
                    
                    # Verify missing_fields is a list
                    if not isinstance(member["missing_fields"], list):
                        self.log_result("Incomplete Data Missing Fields Type", False, 
                                      "Missing fields should be a list")
                        return False
                
                self.log_result("Incomplete Data Report API", True, 
                              f"Retrieved report: {summary['total_members']} total members, "
                              f"{summary['members_with_incomplete_data']} with incomplete data "
                              f"({summary['completion_rate']}% completion rate)")
                return True
                
            else:
                self.log_result("Incomplete Data Report API", False, 
                              f"Failed to get incomplete data report: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Incomplete Data Report API", False, f"Error testing incomplete data report API: {str(e)}")
            return False
    
    def test_birthday_report_api(self):
        """Test Birthday Report API - GET /api/reports/birthdays"""
        print("\n=== Testing Birthday Report API ===")
        
        try:
            # Test different day periods
            test_periods = [7, 14, 30, 60, 90]
            
            for days in test_periods:
                response = requests.get(f"{API_BASE}/reports/birthdays?days_ahead={days}", headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verify required structure
                    required_fields = ["summary", "birthdays"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_result(f"Birthday Report {days}d Structure", False, 
                                      f"Missing fields: {missing_fields}")
                        return False
                    
                    # Verify summary structure
                    summary = data["summary"]
                    summary_fields = ["total_upcoming", "date_range", "by_period"]
                    missing_summary_fields = [field for field in summary_fields if field not in summary]
                    
                    if missing_summary_fields:
                        self.log_result(f"Birthday Report {days}d Summary Structure", False, 
                                      f"Missing summary fields: {missing_summary_fields}")
                        return False
                    
                    # Verify date_range structure
                    date_range = summary["date_range"]
                    date_range_fields = ["from", "to", "days"]
                    missing_date_fields = [field for field in date_range_fields if field not in date_range]
                    
                    if missing_date_fields:
                        self.log_result(f"Birthday Report {days}d Date Range Structure", False, 
                                      f"Missing date range fields: {missing_date_fields}")
                        return False
                    
                    # Verify days parameter matches
                    if date_range["days"] != days:
                        self.log_result(f"Birthday Report {days}d Days Parameter", False, 
                                      f"Days parameter mismatch: expected {days}, got {date_range['days']}")
                        return False
                    
                    # Verify by_period structure
                    by_period = summary["by_period"]
                    period_fields = ["this_week", "next_week", "later"]
                    missing_period_fields = [field for field in period_fields if field not in by_period]
                    
                    if missing_period_fields:
                        self.log_result(f"Birthday Report {days}d Period Structure", False, 
                                      f"Missing period fields: {missing_period_fields}")
                        return False
                    
                    # Verify birthdays structure
                    birthdays = data["birthdays"]
                    birthday_fields = ["this_week", "next_week", "later", "all"]
                    missing_birthday_fields = [field for field in birthday_fields if field not in birthdays]
                    
                    if missing_birthday_fields:
                        self.log_result(f"Birthday Report {days}d Birthdays Structure", False, 
                                      f"Missing birthday fields: {missing_birthday_fields}")
                        return False
                    
                    # Verify member structure if birthdays exist
                    if birthdays["all"]:
                        member = birthdays["all"][0]
                        member_fields = [
                            "id", "first_name", "last_name", "full_name", "email", "phone",
                            "date_of_birth", "birthday_date", "age_turning", "days_until"
                        ]
                        missing_member_fields = [field for field in member_fields if field not in member]
                        
                        if missing_member_fields:
                            self.log_result(f"Birthday Report {days}d Member Structure", False, 
                                          f"Missing member fields: {missing_member_fields}")
                            return False
                        
                        # Verify grouping logic
                        days_until = member["days_until"]
                        if days_until <= 7 and member not in birthdays["this_week"]:
                            self.log_result(f"Birthday Report {days}d Grouping Logic", False, 
                                          f"Member with {days_until} days should be in this_week")
                            return False
                    
                    # Verify totals match
                    calculated_total = by_period["this_week"] + by_period["next_week"] + by_period["later"]
                    if summary["total_upcoming"] != calculated_total:
                        self.log_result(f"Birthday Report {days}d Total Calculation", False, 
                                      f"Total mismatch: {summary['total_upcoming']} != {calculated_total}")
                        return False
                    
                    self.log_result(f"Birthday Report {days}d API", True, 
                                  f"Retrieved {summary['total_upcoming']} upcoming birthdays "
                                  f"(This week: {by_period['this_week']}, Next week: {by_period['next_week']}, Later: {by_period['later']})")
                else:
                    self.log_result(f"Birthday Report {days}d API", False, 
                                  f"Failed to get birthday report: {response.status_code}",
                                  {"response": response.text})
                    return False
            
            # Test default parameter (30 days)
            response = requests.get(f"{API_BASE}/reports/birthdays", headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                if data["summary"]["date_range"]["days"] != 30:
                    self.log_result("Birthday Report Default Parameter", False, 
                                  f"Default days_ahead should be 30, got {data['summary']['date_range']['days']}")
                    return False
                self.log_result("Birthday Report Default Parameter", True, "Default days_ahead=30 working correctly")
            else:
                self.log_result("Birthday Report Default Parameter", False, 
                              f"Failed to test default parameter: {response.status_code}")
                return False
            
            return True
                
        except Exception as e:
            self.log_result("Birthday Report API", False, f"Error testing birthday report API: {str(e)}")
            return False
    
    def test_anniversary_report_api(self):
        """Test Anniversary Report API - GET /api/reports/anniversaries"""
        print("\n=== Testing Anniversary Report API ===")
        
        try:
            # Test different day periods
            test_periods = [7, 14, 30, 60, 90]
            
            for days in test_periods:
                response = requests.get(f"{API_BASE}/reports/anniversaries?days_ahead={days}", headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verify required structure
                    required_fields = ["summary", "anniversaries"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_result(f"Anniversary Report {days}d Structure", False, 
                                      f"Missing fields: {missing_fields}")
                        return False
                    
                    # Verify summary structure
                    summary = data["summary"]
                    summary_fields = ["total_upcoming", "date_range", "by_milestone"]
                    missing_summary_fields = [field for field in summary_fields if field not in summary]
                    
                    if missing_summary_fields:
                        self.log_result(f"Anniversary Report {days}d Summary Structure", False, 
                                      f"Missing summary fields: {missing_summary_fields}")
                        return False
                    
                    # Verify date_range structure
                    date_range = summary["date_range"]
                    date_range_fields = ["from", "to", "days"]
                    missing_date_fields = [field for field in date_range_fields if field not in date_range]
                    
                    if missing_date_fields:
                        self.log_result(f"Anniversary Report {days}d Date Range Structure", False, 
                                      f"Missing date range fields: {missing_date_fields}")
                        return False
                    
                    # Verify days parameter matches
                    if date_range["days"] != days:
                        self.log_result(f"Anniversary Report {days}d Days Parameter", False, 
                                      f"Days parameter mismatch: expected {days}, got {date_range['days']}")
                        return False
                    
                    # Verify by_milestone structure
                    by_milestone = summary["by_milestone"]
                    milestone_fields = ["1_year", "5_years", "10_plus_years"]
                    missing_milestone_fields = [field for field in milestone_fields if field not in by_milestone]
                    
                    if missing_milestone_fields:
                        self.log_result(f"Anniversary Report {days}d Milestone Structure", False, 
                                      f"Missing milestone fields: {missing_milestone_fields}")
                        return False
                    
                    # Verify anniversaries structure
                    anniversaries = data["anniversaries"]
                    anniversary_fields = ["by_milestone", "all"]
                    missing_anniversary_fields = [field for field in anniversary_fields if field not in anniversaries]
                    
                    if missing_anniversary_fields:
                        self.log_result(f"Anniversary Report {days}d Anniversaries Structure", False, 
                                      f"Missing anniversary fields: {missing_anniversary_fields}")
                        return False
                    
                    # Verify by_milestone breakdown
                    milestone_breakdown = anniversaries["by_milestone"]
                    milestone_breakdown_fields = ["1_year", "5_years", "10_plus_years"]
                    missing_breakdown_fields = [field for field in milestone_breakdown_fields if field not in milestone_breakdown]
                    
                    if missing_breakdown_fields:
                        self.log_result(f"Anniversary Report {days}d Milestone Breakdown", False, 
                                      f"Missing milestone breakdown fields: {missing_breakdown_fields}")
                        return False
                    
                    # Verify member structure if anniversaries exist
                    if anniversaries["all"]:
                        member = anniversaries["all"][0]
                        member_fields = [
                            "id", "first_name", "last_name", "full_name", "email", "phone",
                            "join_date", "anniversary_date", "years_completing", "days_until"
                        ]
                        missing_member_fields = [field for field in member_fields if field not in member]
                        
                        if missing_member_fields:
                            self.log_result(f"Anniversary Report {days}d Member Structure", False, 
                                          f"Missing member fields: {missing_member_fields}")
                            return False
                        
                        # Verify only 1+ year members are included
                        years_completing = member["years_completing"]
                        if years_completing < 1:
                            self.log_result(f"Anniversary Report {days}d Years Filter", False, 
                                          f"Only members with 1+ years should be included, found {years_completing}")
                            return False
                        
                        # Verify milestone grouping logic
                        if years_completing == 1 and member not in milestone_breakdown["1_year"]:
                            self.log_result(f"Anniversary Report {days}d Milestone Grouping", False, 
                                          f"1-year member should be in 1_year group")
                            return False
                        elif years_completing == 5 and member not in milestone_breakdown["5_years"]:
                            self.log_result(f"Anniversary Report {days}d Milestone Grouping", False, 
                                          f"5-year member should be in 5_years group")
                            return False
                        elif years_completing >= 10 and member not in milestone_breakdown["10_plus_years"]:
                            self.log_result(f"Anniversary Report {days}d Milestone Grouping", False, 
                                          f"10+ year member should be in 10_plus_years group")
                            return False
                    
                    # Verify totals match
                    calculated_total = by_milestone["1_year"] + by_milestone["5_years"] + by_milestone["10_plus_years"]
                    if summary["total_upcoming"] != calculated_total:
                        self.log_result(f"Anniversary Report {days}d Total Calculation", False, 
                                      f"Total mismatch: {summary['total_upcoming']} != {calculated_total}")
                        return False
                    
                    self.log_result(f"Anniversary Report {days}d API", True, 
                                  f"Retrieved {summary['total_upcoming']} upcoming anniversaries "
                                  f"(1yr: {by_milestone['1_year']}, 5yr: {by_milestone['5_years']}, 10+yr: {by_milestone['10_plus_years']})")
                else:
                    self.log_result(f"Anniversary Report {days}d API", False, 
                                  f"Failed to get anniversary report: {response.status_code}",
                                  {"response": response.text})
                    return False
            
            # Test default parameter (30 days)
            response = requests.get(f"{API_BASE}/reports/anniversaries", headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                if data["summary"]["date_range"]["days"] != 30:
                    self.log_result("Anniversary Report Default Parameter", False, 
                                  f"Default days_ahead should be 30, got {data['summary']['date_range']['days']}")
                    return False
                self.log_result("Anniversary Report Default Parameter", True, "Default days_ahead=30 working correctly")
            else:
                self.log_result("Anniversary Report Default Parameter", False, 
                              f"Failed to test default parameter: {response.status_code}")
                return False
            
            return True
                
        except Exception as e:
            self.log_result("Anniversary Report API", False, f"Error testing anniversary report API: {str(e)}")
            return False
    
    def test_report_api_authentication(self):
        """Test that all report APIs require authentication"""
        print("\n=== Testing Report API Authentication ===")
        
        try:
            # Test without authentication headers
            endpoints = [
                "/reports/incomplete-data",
                "/reports/birthdays",
                "/reports/anniversaries"
            ]
            
            for endpoint in endpoints:
                response = requests.get(f"{API_BASE}{endpoint}")
                
                if response.status_code != 401:
                    self.log_result(f"Authentication {endpoint}", False, 
                                  f"Expected 401 Unauthorized, got {response.status_code}")
                    return False
                
                self.log_result(f"Authentication {endpoint}", True, 
                              "Correctly requires authentication")
            
            return True
                
        except Exception as e:
            self.log_result("Report API Authentication", False, f"Error testing authentication: {str(e)}")
            return False
    
    def test_report_api_error_handling(self):
        """Test error handling for report APIs"""
        print("\n=== Testing Report API Error Handling ===")
        
        try:
            # Test invalid parameters for birthday report
            response = requests.get(f"{API_BASE}/reports/birthdays?days_ahead=-1", headers=self.headers)
            # Should still work but with reasonable defaults or handle gracefully
            
            # Test invalid parameters for anniversary report  
            response = requests.get(f"{API_BASE}/reports/anniversaries?days_ahead=0", headers=self.headers)
            # Should still work but with reasonable defaults or handle gracefully
            
            # Test very large parameters
            response = requests.get(f"{API_BASE}/reports/birthdays?days_ahead=10000", headers=self.headers)
            if response.status_code == 200:
                self.log_result("Birthday Report Large Parameter", True, "Handles large parameters gracefully")
            else:
                self.log_result("Birthday Report Large Parameter", False, f"Failed with large parameter: {response.status_code}")
                return False
            
            response = requests.get(f"{API_BASE}/reports/anniversaries?days_ahead=10000", headers=self.headers)
            if response.status_code == 200:
                self.log_result("Anniversary Report Large Parameter", True, "Handles large parameters gracefully")
            else:
                self.log_result("Anniversary Report Large Parameter", False, f"Failed with large parameter: {response.status_code}")
                return False
            
            return True
                
        except Exception as e:
            self.log_result("Report API Error Handling", False, f"Error testing error handling: {str(e)}")
            return False
    
    def cleanup_test_data(self):
        """Clean up test data created during testing"""
        print("\n=== Cleaning Up Test Data ===")
        
        # Clean up created members
        for member_id in self.created_members:
            try:
                response = requests.delete(f"{API_BASE}/members/{member_id}", headers=self.headers)
                if response.status_code == 200:
                    self.log_result(f"Cleanup Member {member_id[:8]}", True, "Member deleted")
                else:
                    self.log_result(f"Cleanup Member {member_id[:8]}", False, f"Failed to delete: {response.status_code}")
            except Exception as e:
                self.log_result(f"Cleanup Member {member_id[:8]}", False, f"Error: {str(e)}")
        
        # Clean up created access logs
        for access_log_id in self.created_access_logs:
            try:
                response = requests.delete(f"{API_BASE}/access-logs/{access_log_id}", headers=self.headers)
                if response.status_code == 200:
                    self.log_result(f"Cleanup Access Log {access_log_id[:8]}", True, "Access log deleted")
                else:
                    self.log_result(f"Cleanup Access Log {access_log_id[:8]}", False, f"Failed to delete: {response.status_code}")
            except Exception as e:
                self.log_result(f"Cleanup Access Log {access_log_id[:8]}", False, f"Error: {str(e)}")
    
    def run_retention_tests(self):
        """Run the retention intelligence API tests"""
        print("=" * 80)
        print("BACKEND TESTING - PHASE 2B RETENTION INTELLIGENCE APIs")
        print("=" * 80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Setup test members (for context, though retention APIs work with existing data)
        if not self.setup_test_members():
            print("❌ Failed to setup test members. Cannot proceed with tests.")
            return False
        
        # Step 3: Run RETENTION API TESTS
        print("\n" + "=" * 60)
        print("RETENTION INTELLIGENCE API TESTS")
        print("=" * 60)
        
        retention_results = []
        
        # 1. At-Risk Members API
        print("\n🚨 TEST 1: At-Risk Members API")
        retention_results.append(self.test_at_risk_members_api())
        
        # 2. Retention Alerts API (7, 14, 28 days)
        print("\n⚠️ TEST 2: Retention Alerts API")
        retention_results.append(self.test_retention_alerts_api())
        
        # 3. Sleeping Members API
        print("\n😴 TEST 3: Sleeping Members API")
        retention_results.append(self.test_sleeping_members_api())
        
        # 4. Expiring Memberships API (30, 60, 90 days)
        print("\n⏰ TEST 4: Expiring Memberships API")
        retention_results.append(self.test_expiring_memberships_api())
        
        # 5. Dropoff Analytics API
        print("\n📉 TEST 5: Dropoff Analytics API")
        retention_results.append(self.test_dropoff_analytics_api())
        
        # Step 4: Generate Summary
        print("\n" + "=" * 80)
        print("TEST RESULTS SUMMARY")
        print("=" * 80)
        
        retention_passed = sum(retention_results)
        retention_total = len(retention_results)
        
        print(f"\n🎯 RETENTION TESTS: {retention_passed}/{retention_total} PASSED")
        print(f"📈 SUCCESS RATE: {(retention_passed/retention_total)*100:.1f}%")
        
        # Detailed results
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        # Step 5: Cleanup
        self.cleanup_test_data()
        
        # Return success if all retention tests passed
        return retention_passed == retention_total

def main():
    """Main execution function"""
    tester = RetentionTestRunner()
    success = tester.run_retention_tests()
    
    if success:
        print("\n🎉 ALL RETENTION INTELLIGENCE TESTS PASSED!")
        exit(0)
    else:
        print("\n💥 SOME RETENTION INTELLIGENCE TESTS FAILED!")
        exit(1)

if __name__ == "__main__":
    main()