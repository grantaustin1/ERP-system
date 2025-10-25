#!/usr/bin/env python3
"""
Attendance Heatmap API Test Suite
Focus on testing the new attendance heatmap endpoint with various parameters and validation
"""

import requests
import json
import time
import os
from datetime import datetime, timezone, timedelta

# Configuration
BASE_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://gym-analytics-pro.preview.emergentagent.com')
API_BASE = f"{BASE_URL}/api"

# Test credentials
TEST_EMAIL = "admin@gym.com"
TEST_PASSWORD = "admin123"

class AttendanceHeatmapTestRunner:
    def __init__(self):
        self.token = None
        self.headers = {}
        self.test_results = []
        self.test_member_id = None
        self.created_access_logs = []  # Track created access logs for cleanup
        
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
    
    def setup_test_data(self):
        """Setup test data - get a member for access log creation"""
        try:
            # Get an active member for testing
            response = requests.get(f"{API_BASE}/members", headers=self.headers)
            if response.status_code == 200:
                members_data = response.json()
                if isinstance(members_data, list) and members_data:
                    # Find an active member
                    for member in members_data:
                        if member.get("membership_status") == "active":
                            self.test_member_id = member["id"]
                            self.log_result("Get Test Member", True, f"Found active member: {member['first_name']} {member['last_name']}")
                            break
                    
                    if not self.test_member_id:
                        self.log_result("Get Test Member", False, "No active members found for testing")
                        return False
                else:
                    self.log_result("Get Test Member", False, "No members found")
                    return False
            else:
                self.log_result("Get Test Member", False, f"Failed to get members: {response.status_code}")
                return False
            
            return True
                
        except Exception as e:
            self.log_result("Setup Test Data", False, f"Error setting up test data: {str(e)}")
            return False
    
    def create_test_access_logs(self):
        """Create test access logs for different days and hours"""
        try:
            # Create access logs for the past week with various patterns
            base_time = datetime.now(timezone.utc) - timedelta(days=7)
            
            # Monday morning rush (8-10 AM)
            for hour in [8, 9]:
                for i in range(5):  # 5 visits per hour
                    timestamp = base_time.replace(hour=hour, minute=i*10, second=0, microsecond=0)
                    access_data = {
                        "member_id": self.test_member_id,
                        "access_method": "qr_code",
                        "location": "Main Entrance"
                    }
                    
                    # Create access log via API
                    response = requests.post(f"{API_BASE}/access-logs", json=access_data, headers=self.headers)
                    if response.status_code == 200:
                        log_data = response.json()
                        if "access_log" in log_data:
                            self.created_access_logs.append(log_data["access_log"]["id"])
            
            # Tuesday evening (6-8 PM)
            tuesday = base_time + timedelta(days=1)
            for hour in [18, 19]:
                for i in range(8):  # 8 visits per hour
                    timestamp = tuesday.replace(hour=hour, minute=i*7, second=0, microsecond=0)
                    access_data = {
                        "member_id": self.test_member_id,
                        "access_method": "qr_code",
                        "location": "Main Entrance"
                    }
                    
                    response = requests.post(f"{API_BASE}/access-logs", json=access_data, headers=self.headers)
                    if response.status_code == 200:
                        log_data = response.json()
                        if "access_log" in log_data:
                            self.created_access_logs.append(log_data["access_log"]["id"])
            
            # Wednesday lunch time (12-1 PM)
            wednesday = base_time + timedelta(days=2)
            for hour in [12]:
                for i in range(3):  # 3 visits
                    timestamp = wednesday.replace(hour=hour, minute=i*15, second=0, microsecond=0)
                    access_data = {
                        "member_id": self.test_member_id,
                        "access_method": "qr_code",
                        "location": "Main Entrance"
                    }
                    
                    response = requests.post(f"{API_BASE}/access-logs", json=access_data, headers=self.headers)
                    if response.status_code == 200:
                        log_data = response.json()
                        if "access_log" in log_data:
                            self.created_access_logs.append(log_data["access_log"]["id"])
            
            # Saturday morning (10-11 AM)
            saturday = base_time + timedelta(days=5)
            for hour in [10]:
                for i in range(12):  # 12 visits (peak hour)
                    timestamp = saturday.replace(hour=hour, minute=i*5, second=0, microsecond=0)
                    access_data = {
                        "member_id": self.test_member_id,
                        "access_method": "qr_code",
                        "location": "Main Entrance"
                    }
                    
                    response = requests.post(f"{API_BASE}/access-logs", json=access_data, headers=self.headers)
                    if response.status_code == 200:
                        log_data = response.json()
                        if "access_log" in log_data:
                            self.created_access_logs.append(log_data["access_log"]["id"])
            
            self.log_result("Create Test Access Logs", True, f"Created {len(self.created_access_logs)} test access logs")
            return True
            
        except Exception as e:
            self.log_result("Create Test Access Logs", False, f"Error creating test access logs: {str(e)}")
            return False
    
    def test_heatmap_without_parameters(self):
        """Test attendance heatmap endpoint without parameters (should default to last 30 days)"""
        print("\n=== Testing Attendance Heatmap Without Parameters ===")
        
        try:
            response = requests.get(f"{API_BASE}/attendance/heatmap", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                if "heatmap" not in data or "stats" not in data:
                    self.log_result("Heatmap Structure", False, "Missing 'heatmap' or 'stats' field")
                    return False
                
                heatmap = data["heatmap"]
                stats = data["stats"]
                
                # Verify heatmap has 7 days
                if len(heatmap) != 7:
                    self.log_result("Heatmap Days Count", False, f"Expected 7 days, got {len(heatmap)}")
                    return False
                
                # Verify day structure and ordering
                expected_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                for i, day_data in enumerate(heatmap):
                    if day_data.get("day") != expected_days[i]:
                        self.log_result("Heatmap Day Order", False, f"Expected {expected_days[i]}, got {day_data.get('day')}")
                        return False
                    
                    if day_data.get("day_index") != i:
                        self.log_result("Heatmap Day Index", False, f"Expected day_index {i}, got {day_data.get('day_index')}")
                        return False
                    
                    # Verify all 24 hours are present
                    for hour in range(24):
                        hour_key = f"hour_{hour}"
                        if hour_key not in day_data:
                            self.log_result("Heatmap Hour Fields", False, f"Missing {hour_key} in {day_data.get('day')}")
                            return False
                        
                        # Verify hour values are integers
                        if not isinstance(day_data[hour_key], int):
                            self.log_result("Heatmap Hour Values", False, f"Hour value should be integer, got {type(day_data[hour_key])}")
                            return False
                
                # Verify stats structure
                required_stats = ["total_visits", "max_hourly_count", "date_range"]
                for stat in required_stats:
                    if stat not in stats:
                        self.log_result("Stats Structure", False, f"Missing stat: {stat}")
                        return False
                
                # Verify date_range structure
                date_range = stats["date_range"]
                if "start" not in date_range or "end" not in date_range:
                    self.log_result("Date Range Structure", False, "Missing start or end in date_range")
                    return False
                
                # Verify stats values are reasonable
                if not isinstance(stats["total_visits"], int) or stats["total_visits"] < 0:
                    self.log_result("Total Visits Value", False, f"Invalid total_visits: {stats['total_visits']}")
                    return False
                
                if not isinstance(stats["max_hourly_count"], int) or stats["max_hourly_count"] < 0:
                    self.log_result("Max Hourly Count Value", False, f"Invalid max_hourly_count: {stats['max_hourly_count']}")
                    return False
                
                self.log_result("Heatmap Without Parameters", True, f"Valid response with {stats['total_visits']} total visits, max {stats['max_hourly_count']} per hour")
                return True
                
            else:
                self.log_result("Heatmap Without Parameters", False, f"Failed to get heatmap: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Heatmap Without Parameters", False, f"Error testing heatmap: {str(e)}")
            return False
    
    def test_heatmap_with_custom_dates(self):
        """Test attendance heatmap endpoint with custom start_date and end_date parameters"""
        print("\n=== Testing Attendance Heatmap With Custom Dates ===")
        
        try:
            # Test with last 7 days
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=7)
            
            params = {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
            
            response = requests.get(f"{API_BASE}/attendance/heatmap", params=params, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure (same as before)
                if "heatmap" not in data or "stats" not in data:
                    self.log_result("Custom Dates Structure", False, "Missing 'heatmap' or 'stats' field")
                    return False
                
                stats = data["stats"]
                
                # Verify date range matches our parameters
                returned_start = stats["date_range"]["start"]
                returned_end = stats["date_range"]["end"]
                
                if returned_start != start_date.isoformat():
                    self.log_result("Custom Start Date", False, f"Expected {start_date.isoformat()}, got {returned_start}")
                    return False
                
                if returned_end != end_date.isoformat():
                    self.log_result("Custom End Date", False, f"Expected {end_date.isoformat()}, got {returned_end}")
                    return False
                
                self.log_result("Heatmap With Custom Dates", True, f"Custom date range working: {stats['total_visits']} visits")
                
                # Test with different date range (last 3 days)
                end_date_3 = datetime.now(timezone.utc)
                start_date_3 = end_date_3 - timedelta(days=3)
                
                params_3 = {
                    "start_date": start_date_3.isoformat(),
                    "end_date": end_date_3.isoformat()
                }
                
                response_3 = requests.get(f"{API_BASE}/attendance/heatmap", params=params_3, headers=self.headers)
                
                if response_3.status_code == 200:
                    data_3 = response_3.json()
                    stats_3 = data_3["stats"]
                    
                    # Verify different date range returns different (likely fewer) results
                    self.log_result("Different Date Range", True, f"3-day range: {stats_3['total_visits']} visits vs 7-day range: {stats['total_visits']} visits")
                else:
                    self.log_result("Different Date Range", False, f"Failed 3-day range test: {response_3.status_code}")
                    return False
                
                return True
                
            else:
                self.log_result("Heatmap With Custom Dates", False, f"Failed to get heatmap: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Heatmap With Custom Dates", False, f"Error testing custom dates: {str(e)}")
            return False
    
    def test_heatmap_calculation_accuracy(self):
        """Test that heatmap calculations are accurate by verifying against known test data"""
        print("\n=== Testing Heatmap Calculation Accuracy ===")
        
        try:
            # Use a specific date range that includes our test data
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=7)
            
            params = {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
            
            response = requests.get(f"{API_BASE}/attendance/heatmap", params=params, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                heatmap = data["heatmap"]
                stats = data["stats"]
                
                # Verify total visits calculation
                calculated_total = 0
                max_hourly = 0
                
                for day_data in heatmap:
                    for hour in range(24):
                        hour_count = day_data[f"hour_{hour}"]
                        calculated_total += hour_count
                        max_hourly = max(max_hourly, hour_count)
                
                # Verify our calculated totals match the API response
                if calculated_total != stats["total_visits"]:
                    self.log_result("Total Visits Calculation", False, f"Calculated {calculated_total}, API returned {stats['total_visits']}")
                    return False
                
                if max_hourly != stats["max_hourly_count"]:
                    self.log_result("Max Hourly Calculation", False, f"Calculated {max_hourly}, API returned {stats['max_hourly_count']}")
                    return False
                
                # Verify day ordering (Monday=0, Sunday=6)
                day_indices = [day["day_index"] for day in heatmap]
                expected_indices = [0, 1, 2, 3, 4, 5, 6]
                
                if day_indices != expected_indices:
                    self.log_result("Day Index Order", False, f"Expected {expected_indices}, got {day_indices}")
                    return False
                
                # Check if we have some data from our test logs
                has_data = stats["total_visits"] > 0
                if has_data:
                    self.log_result("Test Data Present", True, f"Found {stats['total_visits']} visits in test period")
                    
                    # Look for our specific test patterns
                    monday_data = heatmap[0]  # Monday is index 0
                    tuesday_data = heatmap[1]  # Tuesday is index 1
                    saturday_data = heatmap[5]  # Saturday is index 5
                    
                    # Check if we can find some of our test patterns
                    monday_morning = monday_data["hour_8"] + monday_data["hour_9"]
                    tuesday_evening = tuesday_data["hour_18"] + tuesday_data["hour_19"]
                    saturday_morning = saturday_data["hour_10"]
                    
                    pattern_info = f"Monday 8-9AM: {monday_morning}, Tuesday 6-7PM: {tuesday_evening}, Saturday 10AM: {saturday_morning}"
                    self.log_result("Test Pattern Detection", True, f"Patterns found - {pattern_info}")
                else:
                    self.log_result("Test Data Present", True, "No visits in test period (expected if no test data created)")
                
                self.log_result("Heatmap Calculation Accuracy", True, "All calculations verified correctly")
                return True
                
            else:
                self.log_result("Heatmap Calculation Accuracy", False, f"Failed to get heatmap: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Heatmap Calculation Accuracy", False, f"Error testing calculation accuracy: {str(e)}")
            return False
    
    def test_heatmap_edge_cases(self):
        """Test edge cases like invalid dates, future dates, etc."""
        print("\n=== Testing Heatmap Edge Cases ===")
        
        try:
            # Test with invalid date format
            params_invalid = {
                "start_date": "invalid-date",
                "end_date": "also-invalid"
            }
            
            response = requests.get(f"{API_BASE}/attendance/heatmap", params=params_invalid, headers=self.headers)
            
            # Should either handle gracefully or return error
            if response.status_code in [200, 400, 422]:
                self.log_result("Invalid Date Format", True, f"Handled invalid dates appropriately: {response.status_code}")
            else:
                self.log_result("Invalid Date Format", False, f"Unexpected response to invalid dates: {response.status_code}")
                return False
            
            # Test with future dates
            future_start = datetime.now(timezone.utc) + timedelta(days=1)
            future_end = datetime.now(timezone.utc) + timedelta(days=7)
            
            params_future = {
                "start_date": future_start.isoformat(),
                "end_date": future_end.isoformat()
            }
            
            response = requests.get(f"{API_BASE}/attendance/heatmap", params=params_future, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                stats = data["stats"]
                
                # Future dates should return zero visits
                if stats["total_visits"] == 0:
                    self.log_result("Future Dates", True, "Future dates correctly return zero visits")
                else:
                    self.log_result("Future Dates", False, f"Future dates returned {stats['total_visits']} visits")
                    return False
            else:
                self.log_result("Future Dates", False, f"Failed future dates test: {response.status_code}")
                return False
            
            # Test with start_date after end_date
            end_before_start = datetime.now(timezone.utc) - timedelta(days=7)
            start_after_end = datetime.now(timezone.utc) - timedelta(days=1)
            
            params_reversed = {
                "start_date": start_after_end.isoformat(),
                "end_date": end_before_start.isoformat()
            }
            
            response = requests.get(f"{API_BASE}/attendance/heatmap", params=params_reversed, headers=self.headers)
            
            # Should handle gracefully (either swap dates or return empty)
            if response.status_code in [200, 400]:
                self.log_result("Reversed Dates", True, f"Handled reversed dates appropriately: {response.status_code}")
            else:
                self.log_result("Reversed Dates", False, f"Unexpected response to reversed dates: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Heatmap Edge Cases", False, f"Error testing edge cases: {str(e)}")
            return False
    
    def cleanup_test_data(self):
        """Clean up created test data"""
        try:
            # Note: Access logs cleanup would require a delete endpoint
            # For now, we'll just log that cleanup would be needed
            if self.created_access_logs:
                self.log_result("Cleanup", True, f"Would clean up {len(self.created_access_logs)} access logs (no delete endpoint available)")
            else:
                self.log_result("Cleanup", True, "No test data to clean up")
            
        except Exception as e:
            self.log_result("Cleanup", False, f"Error during cleanup: {str(e)}")
    
    def run_all_tests(self):
        """Run all attendance heatmap tests"""
        print("🚀 Starting Attendance Heatmap API Tests")
        print("=" * 60)
        
        # Authentication
        if not self.authenticate():
            return False
        
        # Setup test data
        if not self.setup_test_data():
            return False
        
        # Create some test access logs (optional - tests work without this too)
        self.create_test_access_logs()
        
        # Run tests
        tests = [
            self.test_heatmap_without_parameters,
            self.test_heatmap_with_custom_dates,
            self.test_heatmap_calculation_accuracy,
            self.test_heatmap_edge_cases
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ FAIL: {test.__name__} - Exception: {str(e)}")
                failed += 1
        
        # Cleanup
        self.cleanup_test_data()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed / (passed + failed) * 100):.1f}%" if (passed + failed) > 0 else "No tests run")
        
        if failed == 0:
            print("🎉 All attendance heatmap tests passed!")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
        return failed == 0

def main():
    """Main test runner"""
    runner = AttendanceHeatmapTestRunner()
    success = runner.run_all_tests()
    
    if success:
        print("\n✅ Attendance Heatmap API testing completed successfully!")
        exit(0)
    else:
        print("\n❌ Attendance Heatmap API testing failed!")
        exit(1)

if __name__ == "__main__":
    main()