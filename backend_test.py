#!/usr/bin/env python3
"""
Backend Test Suite - Phase 2E Engagement Features
Focus on Points System, Global Search, Activity Feeds, and Engagement Scoring
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

class EngagementFeaturesTestRunner:
    def __init__(self):
        self.token = None
        self.headers = {}
        self.test_results = []
        self.created_members = []  # Track created members for cleanup
        self.created_invoices = []  # Track created invoices for cleanup
        self.test_member_id = None
        self.test_member_id_2 = None
        self.test_invoice_id = None
        
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
    
    def test_points_balance_api(self):
        """Test Points Balance API - GET /api/engagement/points/balance/{member_id}"""
        print("\n=== Testing Points Balance API ===")
        
        try:
            # Test with existing member
            response = requests.get(f"{API_BASE}/engagement/points/balance/{self.test_member_id}", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required structure
                required_fields = ["member_id", "total_points", "lifetime_points", "last_updated"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Points Balance Structure", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify data types
                if not isinstance(data["total_points"], int):
                    self.log_result("Points Balance Total Points Type", False, 
                                  "Total points should be integer")
                    return False
                
                if not isinstance(data["lifetime_points"], int):
                    self.log_result("Points Balance Lifetime Points Type", False, 
                                  "Lifetime points should be integer")
                    return False
                
                if data["member_id"] != self.test_member_id:
                    self.log_result("Points Balance Member ID", False, 
                                  "Member ID mismatch")
                    return False
                
                self.log_result("Points Balance API (Existing Member)", True, 
                              f"Retrieved balance: {data['total_points']} total, {data['lifetime_points']} lifetime")
                
                # Test with new member (should initialize to 0)
                response = requests.get(f"{API_BASE}/engagement/points/balance/{self.test_member_id_2}", headers=self.headers)
                if response.status_code == 200:
                    new_data = response.json()
                    if new_data["total_points"] == 0 and new_data["lifetime_points"] == 0:
                        self.log_result("Points Balance API (New Member)", True, 
                                      "New member initialized with 0 points")
                    else:
                        self.log_result("Points Balance API (New Member)", False, 
                                      f"Expected 0 points, got {new_data['total_points']}")
                        return False
                else:
                    self.log_result("Points Balance API (New Member)", False, 
                                  f"Failed to get balance for new member: {response.status_code}")
                    return False
                
                return True
                
            else:
                self.log_result("Points Balance API", False, 
                              f"Failed to get points balance: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Points Balance API", False, f"Error testing points balance API: {str(e)}")
            return False
    
    def test_points_award_api(self):
        """Test Points Award API - POST /api/engagement/points/award"""
        print("\n=== Testing Points Award API ===")
        
        try:
            # Get initial balance
            response = requests.get(f"{API_BASE}/engagement/points/balance/{self.test_member_id}", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Points Award API - Get Initial Balance", False, "Failed to get initial balance")
                return False
            
            initial_balance = response.json()["total_points"]
            
            # Award points
            award_data = {
                "member_id": self.test_member_id,
                "points": 25,
                "reason": "Test reward",
                "reference_id": "test_ref_123"
            }
            
            response = requests.post(f"{API_BASE}/engagement/points/award", json=award_data, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required structure
                required_fields = ["success", "new_balance", "points_awarded", "transaction_id"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Points Award Structure", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify balance update
                if data["new_balance"] != initial_balance + 25:
                    self.log_result("Points Award Balance Update", False, 
                                  f"Expected {initial_balance + 25}, got {data['new_balance']}")
                    return False
                
                if data["points_awarded"] != 25:
                    self.log_result("Points Award Points Awarded", False, 
                                  f"Expected 25, got {data['points_awarded']}")
                    return False
                
                # Verify transaction was recorded
                txn_response = requests.get(f"{API_BASE}/engagement/points/transactions/{self.test_member_id}?limit=1", headers=self.headers)
                if txn_response.status_code == 200:
                    txn_data = txn_response.json()
                    if txn_data["transactions"]:
                        latest_txn = txn_data["transactions"][0]
                        if latest_txn["id"] == data["transaction_id"] and latest_txn["points"] == 25:
                            self.log_result("Points Award Transaction Record", True, "Transaction recorded correctly")
                        else:
                            self.log_result("Points Award Transaction Record", False, "Transaction not recorded correctly")
                            return False
                    else:
                        self.log_result("Points Award Transaction Record", False, "No transactions found")
                        return False
                else:
                    self.log_result("Points Award Transaction Record", False, "Failed to get transactions")
                    return False
                
                # Test with non-existent member (should initialize)
                fake_member_id = "fake_member_123"
                award_data_fake = {
                    "member_id": fake_member_id,
                    "points": 10,
                    "reason": "Test for new member"
                }
                
                response = requests.post(f"{API_BASE}/engagement/points/award", json=award_data_fake, headers=self.headers)
                if response.status_code == 200:
                    fake_data = response.json()
                    if fake_data["new_balance"] == 10:
                        self.log_result("Points Award Non-Existent Member", True, "Initialized new member correctly")
                    else:
                        self.log_result("Points Award Non-Existent Member", False, f"Expected 10, got {fake_data['new_balance']}")
                        return False
                else:
                    self.log_result("Points Award Non-Existent Member", False, f"Failed to award to non-existent member: {response.status_code}")
                    return False
                
                self.log_result("Points Award API", True, 
                              f"Successfully awarded 25 points, new balance: {data['new_balance']}")
                return True
                
            else:
                self.log_result("Points Award API", False, 
                              f"Failed to award points: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Points Award API", False, f"Error testing points award API: {str(e)}")
            return False
    
    def test_points_transactions_api(self):
        """Test Points Transactions API - GET /api/engagement/points/transactions/{member_id}"""
        print("\n=== Testing Points Transactions API ===")
        
        try:
            # Test with default limit (50)
            response = requests.get(f"{API_BASE}/engagement/points/transactions/{self.test_member_id}", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required structure
                required_fields = ["member_id", "transactions", "total_transactions"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Points Transactions Structure", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify member ID
                if data["member_id"] != self.test_member_id:
                    self.log_result("Points Transactions Member ID", False, 
                                  "Member ID mismatch")
                    return False
                
                # Verify transactions structure
                if data["transactions"]:
                    transaction = data["transactions"][0]
                    txn_fields = ["id", "member_id", "points", "transaction_type", "reason", "created_at"]
                    missing_txn_fields = [field for field in txn_fields if field not in transaction]
                    
                    if missing_txn_fields:
                        self.log_result("Points Transactions Transaction Structure", False, 
                                      f"Missing transaction fields: {missing_txn_fields}")
                        return False
                    
                    # Verify transactions are sorted by created_at descending
                    if len(data["transactions"]) > 1:
                        first_txn = data["transactions"][0]
                        second_txn = data["transactions"][1]
                        if first_txn["created_at"] < second_txn["created_at"]:
                            self.log_result("Points Transactions Sort Order", False, 
                                          "Transactions not sorted by created_at descending")
                            return False
                        else:
                            self.log_result("Points Transactions Sort Order", True, 
                                          "Transactions correctly sorted by created_at descending")
                
                # Test with custom limit
                response = requests.get(f"{API_BASE}/engagement/points/transactions/{self.test_member_id}?limit=5", headers=self.headers)
                if response.status_code == 200:
                    limited_data = response.json()
                    if len(limited_data["transactions"]) <= 5:
                        self.log_result("Points Transactions Custom Limit", True, 
                                      f"Custom limit working: {len(limited_data['transactions'])} transactions")
                    else:
                        self.log_result("Points Transactions Custom Limit", False, 
                                      f"Expected ≤5 transactions, got {len(limited_data['transactions'])}")
                        return False
                else:
                    self.log_result("Points Transactions Custom Limit", False, 
                                  f"Failed to get transactions with custom limit: {response.status_code}")
                    return False
                
                self.log_result("Points Transactions API", True, 
                              f"Retrieved {data['total_transactions']} transactions for member")
                return True
                
            else:
                self.log_result("Points Transactions API", False, 
                              f"Failed to get points transactions: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Points Transactions API", False, f"Error testing points transactions API: {str(e)}")
            return False
    
    def test_points_leaderboard_api(self):
        """Test Points Leaderboard API - GET /api/engagement/points/leaderboard"""
        print("\n=== Testing Points Leaderboard API ===")
        
        try:
            # Test with default limit (10)
            response = requests.get(f"{API_BASE}/engagement/points/leaderboard", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required structure
                required_fields = ["period", "leaderboard", "total_members"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Points Leaderboard Structure", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify leaderboard structure
                if data["leaderboard"]:
                    leader = data["leaderboard"][0]
                    leader_fields = ["member_id", "member_name", "email", "membership_type", "total_points", "lifetime_points"]
                    missing_leader_fields = [field for field in leader_fields if field not in leader]
                    
                    if missing_leader_fields:
                        self.log_result("Points Leaderboard Leader Structure", False, 
                                      f"Missing leader fields: {missing_leader_fields}")
                        return False
                    
                    # Verify sorted by total_points descending
                    if len(data["leaderboard"]) > 1:
                        first_leader = data["leaderboard"][0]
                        second_leader = data["leaderboard"][1]
                        if first_leader["total_points"] < second_leader["total_points"]:
                            self.log_result("Points Leaderboard Sort Order", False, 
                                          "Leaderboard not sorted by total_points descending")
                            return False
                        else:
                            self.log_result("Points Leaderboard Sort Order", True, 
                                          "Leaderboard correctly sorted by total_points descending")
                
                # Test with custom limit (20)
                response = requests.get(f"{API_BASE}/engagement/points/leaderboard?limit=20", headers=self.headers)
                if response.status_code == 200:
                    limited_data = response.json()
                    if len(limited_data["leaderboard"]) <= 20:
                        self.log_result("Points Leaderboard Custom Limit", True, 
                                      f"Custom limit working: {len(limited_data['leaderboard'])} members")
                    else:
                        self.log_result("Points Leaderboard Custom Limit", False, 
                                      f"Expected ≤20 members, got {len(limited_data['leaderboard'])}")
                        return False
                else:
                    self.log_result("Points Leaderboard Custom Limit", False, 
                                  f"Failed to get leaderboard with custom limit: {response.status_code}")
                    return False
                
                # Verify member details included
                if data["leaderboard"]:
                    first_member = data["leaderboard"][0]
                    if not first_member.get("member_name") or not first_member.get("email"):
                        self.log_result("Points Leaderboard Member Details", False, 
                                      "Member details (name, email) not properly included")
                        return False
                    else:
                        self.log_result("Points Leaderboard Member Details", True, 
                                      "Member details properly included")
                
                self.log_result("Points Leaderboard API", True, 
                              f"Retrieved leaderboard with {len(data['leaderboard'])} members, "
                              f"total members: {data['total_members']}")
                return True
                
            else:
                self.log_result("Points Leaderboard API", False, 
                              f"Failed to get points leaderboard: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Points Leaderboard API", False, f"Error testing points leaderboard API: {str(e)}")
            return False
    
    def test_global_search_api(self):
        """Test Global Search API - GET /api/engagement/search"""
        print("\n=== Testing Global Search API ===")
        
        try:
            # Test with query length < 2 (should return empty)
            response = requests.get(f"{API_BASE}/engagement/search?query=a", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required structure
                required_fields = ["query", "results", "total_results"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Global Search Structure", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify empty results for short query
                if data["total_results"] != 0:
                    self.log_result("Global Search Short Query", False, 
                                  f"Expected 0 results for short query, got {data['total_results']}")
                    return False
                else:
                    self.log_result("Global Search Short Query", True, 
                                  "Correctly returns empty results for query < 2 characters")
                
                # Test with query length >= 2
                response = requests.get(f"{API_BASE}/engagement/search?query=test", headers=self.headers)
                if response.status_code == 200:
                    search_data = response.json()
                    
                    # Verify results structure
                    results = search_data["results"]
                    result_categories = ["members", "classes", "invoices"]
                    missing_categories = [cat for cat in result_categories if cat not in results]
                    
                    if missing_categories:
                        self.log_result("Global Search Results Categories", False, 
                                      f"Missing result categories: {missing_categories}")
                        return False
                    
                    # Verify member results structure
                    if results["members"]:
                        member = results["members"][0]
                        member_fields = ["id", "name", "email", "phone", "status", "type"]
                        missing_member_fields = [field for field in member_fields if field not in member]
                        
                        if missing_member_fields:
                            self.log_result("Global Search Member Structure", False, 
                                          f"Missing member fields: {missing_member_fields}")
                            return False
                        
                        if member["type"] != "member":
                            self.log_result("Global Search Member Type", False, 
                                          f"Expected type 'member', got '{member['type']}'")
                            return False
                    
                    # Verify class results structure
                    if results["classes"]:
                        class_result = results["classes"][0]
                        class_fields = ["id", "name", "instructor", "type"]
                        missing_class_fields = [field for field in class_fields if field not in class_result]
                        
                        if missing_class_fields:
                            self.log_result("Global Search Class Structure", False, 
                                          f"Missing class fields: {missing_class_fields}")
                            return False
                        
                        if class_result["type"] != "class":
                            self.log_result("Global Search Class Type", False, 
                                          f"Expected type 'class', got '{class_result['type']}'")
                            return False
                    
                    # Verify invoice results structure
                    if results["invoices"]:
                        invoice = results["invoices"][0]
                        invoice_fields = ["id", "invoice_number", "member_id", "amount", "status", "type"]
                        missing_invoice_fields = [field for field in invoice_fields if field not in invoice]
                        
                        if missing_invoice_fields:
                            self.log_result("Global Search Invoice Structure", False, 
                                          f"Missing invoice fields: {missing_invoice_fields}")
                            return False
                        
                        if invoice["type"] != "invoice":
                            self.log_result("Global Search Invoice Type", False, 
                                          f"Expected type 'invoice', got '{invoice['type']}'")
                            return False
                    
                    # Verify limit of 10 per category
                    for category, items in results.items():
                        if len(items) > 10:
                            self.log_result(f"Global Search {category.title()} Limit", False, 
                                          f"Should return max 10 {category}, got {len(items)}")
                            return False
                    
                    # Verify total_results count
                    expected_total = len(results["members"]) + len(results["classes"]) + len(results["invoices"])
                    if search_data["total_results"] != expected_total:
                        self.log_result("Global Search Total Results Count", False, 
                                      f"Expected {expected_total}, got {search_data['total_results']}")
                        return False
                    
                    self.log_result("Global Search API", True, 
                                  f"Search for 'test' returned {search_data['total_results']} results: "
                                  f"{len(results['members'])} members, {len(results['classes'])} classes, "
                                  f"{len(results['invoices'])} invoices")
                    return True
                    
                else:
                    self.log_result("Global Search API", False, 
                                  f"Failed to search with valid query: {response.status_code}")
                    return False
                
            else:
                self.log_result("Global Search API", False, 
                              f"Failed to perform global search: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Global Search API", False, f"Error testing global search API: {str(e)}")
            return False
    
    def test_activity_feed_api(self):
        """Test Activity Feed API - GET /api/engagement/activity-feed/{member_id}"""
        print("\n=== Testing Activity Feed API ===")
        
        try:
            # Test with default limit (50)
            response = requests.get(f"{API_BASE}/engagement/activity-feed/{self.test_member_id}", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required structure
                required_fields = ["member_id", "activities", "total_activities"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Activity Feed Structure", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify member ID
                if data["member_id"] != self.test_member_id:
                    self.log_result("Activity Feed Member ID", False, 
                                  "Member ID mismatch")
                    return False
                
                # Verify activities structure
                if data["activities"]:
                    activity = data["activities"][0]
                    activity_fields = ["type", "timestamp", "description", "icon", "color"]
                    missing_activity_fields = [field for field in activity_fields if field not in activity]
                    
                    if missing_activity_fields:
                        self.log_result("Activity Feed Activity Structure", False, 
                                      f"Missing activity fields: {missing_activity_fields}")
                        return False
                    
                    # Verify activities are sorted by timestamp descending
                    if len(data["activities"]) > 1:
                        first_activity = data["activities"][0]
                        second_activity = data["activities"][1]
                        if first_activity["timestamp"] < second_activity["timestamp"]:
                            self.log_result("Activity Feed Sort Order", False, 
                                          "Activities not sorted by timestamp descending")
                            return False
                        else:
                            self.log_result("Activity Feed Sort Order", True, 
                                          "Activities correctly sorted by timestamp descending")
                    
                    # Verify activity types from multiple sources
                    activity_types = set(act["type"] for act in data["activities"])
                    expected_types = {"check_in", "payment", "class_booking", "points"}
                    
                    self.log_result("Activity Feed Multiple Sources", True, 
                                  f"Activity feed includes types: {list(activity_types)}")
                
                # Test with custom limit
                response = requests.get(f"{API_BASE}/engagement/activity-feed/{self.test_member_id}?limit=10", headers=self.headers)
                if response.status_code == 200:
                    limited_data = response.json()
                    if len(limited_data["activities"]) <= 10:
                        self.log_result("Activity Feed Custom Limit", True, 
                                      f"Custom limit working: {len(limited_data['activities'])} activities")
                    else:
                        self.log_result("Activity Feed Custom Limit", False, 
                                      f"Expected ≤10 activities, got {len(limited_data['activities'])}")
                        return False
                else:
                    self.log_result("Activity Feed Custom Limit", False, 
                                  f"Failed to get activity feed with custom limit: {response.status_code}")
                    return False
                
                self.log_result("Activity Feed API", True, 
                              f"Retrieved {data['total_activities']} activities for member")
                return True
                
            else:
                self.log_result("Activity Feed API", False, 
                              f"Failed to get activity feed: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Activity Feed API", False, f"Error testing activity feed API: {str(e)}")
            return False
    
    def test_analytics_api_error_handling(self):
        """Test error handling for analytics APIs"""
        print("\n=== Testing Analytics API Error Handling ===")
        
        try:
            # Test invalid parameters for revenue breakdown
            response = requests.get(f"{API_BASE}/analytics/revenue-breakdown?period_months=-1", headers=self.headers)
            # Should still work but with reasonable defaults or handle gracefully
            
            # Test invalid parameters for attendance deep dive
            response = requests.get(f"{API_BASE}/analytics/attendance-deep-dive?days_back=0", headers=self.headers)
            # Should still work but with reasonable defaults or handle gracefully
            
            # Test very large parameters
            response = requests.get(f"{API_BASE}/analytics/revenue-breakdown?period_months=1000", headers=self.headers)
            if response.status_code == 200:
                self.log_result("Revenue Breakdown Large Parameter", True, "Handles large parameters gracefully")
            else:
                self.log_result("Revenue Breakdown Large Parameter", False, f"Failed with large parameter: {response.status_code}")
                return False
            
            response = requests.get(f"{API_BASE}/analytics/attendance-deep-dive?days_back=10000", headers=self.headers)
            if response.status_code == 200:
                self.log_result("Attendance Deep Dive Large Parameter", True, "Handles large parameters gracefully")
            else:
                self.log_result("Attendance Deep Dive Large Parameter", False, f"Failed with large parameter: {response.status_code}")
                return False
            
            return True
                
        except Exception as e:
            self.log_result("Analytics API Error Handling", False, f"Error testing error handling: {str(e)}")
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
    
    def run_advanced_analytics_tests(self):
        """Run the advanced analytics API tests"""
        print("=" * 80)
        print("BACKEND TESTING - PHASE 2D ADVANCED ANALYTICS APIs")
        print("=" * 80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Setup test members (for context, though analytics APIs work with existing data)
        if not self.setup_test_members():
            print("❌ Failed to setup test members. Cannot proceed with tests.")
            return False
        
        # Step 3: Run ADVANCED ANALYTICS API TESTS
        print("\n" + "=" * 60)
        print("ADVANCED ANALYTICS API TESTS")
        print("=" * 60)
        
        analytics_results = []
        
        # 1. Authentication Tests
        print("\n🔐 TEST 1: Analytics API Authentication")
        analytics_results.append(self.test_analytics_api_authentication())
        
        # 2. Revenue Breakdown Analytics API
        print("\n💰 TEST 2: Revenue Breakdown Analytics API")
        analytics_results.append(self.test_revenue_breakdown_analytics_api())
        
        # 3. Geographic Distribution Analytics API
        print("\n🌍 TEST 3: Geographic Distribution Analytics API")
        analytics_results.append(self.test_geographic_distribution_analytics_api())
        
        # 4. Attendance Deep Dive Analytics API
        print("\n📊 TEST 4: Attendance Deep Dive Analytics API")
        analytics_results.append(self.test_attendance_deep_dive_analytics_api())
        
        # 5. Member Lifetime Value Analytics API
        print("\n💎 TEST 5: Member Lifetime Value Analytics API")
        analytics_results.append(self.test_member_lifetime_value_analytics_api())
        
        # 6. Churn Prediction Analytics API
        print("\n⚠️ TEST 6: Churn Prediction Analytics API")
        analytics_results.append(self.test_churn_prediction_analytics_api())
        
        # 7. Error Handling Tests
        print("\n🛠️ TEST 7: Analytics API Error Handling")
        analytics_results.append(self.test_analytics_api_error_handling())
        
        # Step 4: Generate Summary
        print("\n" + "=" * 80)
        print("TEST RESULTS SUMMARY")
        print("=" * 80)
        
        analytics_passed = sum(analytics_results)
        analytics_total = len(analytics_results)
        
        print(f"\n🎯 ADVANCED ANALYTICS TESTS: {analytics_passed}/{analytics_total} PASSED")
        print(f"📈 SUCCESS RATE: {(analytics_passed/analytics_total)*100:.1f}%")
        
        # Detailed results
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        # Step 5: Cleanup
        self.cleanup_test_data()
        
        # Return success if all analytics tests passed
        return analytics_passed == analytics_total

def main():
    """Main execution function"""
    tester = AdvancedAnalyticsTestRunner()
    success = tester.run_advanced_analytics_tests()
    
    if success:
        print("\n🎉 ALL ADVANCED ANALYTICS TESTS PASSED!")
        exit(0)
    else:
        print("\n💥 SOME ADVANCED ANALYTICS TESTS FAILED!")
        exit(1)

if __name__ == "__main__":
    main()