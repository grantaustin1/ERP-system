#!/usr/bin/env python3
"""
Backend Test Suite - Re-test Phase 1 Quick Wins - Priority Failed Tests
Focus on Member Cancel API and Enhanced Profile Endpoint
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

class PriorityTestRunner:
    def __init__(self):
        self.token = None
        self.headers = {}
        self.test_results = []
        self.created_members = []  # Track created members for cleanup
        self.created_tags = []  # Track created tags for cleanup
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
        """Create test members for enhanced member management testing"""
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
            timestamp = int(time.time())
            member_data_1 = {
                "first_name": "Alice",
                "last_name": "TestMember",
                "email": f"alice.testmember.{timestamp}@example.com",
                "phone": f"082111{timestamp % 10000:04d}",
                "membership_type_id": membership_type_id
            }
            
            response = requests.post(f"{API_BASE}/members", json=member_data_1, headers=self.headers)
            if response.status_code == 200:
                member = response.json()
                self.test_member_id = member["id"]
                self.created_members.append(member["id"])
                self.log_result("Setup Test Member 1", True, f"Created test member 1: {self.test_member_id}")
            else:
                self.log_result("Setup Test Member 1", False, f"Failed to create test member 1: {response.status_code}")
                return False
            
            # Create second test member
            member_data_2 = {
                "first_name": "Bob",
                "last_name": "TestMember",
                "email": f"bob.testmember.{timestamp}@example.com",
                "phone": f"082222{timestamp % 10000:04d}",
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
                self.log_result("Setup Test Member 2", False, f"Failed to create test member 2: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Setup Test Members", False, f"Error creating test members: {str(e)}")
            return False
    
    
    def test_member_cancel_api_priority(self):
        """PRIORITY TEST: Member Cancel API - Test TypeError fix and proper field updates"""
        print("\n=== PRIORITY TEST: Member Cancel API ===")
        
        if not self.test_member_id:
            self.log_result("Member Cancel API", False, "No test member available")
            return False
        
        # Test 1: Cancel member with NULL notes field
        try:
            # First ensure member has NULL notes
            await_result = requests.patch(f"{API_BASE}/members/{self.test_member_id}", 
                                        json={"notes": None}, headers=self.headers)
            
            cancel_data = {
                "reason": "Moving to another city",
                "notes": "Member relocating for work - 30 days notice provided"
            }
            
            response = requests.post(f"{API_BASE}/members/{self.test_member_id}/cancel", 
                                   json=cancel_data, headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                
                # Verify response indicates success
                if "cancelled" in result.get("message", "").lower():
                    self.log_result("Cancel Member with NULL Notes", True, 
                                  f"Successfully cancelled member: {result.get('message')}")
                    
                    # Verify member fields updated correctly
                    member_response = requests.get(f"{API_BASE}/members/{self.test_member_id}", headers=self.headers)
                    if member_response.status_code == 200:
                        member = member_response.json()
                        
                        # Check all required fields
                        checks = {
                            "membership_status": member.get("membership_status") == "cancelled",
                            "cancellation_reason": member.get("cancellation_reason") == cancel_data["reason"],
                            "cancellation_date": member.get("cancellation_date") is not None,
                            "notes_updated": cancel_data["notes"] in (member.get("notes") or "")
                        }
                        
                        if all(checks.values()):
                            self.log_result("Verify Cancel Fields - NULL Notes", True, 
                                          "All cancellation fields updated correctly")
                        else:
                            failed_checks = [k for k, v in checks.items() if not v]
                            self.log_result("Verify Cancel Fields - NULL Notes", False, 
                                          f"Failed checks: {failed_checks}")
                    
                    # Verify journal entry created
                    journal_response = requests.get(f"{API_BASE}/members/{self.test_member_id}/journal", headers=self.headers)
                    if journal_response.status_code == 200:
                        journal_entries = journal_response.json()
                        cancel_entry = next((e for e in journal_entries if "cancelled" in e.get("description", "").lower()), None)
                        
                        if cancel_entry:
                            self.log_result("Verify Cancel Journal Entry", True, 
                                          "Journal entry created for cancellation")
                        else:
                            self.log_result("Verify Cancel Journal Entry", False, 
                                          "No journal entry found for cancellation")
                    
                    return True
                else:
                    self.log_result("Cancel Member with NULL Notes", False, 
                                  f"Unexpected response: {result}")
                    return False
            else:
                self.log_result("Cancel Member with NULL Notes", False, 
                              f"Failed to cancel member: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Member Cancel API", False, f"Error testing cancel API: {str(e)}")
            return False
    
    def test_member_cancel_existing_notes(self):
        """Test Member Cancel API with existing notes"""
        print("\n=== Testing Member Cancel with Existing Notes ===")
        
        if not self.test_member_id_2:
            self.log_result("Member Cancel with Existing Notes", False, "No test member available")
            return False
        
        try:
            # First set existing notes on member
            existing_notes = "Previous notes: Member requested schedule change last month."
            update_response = requests.patch(f"{API_BASE}/members/{self.test_member_id_2}", 
                                           json={"notes": existing_notes}, headers=self.headers)
            
            if update_response.status_code != 200:
                self.log_result("Set Existing Notes", False, "Failed to set existing notes")
                return False
            
            # Now cancel with additional notes
            cancel_data = {
                "reason": "Financial difficulties",
                "notes": "Member unable to continue due to job loss. Offered payment plan but declined."
            }
            
            response = requests.post(f"{API_BASE}/members/{self.test_member_id_2}/cancel", 
                                   json=cancel_data, headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                
                if "cancelled" in result.get("message", "").lower():
                    self.log_result("Cancel Member with Existing Notes", True, 
                                  f"Successfully cancelled member: {result.get('message')}")
                    
                    # Verify notes were properly concatenated
                    member_response = requests.get(f"{API_BASE}/members/{self.test_member_id_2}", headers=self.headers)
                    if member_response.status_code == 200:
                        member = member_response.json()
                        final_notes = member.get("notes", "")
                        
                        # Check that both existing and new notes are present
                        has_existing = existing_notes in final_notes
                        has_new = cancel_data["notes"] in final_notes
                        
                        if has_existing and has_new:
                            self.log_result("Verify Notes Concatenation", True, 
                                          "Both existing and cancellation notes preserved")
                        else:
                            self.log_result("Verify Notes Concatenation", False, 
                                          f"Notes concatenation failed: existing={has_existing}, new={has_new}")
                    
                    return True
                else:
                    self.log_result("Cancel Member with Existing Notes", False, 
                                  f"Unexpected response: {result}")
                    return False
            else:
                self.log_result("Cancel Member with Existing Notes", False, 
                              f"Failed to cancel member: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Member Cancel with Existing Notes", False, f"Error testing cancel with existing notes: {str(e)}")
            return False
    
    def test_enhanced_profile_endpoint_priority(self):
        """PRIORITY TEST: Enhanced Profile Endpoint - Verify Phase 1 fields and structure"""
        print("\n=== PRIORITY TEST: Enhanced Profile Endpoint ===")
        
        if not self.test_member_id_2:
            self.log_result("Enhanced Profile Endpoint", False, "No test member available")
            return False
        
        try:
            response = requests.get(f"{API_BASE}/members/{self.test_member_id_2}/profile", headers=self.headers)
            
            if response.status_code == 200:
                profile = response.json()
                
                # CRITICAL: Verify member data is nested under "member" key
                has_member_key = "member" in profile
                if not has_member_key:
                    self.log_result("Profile Structure - Member Key", False, 
                                  "Profile response missing 'member' key")
                    return False
                else:
                    self.log_result("Profile Structure - Member Key", True, 
                                  "Profile response has 'member' key")
                
                # Verify Phase 1 enhanced fields are present at root level
                phase1_fields = [
                    "sessions_remaining",
                    "last_visit_date", 
                    "next_billing_date",
                    "tags"
                ]
                
                missing_phase1_fields = [field for field in phase1_fields if field not in profile]
                
                if not missing_phase1_fields:
                    self.log_result("Phase 1 Fields Present", True, 
                                  f"All Phase 1 fields present: {', '.join(phase1_fields)}")
                else:
                    self.log_result("Phase 1 Fields Present", False, 
                                  f"Missing Phase 1 fields: {missing_phase1_fields}")
                    return False
                
                # Verify standard member fields are present in member object
                member_data = profile.get("member", {})
                standard_fields = ["id", "first_name", "last_name", "email", "phone", "membership_status"]
                missing_standard_fields = [field for field in standard_fields if field not in member_data]
                
                if not missing_standard_fields:
                    self.log_result("Standard Member Fields", True, 
                                  f"All standard fields present in member object")
                else:
                    self.log_result("Standard Member Fields", False, 
                                  f"Missing standard fields in member object: {missing_standard_fields}")
                
                # Log current Phase 1 field values for verification
                phase1_values = {field: profile.get(field) for field in phase1_fields}
                self.log_result("Phase 1 Field Values", True, 
                              f"Current values: {json.dumps(phase1_values, indent=2)}")
                
                # Verify additional profile sections exist
                expected_sections = ["stats", "retention", "payment_progress"]
                missing_sections = [section for section in expected_sections if section not in profile]
                
                if not missing_sections:
                    self.log_result("Profile Sections Complete", True, 
                                  "All expected profile sections present")
                else:
                    self.log_result("Profile Sections Complete", False, 
                                  f"Missing profile sections: {missing_sections}")
                
                return len(missing_phase1_fields) == 0 and len(missing_standard_fields) == 0
                
            else:
                self.log_result("Enhanced Profile Endpoint", False, 
                              f"Failed to get member profile: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Enhanced Profile Endpoint", False, f"Error getting member profile: {str(e)}")
            return False
    
    def test_create_custom_tag_quick(self):
        """Quick test: Create one custom tag"""
        print("\n=== Quick Test: Create Custom Tag ===")
        
        try:
            tag_data = {
                "name": "Test Priority Tag",
                "color": "#FF5722",
                "category": "Testing",
                "description": "Tag created during priority testing"
            }
            
            response = requests.post(f"{API_BASE}/tags", json=tag_data, headers=self.headers)
            
            if response.status_code == 200:
                tag = response.json()
                tag_id = tag.get("id")
                
                if tag_id:
                    self.created_tags.append(tag_id)
                
                # Verify tag structure
                required_fields = ["id", "name", "color", "category", "description", "usage_count"]
                has_all_fields = all(field in tag for field in required_fields)
                
                if has_all_fields and tag.get("name") == tag_data["name"]:
                    self.log_result("Create Custom Tag", True, 
                                  f"Tag created successfully: {tag.get('name')}")
                    return tag_id
                else:
                    self.log_result("Create Custom Tag", False, 
                                  "Tag creation issues with structure or data")
                    return None
            else:
                self.log_result("Create Custom Tag", False, 
                              f"Failed to create tag: {response.status_code}",
                              {"response": response.text})
                return None
                
        except Exception as e:
            self.log_result("Create Custom Tag", False, f"Error creating tag: {str(e)}")
            return None
    
    def test_add_tag_to_member_quick(self, tag_name="Test Priority Tag"):
        """Quick test: Add tag to member"""
        print("\n=== Quick Test: Add Tag to Member ===")
        
        if not self.test_member_id:
            self.log_result("Add Tag to Member", False, "No test member available")
            return False
        
        try:
            response = requests.post(f"{API_BASE}/members/{self.test_member_id}/tags/{tag_name}", 
                                   headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                
                if "added" in result.get("message", "").lower():
                    self.log_result("Add Tag to Member", True, 
                                  f"Tag '{tag_name}' added successfully")
                    
                    # Verify tag in member profile
                    member_response = requests.get(f"{API_BASE}/members/{self.test_member_id}", headers=self.headers)
                    if member_response.status_code == 200:
                        member = member_response.json()
                        member_tags = member.get("tags", [])
                        
                        if tag_name in member_tags:
                            self.log_result("Verify Tag in Profile", True, 
                                          f"Tag '{tag_name}' found in member profile")
                            return True
                        else:
                            self.log_result("Verify Tag in Profile", False, 
                                          f"Tag '{tag_name}' not found in member profile")
                    
                    return True
                else:
                    self.log_result("Add Tag to Member", False, 
                                  f"Unexpected response: {result}")
                    return False
            else:
                self.log_result("Add Tag to Member", False, 
                              f"Failed to add tag: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Add Tag to Member", False, f"Error adding tag to member: {str(e)}")
            return False
    
    def test_freeze_unfreeze_quick(self):
        """Quick test: Freeze and Unfreeze membership"""
        print("\n=== Quick Test: Freeze/Unfreeze Membership ===")
        
        if not self.test_member_id_2:
            self.log_result("Freeze/Unfreeze Membership", False, "No test member available")
            return False
        
        try:
            # Test freeze
            freeze_data = {
                "reason": "Temporary medical leave",
                "notes": "Member recovering from surgery",
                "end_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
            }
            
            freeze_response = requests.post(f"{API_BASE}/members/{self.test_member_id_2}/freeze", 
                                          json=freeze_data, headers=self.headers)
            
            if freeze_response.status_code == 200:
                freeze_result = freeze_response.json()
                
                if "frozen" in freeze_result.get("message", "").lower():
                    self.log_result("Freeze Membership", True, 
                                  f"Membership frozen successfully")
                    
                    # Verify freeze status
                    member_response = requests.get(f"{API_BASE}/members/{self.test_member_id_2}", headers=self.headers)
                    if member_response.status_code == 200:
                        member = member_response.json()
                        
                        if member.get("freeze_status") == True:
                            self.log_result("Verify Freeze Status", True, 
                                          "Freeze status updated correctly")
                        else:
                            self.log_result("Verify Freeze Status", False, 
                                          f"Freeze status not updated: {member.get('freeze_status')}")
                    
                    # Test unfreeze
                    unfreeze_response = requests.post(f"{API_BASE}/members/{self.test_member_id_2}/unfreeze", 
                                                    headers=self.headers)
                    
                    if unfreeze_response.status_code == 200:
                        unfreeze_result = unfreeze_response.json()
                        
                        if "unfrozen" in unfreeze_result.get("message", "").lower():
                            self.log_result("Unfreeze Membership", True, 
                                          f"Membership unfrozen successfully")
                            
                            # Verify unfreeze status
                            member_response = requests.get(f"{API_BASE}/members/{self.test_member_id_2}", headers=self.headers)
                            if member_response.status_code == 200:
                                member = member_response.json()
                                
                                if member.get("freeze_status") == False:
                                    self.log_result("Verify Unfreeze Status", True, 
                                                  "Freeze status cleared correctly")
                                    return True
                                else:
                                    self.log_result("Verify Unfreeze Status", False, 
                                                  f"Freeze status not cleared: {member.get('freeze_status')}")
                        else:
                            self.log_result("Unfreeze Membership", False, 
                                          f"Unexpected unfreeze response: {unfreeze_result}")
                    else:
                        self.log_result("Unfreeze Membership", False, 
                                      f"Failed to unfreeze: {unfreeze_response.status_code}")
                else:
                    self.log_result("Freeze Membership", False, 
                                  f"Unexpected freeze response: {freeze_result}")
            else:
                self.log_result("Freeze Membership", False, 
                              f"Failed to freeze: {freeze_response.status_code}")
            
            return False
                
        except Exception as e:
            self.log_result("Freeze/Unfreeze Membership", False, f"Error testing freeze/unfreeze: {str(e)}")
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
        
        # Clean up created tags
        for tag_id in self.created_tags:
            try:
                response = requests.delete(f"{API_BASE}/tags/{tag_id}", headers=self.headers)
                if response.status_code == 200:
                    self.log_result(f"Cleanup Tag {tag_id[:8]}", True, "Tag deleted")
                else:
                    self.log_result(f"Cleanup Tag {tag_id[:8]}", False, f"Failed to delete: {response.status_code}")
            except Exception as e:
                self.log_result(f"Cleanup Tag {tag_id[:8]}", False, f"Error: {str(e)}")
    
    def run_priority_tests(self):
        """Run the priority tests focusing on previously failed items"""
        print("=" * 80)
        print("BACKEND TESTING - RE-TEST PHASE 1 QUICK WINS - PRIORITY FAILED TESTS")
        print("=" * 80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Setup test members
        if not self.setup_test_members():
            print("❌ Failed to setup test members. Cannot proceed with tests.")
            return False
        
        # Step 3: Run PRIORITY TESTS (Previously Failed)
        print("\n" + "=" * 60)
        print("PRIORITY TESTS - PREVIOUSLY FAILED")
        print("=" * 60)
        
        priority_results = []
        
        # 1. Member Cancel API - MUST TEST
        print("\n🔥 PRIORITY TEST 1: Member Cancel API")
        priority_results.append(self.test_member_cancel_api_priority())
        priority_results.append(self.test_member_cancel_existing_notes())
        
        # 2. Enhanced Profile Endpoint - MUST VERIFY
        print("\n🔥 PRIORITY TEST 2: Enhanced Profile Endpoint")
        priority_results.append(self.test_enhanced_profile_endpoint_priority())
        
        # Step 4: Run QUICK VERIFICATION TESTS
        print("\n" + "=" * 60)
        print("QUICK VERIFICATION TESTS")
        print("=" * 60)
        
        quick_results = []
        
        # Create custom tag
        tag_id = self.test_create_custom_tag_quick()
        if tag_id:
            quick_results.append(True)
            # Add tag to member
            quick_results.append(self.test_add_tag_to_member_quick())
        else:
            quick_results.append(False)
            quick_results.append(False)
        
        # Freeze/Unfreeze tests
        quick_results.append(self.test_freeze_unfreeze_quick())
        
        # Step 5: Generate Summary
        print("\n" + "=" * 80)
        print("TEST RESULTS SUMMARY")
        print("=" * 80)
        
        priority_passed = sum(priority_results)
        priority_total = len(priority_results)
        quick_passed = sum(quick_results)
        quick_total = len(quick_results)
        
        print(f"\n🔥 PRIORITY TESTS: {priority_passed}/{priority_total} PASSED")
        print(f"⚡ QUICK TESTS: {quick_passed}/{quick_total} PASSED")
        print(f"📊 OVERALL: {priority_passed + quick_passed}/{priority_total + quick_total} PASSED")
        
        # Detailed results
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        # Step 6: Cleanup
        self.cleanup_test_data()
        
        # Return success if all priority tests passed
        return priority_passed == priority_total

def main():
    """Main execution function"""
    tester = PriorityTestRunner()
    success = tester.run_priority_tests()
    
    if success:
        print("\n🎉 ALL PRIORITY TESTS PASSED!")
        exit(0)
    else:
        print("\n💥 SOME PRIORITY TESTS FAILED!")
        exit(1)

if __name__ == "__main__":
    main()
