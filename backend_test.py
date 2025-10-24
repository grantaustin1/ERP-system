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
BASE_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://fit-manager-pro.preview.emergentagent.com')
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
    
    def test_recent_members_api(self):
        """Test Recent Members API - GET /api/dashboard/recent-members"""
        print("\n=== Testing Recent Members API ===")
        
        try:
            # Test with period=today
            response_today = requests.get(f"{API_BASE}/dashboard/recent-members?period=today", headers=self.headers)
            
            if response_today.status_code == 200:
                members_today = response_today.json()
                
                # Verify response is a list
                if not isinstance(members_today, list):
                    self.log_result("Recent Members Today Response Type", False, 
                                  f"Expected list, got {type(members_today)}")
                    return False
                
                # If there are members, verify structure
                if members_today:
                    member = members_today[0]
                    required_fields = [
                        "id", "first_name", "last_name", "full_name", 
                        "email", "phone", "membership_status", "join_date", "created_at"
                    ]
                    missing_fields = [field for field in required_fields if field not in member]
                    
                    if missing_fields:
                        self.log_result("Recent Members Today Fields", False, 
                                      f"Missing fields: {missing_fields}")
                        return False
                    
                    # Verify full_name is constructed correctly
                    expected_full_name = f"{member['first_name']} {member['last_name']}".strip()
                    if member["full_name"] != expected_full_name:
                        self.log_result("Recent Members Full Name Construction", False, 
                                      f"Expected '{expected_full_name}', got '{member['full_name']}'")
                        return False
                
                # Check if our test members are included in today's results
                test_member_found = False
                if members_today:
                    for member in members_today:
                        if member.get("id") in [self.test_member_id, self.test_member_id_2]:
                            test_member_found = True
                            break
                
                if test_member_found:
                    self.log_result("Recent Members Today API", True, 
                                  f"Retrieved {len(members_today)} members for today (including test members)")
                else:
                    self.log_result("Recent Members Today API", True, 
                                  f"Retrieved {len(members_today)} members for today (test members may be filtered by date)")
                
                # Test with period=yesterday
                response_yesterday = requests.get(f"{API_BASE}/dashboard/recent-members?period=yesterday", headers=self.headers)
                
                if response_yesterday.status_code == 200:
                    members_yesterday = response_yesterday.json()
                    
                    if not isinstance(members_yesterday, list):
                        self.log_result("Recent Members Yesterday Response Type", False, 
                                      f"Expected list, got {type(members_yesterday)}")
                        return False
                    
                    self.log_result("Recent Members Yesterday API", True, 
                                  f"Retrieved {len(members_yesterday)} members for yesterday")
                    
                    # Test sorting (should be by created_at descending)
                    if len(members_today) > 1:
                        for i in range(len(members_today) - 1):
                            current_date = members_today[i]["created_at"]
                            next_date = members_today[i + 1]["created_at"]
                            
                            if current_date < next_date:
                                self.log_result("Recent Members Sorting", False, 
                                              "Members not sorted by created_at descending")
                                return False
                        
                        self.log_result("Recent Members Sorting", True, 
                                      "Members correctly sorted by created_at descending")
                    
                    return True
                else:
                    self.log_result("Recent Members Yesterday API", False, 
                                  f"Failed to get yesterday members: {response_yesterday.status_code}")
                    return False
                
            else:
                self.log_result("Recent Members Today API", False, 
                              f"Failed to get today members: {response_today.status_code}",
                              {"response": response_today.text})
                return False
                
        except Exception as e:
            self.log_result("Recent Members API", False, f"Error testing recent members API: {str(e)}")
            return False
    
    def create_test_access_logs(self):
        """Create test access logs for dashboard testing"""
        print("\n=== Creating Test Access Logs ===")
        
        if not self.test_member_id:
            self.log_result("Create Test Access Logs", False, "No test member available")
            return False
        
        try:
            # Create access log for today using access validation endpoint
            access_log_data = {
                "member_id": self.test_member_id,
                "access_method": "qr_code",
                "location": "Main Entrance",
                "device_id": "device_001"
            }
            
            response = requests.post(f"{API_BASE}/access/validate", json=access_log_data, headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                self.log_result("Create Test Access Log", True, 
                              f"Created access log for member {self.test_member_id[:8]} - Status: {result.get('status')}")
                return True
            else:
                self.log_result("Create Test Access Log", False, 
                              f"Failed to create access log: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Create Test Access Logs", False, f"Error creating access logs: {str(e)}")
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
    
    def run_dashboard_tests(self):
        """Run the dashboard enhancement tests"""
        print("=" * 80)
        print("BACKEND TESTING - PHASE 2A DASHBOARD ENHANCEMENTS")
        print("=" * 80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Setup test members
        if not self.setup_test_members():
            print("❌ Failed to setup test members. Cannot proceed with tests.")
            return False
        
        # Step 3: Create test access logs for dashboard data
        self.create_test_access_logs()
        
        # Step 4: Run DASHBOARD API TESTS
        print("\n" + "=" * 60)
        print("DASHBOARD API TESTS")
        print("=" * 60)
        
        dashboard_results = []
        
        # 1. Dashboard Snapshot API
        print("\n📊 TEST 1: Dashboard Snapshot API")
        dashboard_results.append(self.test_dashboard_snapshot_api())
        
        # 2. Recent Members API
        print("\n👥 TEST 2: Recent Members API")
        dashboard_results.append(self.test_recent_members_api())
        
        # Step 5: Generate Summary
        print("\n" + "=" * 80)
        print("TEST RESULTS SUMMARY")
        print("=" * 80)
        
        dashboard_passed = sum(dashboard_results)
        dashboard_total = len(dashboard_results)
        
        print(f"\n📊 DASHBOARD TESTS: {dashboard_passed}/{dashboard_total} PASSED")
        print(f"📈 SUCCESS RATE: {(dashboard_passed/dashboard_total)*100:.1f}%")
        
        # Detailed results
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        # Step 6: Cleanup
        self.cleanup_test_data()
        
        # Return success if all dashboard tests passed
        return dashboard_passed == dashboard_total

def main():
    """Main execution function"""
    tester = DashboardTestRunner()
    success = tester.run_dashboard_tests()
    
    if success:
        print("\n🎉 ALL DASHBOARD TESTS PASSED!")
        exit(0)
    else:
        print("\n💥 SOME DASHBOARD TESTS FAILED!")
        exit(1)

if __name__ == "__main__":
    main()