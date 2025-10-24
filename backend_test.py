#!/usr/bin/env python3
"""
Backend Test Suite - Phase 2B Retention Intelligence APIs
Focus on Retention Intelligence backend APIs testing
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

class RetentionTestRunner:
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
    
    def test_at_risk_members_api(self):
        """Test At-Risk Members API - GET /api/retention/at-risk-members"""
        print("\n=== Testing At-Risk Members API ===")
        
        try:
            response = requests.get(f"{API_BASE}/retention/at-risk-members", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required structure
                required_fields = ["total", "critical", "high", "medium", "members"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("At-Risk Members Structure", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify data types
                if not isinstance(data["total"], int) or not isinstance(data["critical"], int) or \
                   not isinstance(data["high"], int) or not isinstance(data["medium"], int):
                    self.log_result("At-Risk Members Data Types", False, 
                                  "Count fields should be integers")
                    return False
                
                if not isinstance(data["members"], list):
                    self.log_result("At-Risk Members Members Type", False, 
                                  "Members field should be a list")
                    return False
                
                # Verify member structure if members exist
                if data["members"]:
                    member = data["members"][0]
                    member_fields = [
                        "id", "first_name", "last_name", "full_name", "email", 
                        "risk_score", "risk_level", "risk_factors"
                    ]
                    missing_member_fields = [field for field in member_fields if field not in member]
                    
                    if missing_member_fields:
                        self.log_result("At-Risk Members Member Structure", False, 
                                      f"Missing member fields: {missing_member_fields}")
                        return False
                    
                    # Verify risk_level categorization
                    valid_risk_levels = ["critical", "high", "medium"]
                    if member["risk_level"] not in valid_risk_levels:
                        self.log_result("At-Risk Members Risk Level", False, 
                                      f"Invalid risk level: {member['risk_level']}")
                        return False
                    
                    # Verify risk_factors is a list
                    if not isinstance(member["risk_factors"], list):
                        self.log_result("At-Risk Members Risk Factors", False, 
                                      "Risk factors should be a list")
                        return False
                
                # Verify totals match
                calculated_total = data["critical"] + data["high"] + data["medium"]
                if data["total"] != calculated_total:
                    self.log_result("At-Risk Members Total Calculation", False, 
                                  f"Total mismatch: {data['total']} != {calculated_total}")
                    return False
                
                self.log_result("At-Risk Members API", True, 
                              f"Retrieved {data['total']} at-risk members (Critical: {data['critical']}, High: {data['high']}, Medium: {data['medium']})")
                return True
                
            else:
                self.log_result("At-Risk Members API", False, 
                              f"Failed to get at-risk members: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("At-Risk Members API", False, f"Error testing at-risk members API: {str(e)}")
            return False
    
    def test_retention_alerts_api(self):
        """Test Retention Alerts API - GET /api/retention/retention-alerts"""
        print("\n=== Testing Retention Alerts API ===")
        
        try:
            # Test different day periods
            test_periods = [7, 14, 28]
            
            for days in test_periods:
                response = requests.get(f"{API_BASE}/retention/retention-alerts?days={days}", headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verify required structure
                    required_fields = ["alert_type", "days", "total", "members"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_result(f"Retention Alerts {days}d Structure", False, 
                                      f"Missing fields: {missing_fields}")
                        return False
                    
                    # Verify data types
                    if data["days"] != days:
                        self.log_result(f"Retention Alerts {days}d Days Field", False, 
                                      f"Days field mismatch: expected {days}, got {data['days']}")
                        return False
                    
                    if not isinstance(data["total"], int):
                        self.log_result(f"Retention Alerts {days}d Total Type", False, 
                                      "Total should be an integer")
                        return False
                    
                    if not isinstance(data["members"], list):
                        self.log_result(f"Retention Alerts {days}d Members Type", False, 
                                      "Members should be a list")
                        return False
                    
                    # Verify alert_type format
                    expected_alert_type = f"{days}_day_retention_alert"
                    if data["alert_type"] != expected_alert_type:
                        self.log_result(f"Retention Alerts {days}d Alert Type", False, 
                                      f"Expected '{expected_alert_type}', got '{data['alert_type']}'")
                        return False
                    
                    # Verify member structure if members exist
                    if data["members"]:
                        member = data["members"][0]
                        member_fields = [
                            "id", "first_name", "last_name", "full_name", "email", 
                            "last_visit_date", "days_since_visit", "join_date"
                        ]
                        missing_member_fields = [field for field in member_fields if field not in member]
                        
                        if missing_member_fields:
                            self.log_result(f"Retention Alerts {days}d Member Structure", False, 
                                          f"Missing member fields: {missing_member_fields}")
                            return False
                    
                    self.log_result(f"Retention Alerts {days}d API", True, 
                                  f"Retrieved {data['total']} members inactive for {days}+ days")
                else:
                    self.log_result(f"Retention Alerts {days}d API", False, 
                                  f"Failed to get retention alerts: {response.status_code}",
                                  {"response": response.text})
                    return False
            
            return True
                
        except Exception as e:
            self.log_result("Retention Alerts API", False, f"Error testing retention alerts API: {str(e)}")
            return False
    
    def test_sleeping_members_api(self):
        """Test Sleeping Members API - GET /api/retention/sleeping-members"""
        print("\n=== Testing Sleeping Members API ===")
        
        try:
            response = requests.get(f"{API_BASE}/retention/sleeping-members", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required structure
                required_fields = ["total", "members"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Sleeping Members Structure", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify data types
                if not isinstance(data["total"], int):
                    self.log_result("Sleeping Members Total Type", False, 
                                  "Total should be an integer")
                    return False
                
                if not isinstance(data["members"], list):
                    self.log_result("Sleeping Members Members Type", False, 
                                  "Members should be a list")
                    return False
                
                # Verify member structure if members exist
                if data["members"]:
                    member = data["members"][0]
                    member_fields = [
                        "id", "first_name", "last_name", "full_name", "email", 
                        "last_visit_date", "days_sleeping", "join_date", "is_debtor"
                    ]
                    missing_member_fields = [field for field in member_fields if field not in member]
                    
                    if missing_member_fields:
                        self.log_result("Sleeping Members Member Structure", False, 
                                      f"Missing member fields: {missing_member_fields}")
                        return False
                    
                    # Verify days_sleeping calculation
                    days_sleeping = member["days_sleeping"]
                    if days_sleeping != "Never visited" and not isinstance(days_sleeping, int):
                        self.log_result("Sleeping Members Days Sleeping Type", False, 
                                      "Days sleeping should be integer or 'Never visited'")
                        return False
                
                self.log_result("Sleeping Members API", True, 
                              f"Retrieved {data['total']} sleeping members (no attendance in 30+ days)")
                return True
                
            else:
                self.log_result("Sleeping Members API", False, 
                              f"Failed to get sleeping members: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Sleeping Members API", False, f"Error testing sleeping members API: {str(e)}")
            return False
    
    def test_expiring_memberships_api(self):
        """Test Expiring Memberships API - GET /api/retention/expiring-memberships"""
        print("\n=== Testing Expiring Memberships API ===")
        
        try:
            # Test different day periods
            test_periods = [30, 60, 90]
            
            for days in test_periods:
                response = requests.get(f"{API_BASE}/retention/expiring-memberships?days={days}", headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verify required structure
                    required_fields = ["period_days", "total", "members"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_result(f"Expiring Memberships {days}d Structure", False, 
                                      f"Missing fields: {missing_fields}")
                        return False
                    
                    # Verify data types
                    if data["period_days"] != days:
                        self.log_result(f"Expiring Memberships {days}d Period Field", False, 
                                      f"Period field mismatch: expected {days}, got {data['period_days']}")
                        return False
                    
                    if not isinstance(data["total"], int):
                        self.log_result(f"Expiring Memberships {days}d Total Type", False, 
                                      "Total should be an integer")
                        return False
                    
                    if not isinstance(data["members"], list):
                        self.log_result(f"Expiring Memberships {days}d Members Type", False, 
                                      "Members should be a list")
                        return False
                    
                    # Verify member structure if members exist
                    if data["members"]:
                        member = data["members"][0]
                        member_fields = [
                            "id", "first_name", "last_name", "full_name", "email", 
                            "expiry_date", "days_until_expiry", "membership_type", "is_debtor"
                        ]
                        missing_member_fields = [field for field in member_fields if field not in member]
                        
                        if missing_member_fields:
                            self.log_result(f"Expiring Memberships {days}d Member Structure", False, 
                                          f"Missing member fields: {missing_member_fields}")
                            return False
                        
                        # Verify days_until_expiry is calculated correctly
                        if not isinstance(member["days_until_expiry"], int):
                            self.log_result(f"Expiring Memberships {days}d Days Until Expiry Type", False, 
                                          "Days until expiry should be an integer")
                            return False
                    
                    self.log_result(f"Expiring Memberships {days}d API", True, 
                                  f"Retrieved {data['total']} memberships expiring in {days} days")
                else:
                    self.log_result(f"Expiring Memberships {days}d API", False, 
                                  f"Failed to get expiring memberships: {response.status_code}",
                                  {"response": response.text})
                    return False
            
            return True
                
        except Exception as e:
            self.log_result("Expiring Memberships API", False, f"Error testing expiring memberships API: {str(e)}")
            return False
    
    def test_dropoff_analytics_api(self):
        """Test Dropoff Analytics API - GET /api/retention/dropoff-analytics"""
        print("\n=== Testing Dropoff Analytics API ===")
        
        try:
            response = requests.get(f"{API_BASE}/retention/dropoff-analytics", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required structure
                required_fields = [
                    "total_cancelled_members", "members_analyzed", 
                    "average_days_inactive_before_cancel", "distribution", "recommendation"
                ]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Dropoff Analytics Structure", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify data types
                if not isinstance(data["total_cancelled_members"], int):
                    self.log_result("Dropoff Analytics Total Cancelled Type", False, 
                                  "Total cancelled members should be an integer")
                    return False
                
                if not isinstance(data["members_analyzed"], int):
                    self.log_result("Dropoff Analytics Members Analyzed Type", False, 
                                  "Members analyzed should be an integer")
                    return False
                
                if not isinstance(data["average_days_inactive_before_cancel"], (int, float)):
                    self.log_result("Dropoff Analytics Average Days Type", False, 
                                  "Average days should be a number")
                    return False
                
                # Verify distribution structure
                distribution = data["distribution"]
                expected_distribution_keys = ["0-7_days", "8-14_days", "15-30_days", "31-60_days", "60+_days"]
                missing_dist_keys = [key for key in expected_distribution_keys if key not in distribution]
                
                if missing_dist_keys:
                    self.log_result("Dropoff Analytics Distribution Structure", False, 
                                  f"Missing distribution keys: {missing_dist_keys}")
                    return False
                
                # Verify all distribution values are integers
                for key, value in distribution.items():
                    if not isinstance(value, int):
                        self.log_result("Dropoff Analytics Distribution Values", False, 
                                      f"Distribution value for {key} should be integer, got {type(value)}")
                        return False
                
                # Verify recommendation is a string
                if not isinstance(data["recommendation"], str):
                    self.log_result("Dropoff Analytics Recommendation Type", False, 
                                  "Recommendation should be a string")
                    return False
                
                self.log_result("Dropoff Analytics API", True, 
                              f"Analyzed {data['members_analyzed']}/{data['total_cancelled_members']} cancelled members. "
                              f"Average inactive days: {data['average_days_inactive_before_cancel']}")
                return True
                
            else:
                self.log_result("Dropoff Analytics API", False, 
                              f"Failed to get dropoff analytics: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Dropoff Analytics API", False, f"Error testing dropoff analytics API: {str(e)}")
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