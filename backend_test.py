#!/usr/bin/env python3
"""
Backend Test Suite - Phase 2D Advanced Analytics APIs
Focus on Advanced Analytics backend APIs testing
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

class AdvancedAnalyticsTestRunner:
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
    
    def test_revenue_breakdown_analytics_api(self):
        """Test Revenue Breakdown Analytics API - GET /api/analytics/revenue-breakdown"""
        print("\n=== Testing Revenue Breakdown Analytics API ===")
        
        try:
            # Test with default period (12 months)
            response = requests.get(f"{API_BASE}/analytics/revenue-breakdown", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required structure
                required_fields = ["summary", "by_membership_type", "by_payment_method", "monthly_trend"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Revenue Breakdown Structure", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify summary structure
                summary = data["summary"]
                summary_fields = ["total_revenue", "mrr", "arpu", "active_members"]
                missing_summary_fields = [field for field in summary_fields if field not in summary]
                
                if missing_summary_fields:
                    self.log_result("Revenue Breakdown Summary Structure", False, 
                                  f"Missing summary fields: {missing_summary_fields}")
                    return False
                
                # Verify data types
                if not isinstance(summary["total_revenue"], (int, float)):
                    self.log_result("Revenue Breakdown Total Revenue Type", False, 
                                  "Total revenue should be number")
                    return False
                
                if not isinstance(summary["mrr"], (int, float)):
                    self.log_result("Revenue Breakdown MRR Type", False, 
                                  "MRR should be number")
                    return False
                
                if not isinstance(summary["arpu"], (int, float)):
                    self.log_result("Revenue Breakdown ARPU Type", False, 
                                  "ARPU should be number")
                    return False
                
                if not isinstance(summary["active_members"], int):
                    self.log_result("Revenue Breakdown Active Members Type", False, 
                                  "Active members should be integer")
                    return False
                
                # Verify by_membership_type structure
                if data["by_membership_type"]:
                    membership_type = data["by_membership_type"][0]
                    membership_fields = ["membership_type", "revenue", "percentage", "member_count"]
                    missing_membership_fields = [field for field in membership_fields if field not in membership_type]
                    
                    if missing_membership_fields:
                        self.log_result("Revenue Breakdown Membership Type Structure", False, 
                                      f"Missing membership type fields: {missing_membership_fields}")
                        return False
                
                # Verify by_payment_method structure
                if data["by_payment_method"]:
                    payment_method = data["by_payment_method"][0]
                    payment_fields = ["payment_method", "revenue", "percentage", "transaction_count"]
                    missing_payment_fields = [field for field in payment_fields if field not in payment_method]
                    
                    if missing_payment_fields:
                        self.log_result("Revenue Breakdown Payment Method Structure", False, 
                                      f"Missing payment method fields: {missing_payment_fields}")
                        return False
                
                # Verify monthly_trend structure
                if data["monthly_trend"]:
                    trend = data["monthly_trend"][0]
                    trend_fields = ["month", "revenue", "member_count"]
                    missing_trend_fields = [field for field in trend_fields if field not in trend]
                    
                    if missing_trend_fields:
                        self.log_result("Revenue Breakdown Monthly Trend Structure", False, 
                                      f"Missing monthly trend fields: {missing_trend_fields}")
                        return False
                
                self.log_result("Revenue Breakdown Analytics API (Default)", True, 
                              f"Retrieved revenue breakdown: Total Revenue R{summary['total_revenue']:.2f}, "
                              f"MRR R{summary['mrr']:.2f}, ARPU R{summary['arpu']:.2f}, "
                              f"Active Members {summary['active_members']}")
                
                # Test with different periods
                test_periods = [3, 6, 24]
                for period in test_periods:
                    response = requests.get(f"{API_BASE}/analytics/revenue-breakdown?period_months={period}", headers=self.headers)
                    if response.status_code == 200:
                        period_data = response.json()
                        self.log_result(f"Revenue Breakdown Analytics API ({period}m)", True, 
                                      f"Retrieved {period}-month revenue breakdown successfully")
                    else:
                        self.log_result(f"Revenue Breakdown Analytics API ({period}m)", False, 
                                      f"Failed to get {period}-month revenue breakdown: {response.status_code}")
                        return False
                
                return True
                
            else:
                self.log_result("Revenue Breakdown Analytics API", False, 
                              f"Failed to get revenue breakdown: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Revenue Breakdown Analytics API", False, f"Error testing revenue breakdown API: {str(e)}")
            return False
    
    def test_geographic_distribution_analytics_api(self):
        """Test Geographic Distribution Analytics API - GET /api/analytics/geographic-distribution"""
        print("\n=== Testing Geographic Distribution Analytics API ===")
        
        try:
            response = requests.get(f"{API_BASE}/analytics/geographic-distribution", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required structure
                required_fields = ["summary", "by_postcode", "by_city", "by_state"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Geographic Distribution Structure", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify summary structure
                summary = data["summary"]
                summary_fields = ["total_members", "members_with_postcode", "members_with_city", 
                                "members_with_state", "postcode_coverage", "city_coverage", "state_coverage"]
                missing_summary_fields = [field for field in summary_fields if field not in summary]
                
                if missing_summary_fields:
                    self.log_result("Geographic Distribution Summary Structure", False, 
                                  f"Missing summary fields: {missing_summary_fields}")
                    return False
                
                # Verify data types
                if not isinstance(summary["total_members"], int):
                    self.log_result("Geographic Distribution Total Members Type", False, 
                                  "Total members should be integer")
                    return False
                
                if not isinstance(summary["postcode_coverage"], (int, float)):
                    self.log_result("Geographic Distribution Postcode Coverage Type", False, 
                                  "Postcode coverage should be number")
                    return False
                
                # Verify by_postcode structure (top 20)
                if data["by_postcode"]:
                    postcode = data["by_postcode"][0]
                    postcode_fields = ["postcode", "member_count", "percentage"]
                    missing_postcode_fields = [field for field in postcode_fields if field not in postcode]
                    
                    if missing_postcode_fields:
                        self.log_result("Geographic Distribution Postcode Structure", False, 
                                      f"Missing postcode fields: {missing_postcode_fields}")
                        return False
                    
                    # Verify top 20 limit
                    if len(data["by_postcode"]) > 20:
                        self.log_result("Geographic Distribution Postcode Limit", False, 
                                      f"Should return top 20 postcodes, got {len(data['by_postcode'])}")
                        return False
                
                # Verify by_city structure (top 10)
                if data["by_city"]:
                    city = data["by_city"][0]
                    city_fields = ["city", "member_count", "percentage"]
                    missing_city_fields = [field for field in city_fields if field not in city]
                    
                    if missing_city_fields:
                        self.log_result("Geographic Distribution City Structure", False, 
                                      f"Missing city fields: {missing_city_fields}")
                        return False
                    
                    # Verify top 10 limit
                    if len(data["by_city"]) > 10:
                        self.log_result("Geographic Distribution City Limit", False, 
                                      f"Should return top 10 cities, got {len(data['by_city'])}")
                        return False
                
                # Verify by_state structure
                if data["by_state"]:
                    state = data["by_state"][0]
                    state_fields = ["state", "member_count", "percentage"]
                    missing_state_fields = [field for field in state_fields if field not in state]
                    
                    if missing_state_fields:
                        self.log_result("Geographic Distribution State Structure", False, 
                                      f"Missing state fields: {missing_state_fields}")
                        return False
                
                self.log_result("Geographic Distribution Analytics API", True, 
                              f"Retrieved geographic distribution: {summary['total_members']} total members, "
                              f"Postcode coverage: {summary['postcode_coverage']:.1f}%, "
                              f"City coverage: {summary['city_coverage']:.1f}%, "
                              f"State coverage: {summary['state_coverage']:.1f}%")
                return True
                
            else:
                self.log_result("Geographic Distribution Analytics API", False, 
                              f"Failed to get geographic distribution: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Geographic Distribution Analytics API", False, f"Error testing geographic distribution API: {str(e)}")
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
    
    def run_report_library_tests(self):
        """Run the report library API tests"""
        print("=" * 80)
        print("BACKEND TESTING - PHASE 2C REPORT LIBRARY APIs")
        print("=" * 80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Setup test members (for context, though report APIs work with existing data)
        if not self.setup_test_members():
            print("❌ Failed to setup test members. Cannot proceed with tests.")
            return False
        
        # Step 3: Run REPORT LIBRARY API TESTS
        print("\n" + "=" * 60)
        print("REPORT LIBRARY API TESTS")
        print("=" * 60)
        
        report_results = []
        
        # 1. Authentication Tests
        print("\n🔐 TEST 1: Report API Authentication")
        report_results.append(self.test_report_api_authentication())
        
        # 2. Incomplete Data Report API
        print("\n📊 TEST 2: Incomplete Data Report API")
        report_results.append(self.test_incomplete_data_report_api())
        
        # 3. Birthday Report API (7, 14, 30, 60, 90 days)
        print("\n🎂 TEST 3: Birthday Report API")
        report_results.append(self.test_birthday_report_api())
        
        # 4. Anniversary Report API (7, 14, 30, 60, 90 days)
        print("\n🎉 TEST 4: Anniversary Report API")
        report_results.append(self.test_anniversary_report_api())
        
        # 5. Error Handling Tests
        print("\n⚠️ TEST 5: Report API Error Handling")
        report_results.append(self.test_report_api_error_handling())
        
        # Step 4: Generate Summary
        print("\n" + "=" * 80)
        print("TEST RESULTS SUMMARY")
        print("=" * 80)
        
        report_passed = sum(report_results)
        report_total = len(report_results)
        
        print(f"\n🎯 REPORT LIBRARY TESTS: {report_passed}/{report_total} PASSED")
        print(f"📈 SUCCESS RATE: {(report_passed/report_total)*100:.1f}%")
        
        # Detailed results
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        # Step 5: Cleanup
        self.cleanup_test_data()
        
        # Return success if all report tests passed
        return report_passed == report_total

def main():
    """Main execution function"""
    tester = ReportLibraryTestRunner()
    success = tester.run_report_library_tests()
    
    if success:
        print("\n🎉 ALL REPORT LIBRARY TESTS PASSED!")
        exit(0)
    else:
        print("\n💥 SOME REPORT LIBRARY TESTS FAILED!")
        exit(1)

if __name__ == "__main__":
    main()