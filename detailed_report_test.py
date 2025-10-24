#!/usr/bin/env python3
"""
Detailed Report Library API Testing - Phase 2C
Comprehensive testing of all report endpoints with detailed validation
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

class DetailedReportTester:
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
        print(f"{status}: {test_name}")
        print(f"   {message}")
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
    
    def test_incomplete_data_report_detailed(self):
        """Detailed test of Incomplete Data Report API"""
        print("\n" + "="*60)
        print("TESTING: GET /api/reports/incomplete-data")
        print("="*60)
        
        try:
            response = requests.get(f"{API_BASE}/reports/incomplete-data", headers=self.headers)
            
            if response.status_code != 200:
                self.log_result("Incomplete Data Report - Status Code", False, 
                              f"Expected 200, got {response.status_code}")
                return False
            
            data = response.json()
            print(f"Response received: {json.dumps(data, indent=2)[:500]}...")
            
            # Test summary statistics
            summary = data.get("summary", {})
            
            # Verify summary structure
            required_summary_fields = [
                "total_members", "members_with_incomplete_data", "completion_rate", 
                "by_priority", "most_common_missing"
            ]
            
            for field in required_summary_fields:
                if field not in summary:
                    self.log_result(f"Incomplete Data - Summary Field {field}", False, 
                                  f"Missing required summary field: {field}")
                    return False
            
            # Test priority distribution
            by_priority = summary.get("by_priority", {})
            priority_levels = ["critical", "high", "medium", "low"]
            
            for level in priority_levels:
                if level not in by_priority:
                    self.log_result(f"Incomplete Data - Priority Level {level}", False, 
                                  f"Missing priority level: {level}")
                    return False
                
                if not isinstance(by_priority[level], int):
                    self.log_result(f"Incomplete Data - Priority Count Type", False, 
                                  f"Priority count for {level} should be integer")
                    return False
            
            self.log_result("Incomplete Data - Priority Distribution", True, 
                          f"Critical: {by_priority['critical']}, High: {by_priority['high']}, "
                          f"Medium: {by_priority['medium']}, Low: {by_priority['low']}")
            
            # Test most common missing fields
            most_common = summary.get("most_common_missing", [])
            if most_common:
                for item in most_common:
                    if "field" not in item or "count" not in item:
                        self.log_result("Incomplete Data - Missing Fields Structure", False, 
                                      "Most common missing fields should have 'field' and 'count'")
                        return False
            
            self.log_result("Incomplete Data - Most Common Missing", True, 
                          f"Found {len(most_common)} common missing field types")
            
            # Test member list structure
            members = data.get("members", [])
            if members:
                member = members[0]
                required_member_fields = [
                    "id", "first_name", "last_name", "full_name", "email", "phone",
                    "membership_status", "missing_fields", "priority", "priority_score"
                ]
                
                for field in required_member_fields:
                    if field not in member:
                        self.log_result(f"Incomplete Data - Member Field {field}", False, 
                                      f"Missing required member field: {field}")
                        return False
                
                # Test priority scoring logic
                priority = member["priority"]
                score = member["priority_score"]
                
                if priority == "Critical" and score < 20:
                    self.log_result("Incomplete Data - Priority Logic Critical", False, 
                                  f"Critical priority should have score ≥20, got {score}")
                    return False
                elif priority == "High" and (score < 10 or score >= 20):
                    self.log_result("Incomplete Data - Priority Logic High", False, 
                                  f"High priority should have score 10-19, got {score}")
                    return False
                elif priority == "Medium" and (score < 5 or score >= 10):
                    self.log_result("Incomplete Data - Priority Logic Medium", False, 
                                  f"Medium priority should have score 5-9, got {score}")
                    return False
                elif priority == "Low" and score >= 5:
                    self.log_result("Incomplete Data - Priority Logic Low", False, 
                                  f"Low priority should have score <5, got {score}")
                    return False
                
                self.log_result("Incomplete Data - Priority Scoring Logic", True, 
                              f"Priority '{priority}' with score {score} is correctly calculated")
                
                # Test missing fields list
                missing_fields = member.get("missing_fields", [])
                if not isinstance(missing_fields, list):
                    self.log_result("Incomplete Data - Missing Fields Type", False, 
                                  "Missing fields should be a list")
                    return False
                
                self.log_result("Incomplete Data - Member Structure", True, 
                              f"Member has {len(missing_fields)} missing fields: {missing_fields[:3]}...")
            
            # Test completion rate calculation
            total = summary.get("total_members", 0)
            incomplete = summary.get("members_with_incomplete_data", 0)
            completion_rate = summary.get("completion_rate", 0)
            
            if total > 0:
                expected_rate = round((total - incomplete) / total * 100, 1)
                if abs(completion_rate - expected_rate) > 0.1:
                    self.log_result("Incomplete Data - Completion Rate Calculation", False, 
                                  f"Expected {expected_rate}%, got {completion_rate}%")
                    return False
            
            self.log_result("Incomplete Data - Completion Rate", True, 
                          f"Completion rate: {completion_rate}% ({total - incomplete}/{total} complete)")
            
            return True
            
        except Exception as e:
            self.log_result("Incomplete Data Report - Exception", False, f"Error: {str(e)}")
            return False
    
    def test_birthday_report_detailed(self):
        """Detailed test of Birthday Report API"""
        print("\n" + "="*60)
        print("TESTING: GET /api/reports/birthdays")
        print("="*60)
        
        try:
            # Test with different days_ahead values
            test_values = [7, 14, 30, 60, 90]
            
            for days in test_values:
                print(f"\nTesting with days_ahead={days}")
                response = requests.get(f"{API_BASE}/reports/birthdays?days_ahead={days}", headers=self.headers)
                
                if response.status_code != 200:
                    self.log_result(f"Birthday Report {days}d - Status Code", False, 
                                  f"Expected 200, got {response.status_code}")
                    return False
                
                data = response.json()
                
                # Test summary structure
                summary = data.get("summary", {})
                required_summary_fields = ["total_upcoming", "date_range", "by_period"]
                
                for field in required_summary_fields:
                    if field not in summary:
                        self.log_result(f"Birthday Report {days}d - Summary Field {field}", False, 
                                      f"Missing summary field: {field}")
                        return False
                
                # Test date range
                date_range = summary.get("date_range", {})
                if date_range.get("days") != days:
                    self.log_result(f"Birthday Report {days}d - Days Parameter", False, 
                                  f"Expected days={days}, got {date_range.get('days')}")
                    return False
                
                # Test period grouping
                by_period = summary.get("by_period", {})
                period_fields = ["this_week", "next_week", "later"]
                
                for field in period_fields:
                    if field not in by_period:
                        self.log_result(f"Birthday Report {days}d - Period Field {field}", False, 
                                      f"Missing period field: {field}")
                        return False
                
                # Test birthdays structure
                birthdays = data.get("birthdays", {})
                birthday_fields = ["this_week", "next_week", "later", "all"]
                
                for field in birthday_fields:
                    if field not in birthdays:
                        self.log_result(f"Birthday Report {days}d - Birthday Field {field}", False, 
                                      f"Missing birthday field: {field}")
                        return False
                
                # Test member structure if birthdays exist
                all_birthdays = birthdays.get("all", [])
                if all_birthdays:
                    member = all_birthdays[0]
                    required_member_fields = [
                        "id", "first_name", "last_name", "full_name", "email", "phone",
                        "date_of_birth", "birthday_date", "age_turning", "days_until"
                    ]
                    
                    for field in required_member_fields:
                        if field not in member:
                            self.log_result(f"Birthday Report {days}d - Member Field {field}", False, 
                                          f"Missing member field: {field}")
                            return False
                    
                    # Test grouping logic
                    days_until = member["days_until"]
                    if days_until <= 7:
                        expected_group = "this_week"
                    elif days_until <= 14:
                        expected_group = "next_week"
                    else:
                        expected_group = "later"
                    
                    if member not in birthdays[expected_group]:
                        self.log_result(f"Birthday Report {days}d - Grouping Logic", False, 
                                      f"Member with {days_until} days should be in {expected_group}")
                        return False
                
                self.log_result(f"Birthday Report {days}d - Structure", True, 
                              f"Found {summary['total_upcoming']} upcoming birthdays")
            
            # Test default parameter
            response = requests.get(f"{API_BASE}/reports/birthdays", headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                if data["summary"]["date_range"]["days"] != 30:
                    self.log_result("Birthday Report - Default Parameter", False, 
                                  f"Default should be 30 days, got {data['summary']['date_range']['days']}")
                    return False
                
                self.log_result("Birthday Report - Default Parameter", True, 
                              "Default days_ahead=30 working correctly")
            
            return True
            
        except Exception as e:
            self.log_result("Birthday Report - Exception", False, f"Error: {str(e)}")
            return False
    
    def test_anniversary_report_detailed(self):
        """Detailed test of Anniversary Report API"""
        print("\n" + "="*60)
        print("TESTING: GET /api/reports/anniversaries")
        print("="*60)
        
        try:
            # Test with different days_ahead values
            test_values = [7, 14, 30, 60, 90]
            
            for days in test_values:
                print(f"\nTesting with days_ahead={days}")
                response = requests.get(f"{API_BASE}/reports/anniversaries?days_ahead={days}", headers=self.headers)
                
                if response.status_code != 200:
                    self.log_result(f"Anniversary Report {days}d - Status Code", False, 
                                  f"Expected 200, got {response.status_code}")
                    return False
                
                data = response.json()
                
                # Test summary structure
                summary = data.get("summary", {})
                required_summary_fields = ["total_upcoming", "date_range", "by_milestone"]
                
                for field in required_summary_fields:
                    if field not in summary:
                        self.log_result(f"Anniversary Report {days}d - Summary Field {field}", False, 
                                      f"Missing summary field: {field}")
                        return False
                
                # Test date range
                date_range = summary.get("date_range", {})
                if date_range.get("days") != days:
                    self.log_result(f"Anniversary Report {days}d - Days Parameter", False, 
                                  f"Expected days={days}, got {date_range.get('days')}")
                    return False
                
                # Test milestone grouping
                by_milestone = summary.get("by_milestone", {})
                milestone_fields = ["1_year", "5_years", "10_plus_years"]
                
                for field in milestone_fields:
                    if field not in by_milestone:
                        self.log_result(f"Anniversary Report {days}d - Milestone Field {field}", False, 
                                      f"Missing milestone field: {field}")
                        return False
                
                # Test anniversaries structure
                anniversaries = data.get("anniversaries", {})
                anniversary_fields = ["by_milestone", "all"]
                
                for field in anniversary_fields:
                    if field not in anniversaries:
                        self.log_result(f"Anniversary Report {days}d - Anniversary Field {field}", False, 
                                      f"Missing anniversary field: {field}")
                        return False
                
                # Test milestone breakdown
                milestone_breakdown = anniversaries.get("by_milestone", {})
                for field in milestone_fields:
                    if field not in milestone_breakdown:
                        self.log_result(f"Anniversary Report {days}d - Milestone Breakdown {field}", False, 
                                      f"Missing milestone breakdown field: {field}")
                        return False
                
                # Test member structure if anniversaries exist
                all_anniversaries = anniversaries.get("all", [])
                if all_anniversaries:
                    member = all_anniversaries[0]
                    required_member_fields = [
                        "id", "first_name", "last_name", "full_name", "email", "phone",
                        "join_date", "anniversary_date", "years_completing", "days_until"
                    ]
                    
                    for field in required_member_fields:
                        if field not in member:
                            self.log_result(f"Anniversary Report {days}d - Member Field {field}", False, 
                                          f"Missing member field: {field}")
                            return False
                    
                    # Test 1+ years filter
                    years_completing = member["years_completing"]
                    if years_completing < 1:
                        self.log_result(f"Anniversary Report {days}d - Years Filter", False, 
                                      f"Only 1+ year members should be included, found {years_completing}")
                        return False
                    
                    # Test milestone grouping logic
                    if years_completing == 1:
                        expected_group = "1_year"
                    elif years_completing == 5:
                        expected_group = "5_years"
                    elif years_completing >= 10:
                        expected_group = "10_plus_years"
                    else:
                        expected_group = None  # Not in any special milestone group
                    
                    if expected_group and member not in milestone_breakdown[expected_group]:
                        self.log_result(f"Anniversary Report {days}d - Milestone Grouping", False, 
                                      f"Member with {years_completing} years should be in {expected_group}")
                        return False
                
                self.log_result(f"Anniversary Report {days}d - Structure", True, 
                              f"Found {summary['total_upcoming']} upcoming anniversaries")
            
            # Test default parameter
            response = requests.get(f"{API_BASE}/reports/anniversaries", headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                if data["summary"]["date_range"]["days"] != 30:
                    self.log_result("Anniversary Report - Default Parameter", False, 
                                  f"Default should be 30 days, got {data['summary']['date_range']['days']}")
                    return False
                
                self.log_result("Anniversary Report - Default Parameter", True, 
                              "Default days_ahead=30 working correctly")
            
            return True
            
        except Exception as e:
            self.log_result("Anniversary Report - Exception", False, f"Error: {str(e)}")
            return False
    
    def run_detailed_tests(self):
        """Run all detailed report tests"""
        print("=" * 80)
        print("DETAILED REPORT LIBRARY API TESTING - PHASE 2C")
        print("=" * 80)
        
        # Authenticate
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Run detailed tests
        test_results = []
        
        test_results.append(self.test_incomplete_data_report_detailed())
        test_results.append(self.test_birthday_report_detailed())
        test_results.append(self.test_anniversary_report_detailed())
        
        # Generate summary
        print("\n" + "=" * 80)
        print("DETAILED TEST RESULTS SUMMARY")
        print("=" * 80)
        
        passed = sum(test_results)
        total = len(test_results)
        
        print(f"\n🎯 DETAILED TESTS: {passed}/{total} PASSED")
        print(f"📈 SUCCESS RATE: {(passed/total)*100:.1f}%")
        
        # Show all results
        print(f"\n📋 ALL TEST RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        return passed == total

def main():
    """Main execution function"""
    tester = DetailedReportTester()
    success = tester.run_detailed_tests()
    
    if success:
        print("\n🎉 ALL DETAILED REPORT TESTS PASSED!")
        exit(0)
    else:
        print("\n💥 SOME DETAILED REPORT TESTS FAILED!")
        exit(1)

if __name__ == "__main__":
    main()