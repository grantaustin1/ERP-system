#!/usr/bin/env python3
"""
Backend Test Suite for Access Override System
Comprehensive testing of override reasons, member search, access overrides, and prospect conversion
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

class AccessOverrideTester:
    def __init__(self):
        self.token = None
        self.headers = {}
        self.test_results = []
        self.created_members = []  # Track created members for cleanup
        self.created_overrides = []  # Track created overrides for cleanup
        self.test_member_id = None
        self.test_prospect_id = None
        self.reason_ids = {}  # Store reason IDs for testing
        
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
    
    def test_seed_default_override_reasons(self):
        """Test seeding default override reasons"""
        print("\n=== Testing Seed Default Override Reasons ===")
        
        try:
            response = requests.post(f"{API_BASE}/override-reasons/seed-defaults", 
                                   headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if seeding was successful or if reasons already exist
                if result.get("success") or "already exist" in result.get("message", ""):
                    main_reasons = result.get("main_reasons", 5)  # Default if already exist
                    sub_reasons = result.get("sub_reasons", 6)    # Default if already exist
                    
                    self.log_result("Seed Default Override Reasons", True, 
                                  f"Override reasons available: {result.get('message', 'Seeded successfully')}")
                    return True
                else:
                    self.log_result("Seed Default Override Reasons", False, 
                                  f"Seed operation failed: {result}")
                    return False
            else:
                self.log_result("Seed Default Override Reasons", False, 
                              f"Failed to seed reasons: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Seed Default Override Reasons", False, f"Error seeding reasons: {str(e)}")
            return False
    
    def test_get_override_reasons_flat(self):
        """Test getting override reasons in flat list format"""
        print("\n=== Testing Get Override Reasons (Flat List) ===")
        
        try:
            response = requests.get(f"{API_BASE}/override-reasons", headers=self.headers)
            
            if response.status_code == 200:
                reasons = response.json()
                
                if len(reasons) >= 11:  # 5 main + 6 sub = 11 total
                    # Store reason IDs for later tests
                    for reason in reasons:
                        reason_name = reason.get("name", "")
                        if "New Prospect" in reason_name:
                            self.reason_ids["new_prospect"] = reason.get("reason_id")
                        elif "Debt Arrangement" in reason_name:
                            self.reason_ids["debt_arrangement"] = reason.get("reason_id")
                    
                    # Verify structure
                    first_reason = reasons[0]
                    required_fields = ["reason_id", "name", "requires_pin", "is_active"]
                    has_all_fields = all(field in first_reason for field in required_fields)
                    
                    if has_all_fields:
                        self.log_result("Get Override Reasons Flat", True, 
                                      f"Retrieved {len(reasons)} reasons with correct structure")
                        return True
                    else:
                        missing_fields = [field for field in required_fields if field not in first_reason]
                        self.log_result("Get Override Reasons Flat", False, 
                                      f"Missing fields in reason structure: {missing_fields}")
                        return False
                else:
                    self.log_result("Get Override Reasons Flat", False, 
                                  f"Expected at least 11 reasons, got {len(reasons)}")
                    return False
            else:
                self.log_result("Get Override Reasons Flat", False, 
                              f"Failed to get reasons: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Get Override Reasons Flat", False, f"Error getting reasons: {str(e)}")
            return False
    
    def test_get_override_reasons_hierarchical(self):
        """Test getting override reasons in hierarchical format"""
        print("\n=== Testing Get Override Reasons (Hierarchical) ===")
        
        try:
            response = requests.get(f"{API_BASE}/override-reasons/hierarchical", headers=self.headers)
            
            if response.status_code == 200:
                reasons = response.json()
                
                # Find New Prospect reason to verify hierarchy
                new_prospect_reason = None
                for reason in reasons:
                    if "New Prospect" in reason.get("name", ""):
                        new_prospect_reason = reason
                        break
                
                if new_prospect_reason:
                    sub_reasons = new_prospect_reason.get("sub_reasons", [])
                    if len(sub_reasons) >= 6:  # Should have 6 sub-reasons
                        self.log_result("Get Override Reasons Hierarchical", True, 
                                      f"Hierarchical structure correct: New Prospect has {len(sub_reasons)} sub-reasons")
                        
                        # Store sub-reason ID for testing
                        if sub_reasons:
                            self.reason_ids["new_prospect_sub"] = sub_reasons[0].get("reason_id")
                        
                        return True
                    else:
                        self.log_result("Get Override Reasons Hierarchical", False, 
                                      f"New Prospect has {len(sub_reasons)} sub-reasons, expected 6")
                        return False
                else:
                    self.log_result("Get Override Reasons Hierarchical", False, 
                                  "New Prospect reason not found in hierarchical response")
                    return False
            else:
                self.log_result("Get Override Reasons Hierarchical", False, 
                              f"Failed to get hierarchical reasons: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Get Override Reasons Hierarchical", False, f"Error getting hierarchical reasons: {str(e)}")
            return False
    
    def setup_test_member(self):
        """Create a test member for override testing"""
        print("\n=== Setting Up Test Member ===")
        
        try:
            # Get membership types first
            response = requests.get(f"{API_BASE}/membership-types", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Get Membership Types", False, "Failed to get membership types")
                return False
            
            membership_types = response.json()
            if not membership_types:
                self.log_result("Get Membership Types", False, "No membership types found")
                return False
            
            membership_type_id = membership_types[0]["id"]
            
            # Create test member with unique name
            timestamp = int(time.time())
            member_data = {
                "first_name": f"TestMember{timestamp % 1000}",
                "last_name": f"Override{timestamp % 1000}",
                "email": f"test.member.{timestamp}@example.com",
                "phone": f"082555{timestamp % 10000:04d}",
                "membership_type_id": membership_type_id
            }
            
            response = requests.post(f"{API_BASE}/members", json=member_data, headers=self.headers)
            
            if response.status_code == 200:
                member = response.json()
                self.test_member_id = member["id"]
                self.created_members.append(member["id"])
                
                # Set access PIN via PUT request
                pin_response = requests.put(f"{API_BASE}/members/{self.test_member_id}", 
                                          json={"access_pin": "1234"}, headers=self.headers)
                
                if pin_response.status_code == 200:
                    self.log_result("Setup Test Member", True, 
                                  f"Created test member with ID: {self.test_member_id} and set PIN")
                    return True
                else:
                    self.log_result("Setup Test Member", False, 
                                  f"Failed to set PIN: {pin_response.status_code}")
                    return False
            else:
                self.log_result("Setup Test Member", False, 
                              f"Failed to create member: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Setup Test Member", False, f"Error creating test member: {str(e)}")
            return False
    
    def test_member_search(self):
        """Test member search functionality"""
        print("\n=== Testing Member Search ===")
        
        if not self.test_member_id:
            self.log_result("Member Search", False, "No test member available for search testing")
            return False
        
        try:
            # Get the test member details first
            response = requests.get(f"{API_BASE}/members/{self.test_member_id}", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Get Test Member", False, "Failed to get test member details")
                return False
            
            member = response.json()
            first_name = member.get("first_name")
            email = member.get("email")
            phone = member.get("phone")
            
            # Test 1: Search by first name
            response = requests.get(f"{API_BASE}/members/search", 
                                  params={"q": first_name}, headers=self.headers)
            
            if response.status_code == 200:
                results = response.json()
                found_member = any(m.get("id") == self.test_member_id for m in results)
                
                if found_member and len(results) > 0:
                    # Verify status_label is populated
                    test_member_result = next(m for m in results if m.get("id") == self.test_member_id)
                    status_label = test_member_result.get("status_label")
                    
                    if status_label in ["Active", "Expired", "Suspended", "Cancelled"]:
                        self.log_result("Member Search by First Name", True, 
                                      f"Found member by first name '{first_name}' with status_label: {status_label}")
                    else:
                        self.log_result("Member Search by First Name", False, 
                                      f"Member found but status_label missing or invalid: {status_label}")
                else:
                    self.log_result("Member Search by First Name", False, 
                                  f"Member not found in search results for '{first_name}'")
            elif response.status_code == 404:
                self.log_result("Member Search by First Name", False, 
                              f"No members found for search term '{first_name}' (404 - this may be expected if no matches)")
            else:
                self.log_result("Member Search by First Name", False, 
                              f"Search by first name failed: {response.status_code}")
            
            # Test 2: Search by email
            response = requests.get(f"{API_BASE}/members/search", 
                                  params={"q": email}, headers=self.headers)
            
            if response.status_code == 200:
                results = response.json()
                found_member = any(m.get("id") == self.test_member_id for m in results)
                
                if found_member:
                    self.log_result("Member Search by Email", True, 
                                  f"Found member by email '{email}'")
                else:
                    self.log_result("Member Search by Email", False, 
                                  f"Member not found in search results for '{email}'")
            elif response.status_code == 404:
                self.log_result("Member Search by Email", False, 
                              f"No members found for email '{email}' (404)")
            else:
                self.log_result("Member Search by Email", False, 
                              f"Search by email failed: {response.status_code}")
            
            # Test 3: Search by phone
            response = requests.get(f"{API_BASE}/members/search", 
                                  params={"q": phone}, headers=self.headers)
            
            if response.status_code == 200:
                results = response.json()
                found_member = any(m.get("id") == self.test_member_id for m in results)
                
                if found_member:
                    self.log_result("Member Search by Phone", True, 
                                  f"Found member by phone '{phone}'")
                    return True
                else:
                    self.log_result("Member Search by Phone", False, 
                                  f"Member not found in search results for '{phone}'")
                    return False
            elif response.status_code == 404:
                self.log_result("Member Search by Phone", False, 
                              f"No members found for phone '{phone}' (404)")
                return False
            else:
                self.log_result("Member Search by Phone", False, 
                              f"Search by phone failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Member Search", False, f"Error in member search: {str(e)}")
            return False
    
    def test_access_override_existing_member_with_pin(self):
        """Test access override for existing member with correct PIN"""
        print("\n=== Testing Access Override - Existing Member with PIN ===")
        
        if not self.test_member_id or not self.reason_ids.get("debt_arrangement"):
            self.log_result("Access Override with PIN", False, 
                          "Missing test member or debt arrangement reason ID")
            return False
        
        try:
            override_data = {
                "member_id": self.test_member_id,
                "reason_id": self.reason_ids["debt_arrangement"],
                "access_pin": "1234",  # Correct PIN
                "location": "Main Entrance"
            }
            
            response = requests.post(f"{API_BASE}/access/override", 
                                   json=override_data, headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                
                # Verify access is granted
                if result.get("success") is True:
                    override_id = result.get("override_id")
                    if override_id:
                        self.created_overrides.append(override_id)
                    
                    self.log_result("Access Override with PIN", True, 
                                  f"Access granted with correct PIN, override ID: {override_id}")
                    
                    # Verify daily override count is incremented
                    member_response = requests.get(f"{API_BASE}/members/{self.test_member_id}", 
                                                 headers=self.headers)
                    if member_response.status_code == 200:
                        member = member_response.json()
                        daily_count = member.get("daily_override_count", 0)
                        
                        if daily_count >= 1:
                            self.log_result("Daily Override Count", True, 
                                          f"Daily override count incremented to {daily_count}")
                        else:
                            self.log_result("Daily Override Count", False, 
                                          f"Daily override count not incremented: {daily_count}")
                    
                    # Verify access log is created
                    # Note: This would require an access log endpoint to verify
                    
                    # Verify member journal entry is created
                    # Note: This would require a journal endpoint to verify
                    
                    return True
                else:
                    self.log_result("Access Override with PIN", False, 
                                  f"Access not granted despite correct PIN: {result}")
                    return False
            else:
                self.log_result("Access Override with PIN", False, 
                              f"Override request failed: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Access Override with PIN", False, f"Error in access override: {str(e)}")
            return False
    
    def test_access_override_wrong_pin(self):
        """Test access override with incorrect PIN"""
        print("\n=== Testing Access Override - Wrong PIN ===")
        
        if not self.test_member_id or not self.reason_ids.get("debt_arrangement"):
            self.log_result("Access Override Wrong PIN", False, 
                          "Missing test member or debt arrangement reason ID")
            return False
        
        try:
            override_data = {
                "member_id": self.test_member_id,
                "reason_id": self.reason_ids["debt_arrangement"],
                "access_pin": "9999",  # Wrong PIN
                "location": "Main Entrance"
            }
            
            response = requests.post(f"{API_BASE}/access/override", 
                                   json=override_data, headers=self.headers)
            
            if response.status_code == 403:
                self.log_result("Access Override Wrong PIN", True, 
                              "Correctly rejected access with wrong PIN (403 error)")
                return True
            elif response.status_code == 200:
                result = response.json()
                if result.get("success") is False:
                    self.log_result("Access Override Wrong PIN", True, 
                                  "Correctly rejected access with wrong PIN")
                    return True
                else:
                    self.log_result("Access Override Wrong PIN", False, 
                                  "Access granted despite wrong PIN")
                    return False
            else:
                self.log_result("Access Override Wrong PIN", False, 
                              f"Unexpected response code: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Access Override Wrong PIN", False, f"Error testing wrong PIN: {str(e)}")
            return False
    
    def test_access_override_new_prospect(self):
        """Test access override for new prospect"""
        print("\n=== Testing Access Override - New Prospect ===")
        
        if not self.reason_ids.get("new_prospect") or not self.reason_ids.get("new_prospect_sub"):
            self.log_result("Access Override New Prospect", False, 
                          "Missing new prospect reason IDs")
            return False
        
        try:
            timestamp = int(time.time())
            override_data = {
                "first_name": "Test",
                "last_name": "Prospect",
                "phone": f"083444{timestamp % 10000:04d}",
                "email": f"test.prospect.{timestamp}@example.com",
                "reason_id": self.reason_ids["new_prospect"],
                "sub_reason_id": self.reason_ids["new_prospect_sub"],
                "location": "Main Entrance"
            }
            
            response = requests.post(f"{API_BASE}/access/override", 
                                   json=override_data, headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                
                # Verify access is granted
                if result.get("success") is True:
                    member_id = result.get("member_id")
                    override_id = result.get("override_id")
                    
                    if member_id:
                        self.test_prospect_id = member_id
                        self.created_members.append(member_id)
                    
                    if override_id:
                        self.created_overrides.append(override_id)
                    
                    self.log_result("Access Override New Prospect", True, 
                                  f"New prospect created and access granted, member ID: {member_id}")
                    
                    # Verify new member record is created with is_prospect=true
                    if member_id:
                        member_response = requests.get(f"{API_BASE}/members/{member_id}", 
                                                     headers=self.headers)
                        if member_response.status_code == 200:
                            member = member_response.json()
                            is_prospect = member.get("is_prospect", False)
                            
                            if is_prospect:
                                self.log_result("New Prospect Member Record", True, 
                                              "Member created with is_prospect=true")
                            else:
                                self.log_result("New Prospect Member Record", False, 
                                              f"Member created but is_prospect={is_prospect}")
                    
                    return True
                else:
                    self.log_result("Access Override New Prospect", False, 
                                  f"Access not granted for new prospect: {result}")
                    return False
            else:
                self.log_result("Access Override New Prospect", False, 
                              f"New prospect override failed: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Access Override New Prospect", False, f"Error creating new prospect: {str(e)}")
            return False
    
    def test_daily_override_limit(self):
        """Test daily override limit enforcement"""
        print("\n=== Testing Daily Override Limit ===")
        
        if not self.test_member_id or not self.reason_ids.get("debt_arrangement"):
            self.log_result("Daily Override Limit", False, 
                          "Missing test member or debt arrangement reason ID")
            return False
        
        try:
            override_data = {
                "member_id": self.test_member_id,
                "reason_id": self.reason_ids["debt_arrangement"],
                "access_pin": "1234",
                "location": "Main Entrance"
            }
            
            # Create 2 more overrides (we already have 1 from previous test)
            for i in range(2):
                response = requests.post(f"{API_BASE}/access/override", 
                                       json=override_data, headers=self.headers)
                
                if response.status_code == 200:
                    result = response.json()
                    override_id = result.get("override_id")
                    if override_id:
                        self.created_overrides.append(override_id)
            
            # Try 4th override (should be rejected due to daily limit of 3)
            response = requests.post(f"{API_BASE}/access/override", 
                                   json=override_data, headers=self.headers)
            
            if response.status_code in [400, 403, 429]:
                response_text = response.text
                if "Daily override limit" in response_text or "limit reached" in response_text:
                    self.log_result("Daily Override Limit", True, 
                                  f"4th override correctly rejected due to daily limit (status: {response.status_code})")
                    return True
                else:
                    self.log_result("Daily Override Limit", False, 
                                  f"4th override rejected but not for daily limit: {response_text}")
                    return False
            elif response.status_code == 200:
                result = response.json()
                if result.get("success") is False:
                    self.log_result("Daily Override Limit", True, 
                                  "4th override correctly rejected due to daily limit")
                    return True
                else:
                    self.log_result("Daily Override Limit", False, 
                                  "4th override was granted despite daily limit")
                    return False
            else:
                self.log_result("Daily Override Limit", False, 
                              f"Unexpected response for 4th override: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Daily Override Limit", False, f"Error testing daily limit: {str(e)}")
            return False
    
    def test_convert_prospect_to_member(self):
        """Test converting prospect to full member"""
        print("\n=== Testing Convert Prospect to Member ===")
        
        if not self.test_prospect_id:
            self.log_result("Convert Prospect to Member", False, 
                          "No test prospect available for conversion")
            return False
        
        try:
            # Get membership types
            response = requests.get(f"{API_BASE}/membership-types", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Get Membership Types for Conversion", False, 
                              "Failed to get membership types")
                return False
            
            membership_types = response.json()
            if not membership_types:
                self.log_result("Get Membership Types for Conversion", False, 
                              "No membership types found")
                return False
            
            membership_type_id = membership_types[0]["id"]
            
            # Convert prospect to member
            response = requests.post(f"{API_BASE}/members/convert-prospect/{self.test_prospect_id}", 
                                   params={"membership_type_id": membership_type_id}, headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    self.log_result("Convert Prospect to Member", True, 
                                  f"Prospect successfully converted to member: {result.get('message')}")
                    
                    # Verify is_prospect becomes false and membership_status becomes active
                    member_response = requests.get(f"{API_BASE}/members/{self.test_prospect_id}", 
                                                 headers=self.headers)
                    if member_response.status_code == 200:
                        member = member_response.json()
                        is_prospect = member.get("is_prospect", True)
                        membership_status = member.get("membership_status")
                        
                        if not is_prospect and membership_status == "active":
                            self.log_result("Prospect Conversion Verification", True, 
                                          f"is_prospect={is_prospect}, membership_status={membership_status}")
                        else:
                            self.log_result("Prospect Conversion Verification", False, 
                                          f"Conversion incomplete: is_prospect={is_prospect}, status={membership_status}")
                    
                    return True
                else:
                    self.log_result("Convert Prospect to Member", False, 
                                  f"Conversion failed: {result}")
                    return False
            else:
                self.log_result("Convert Prospect to Member", False, 
                              f"Conversion request failed: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Convert Prospect to Member", False, f"Error converting prospect: {str(e)}")
            return False
    
    def cleanup_test_data(self):
        """Clean up test data created during testing"""
        print("\n=== Cleaning Up Test Data ===")
        
        # Note: In a real implementation, we would clean up created members and overrides
        # For now, we'll just log what we would clean up
        
        if self.created_members:
            self.log_result("Cleanup Test Data", True, 
                          f"Would clean up {len(self.created_members)} test members")
        
        if self.created_overrides:
            self.log_result("Cleanup Test Data", True, 
                          f"Would clean up {len(self.created_overrides)} test overrides")
    
    def run_all_tests(self):
        """Run all access override system tests"""
        print("🚀 Starting Access Override System Tests")
        print(f"Testing against: {API_BASE}")
        print("=" * 80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        print("\n📋 ACCESS OVERRIDE SYSTEM TESTING")
        print("Testing Requirements:")
        print("- Authentication: admin@gym.com / admin123")
        print("- Seed default override reasons (5 main, 6 sub)")
        print("- Get override reasons (flat and hierarchical)")
        print("- Member search by name, email, phone")
        print("- Access override with PIN verification")
        print("- Access override for new prospects")
        print("- Daily override limit enforcement")
        print("- Prospect to member conversion")
        
        # Execute all test phases
        success_count = 0
        total_tests = 8
        
        if self.test_seed_default_override_reasons():
            success_count += 1
        
        if self.test_get_override_reasons_flat():
            success_count += 1
        
        if self.test_get_override_reasons_hierarchical():
            success_count += 1
        
        if self.setup_test_member():
            if self.test_member_search():
                success_count += 1
            
            if self.test_access_override_existing_member_with_pin():
                success_count += 1
            
            if self.test_access_override_wrong_pin():
                success_count += 1
            
            if self.test_daily_override_limit():
                success_count += 1
        
        if self.test_access_override_new_prospect():
            if self.test_convert_prospect_to_member():
                success_count += 1
        
        # Cleanup
        self.cleanup_test_data()
        
        # Print summary
        self.print_summary()
        
        return success_count, total_tests
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🏁 ACCESS OVERRIDE SYSTEM TEST SUMMARY")
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

def main():
    """Main function to run the tests"""
    tester = AccessOverrideTester()
    success_count, total_tests = tester.run_all_tests()
    
    print(f"\n🎯 FINAL RESULT: {success_count}/{total_tests} major test scenarios passed")
    
    if success_count == total_tests:
        print("🎉 All Access Override System tests PASSED!")
        return 0
    else:
        print("⚠️  Some Access Override System tests FAILED!")
        return 1

if __name__ == "__main__":
    exit(main())