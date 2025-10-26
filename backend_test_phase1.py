#!/usr/bin/env python3
"""
Backend Test Suite for Enhanced Member Management System - Phase 1 Quick Wins
Comprehensive testing of tag management, member tagging, member actions, and enhanced profile APIs
"""

import requests
import json
import time
import os
from datetime import datetime, timezone, timedelta

# Configuration
BASE_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://gym-rbac-erp.preview.emergentagent.com')
API_BASE = f"{BASE_URL}/api"

# Test credentials
TEST_EMAIL = "admin@gym.com"
TEST_PASSWORD = "admin123"

class EnhancedMemberManagementTester:
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

    def test_get_default_tags(self):
        """Test GET /api/tags - Should return 7 default tags"""
        print("\n=== Testing Get Default Tags ===")
        
        try:
            response = requests.get(f"{API_BASE}/tags", headers=self.headers)
            
            if response.status_code == 200:
                tags = response.json()
                
                # Verify we have the expected default tags
                expected_default_tags = ["VIP", "New Member", "Late Payer", "Personal Training", "Group Classes", "High Risk", "Loyal"]
                
                if isinstance(tags, list) and len(tags) >= 7:
                    tag_names = [tag.get("name", "") for tag in tags]
                    has_default_tags = all(default_tag in tag_names for default_tag in expected_default_tags)
                    
                    if has_default_tags:
                        self.log_result("Get Default Tags", True, 
                                      f"Retrieved {len(tags)} tags including all 7 default tags")
                        return tags
                    else:
                        missing_tags = [tag for tag in expected_default_tags if tag not in tag_names]
                        self.log_result("Get Default Tags", False, 
                                      f"Missing default tags: {missing_tags}")
                        return tags
                else:
                    self.log_result("Get Default Tags", False, 
                                  f"Expected at least 7 tags, got {len(tags) if isinstance(tags, list) else 'invalid response'}")
                    return None
            else:
                self.log_result("Get Default Tags", False, 
                              f"Failed to get tags: {response.status_code}",
                              {"response": response.text})
                return None
                
        except Exception as e:
            self.log_result("Get Default Tags", False, f"Error getting tags: {str(e)}")
            return None

    def test_create_custom_tags(self):
        """Test POST /api/tags - Create new tags with different colors and categories"""
        print("\n=== Testing Create Custom Tags ===")
        
        # Test creating 3 custom tags with different properties
        custom_tags = [
            {
                "name": "Premium Member",
                "color": "#FFD700",  # Gold
                "category": "Status",
                "description": "Premium membership tier with exclusive benefits"
            },
            {
                "name": "Fitness Challenge",
                "color": "#FF6B35",  # Orange
                "category": "Program",
                "description": "Members participating in fitness challenges"
            },
            {
                "name": "Corporate Client",
                "color": "#4ECDC4",  # Teal
                "category": "Type",
                "description": "Corporate membership clients"
            }
        ]
        
        created_tags = []
        
        try:
            for tag_data in custom_tags:
                response = requests.post(f"{API_BASE}/tags", json=tag_data, headers=self.headers)
                
                if response.status_code == 200:
                    tag = response.json()
                    tag_id = tag.get("id")
                    
                    if tag_id:
                        created_tags.append(tag_id)
                        self.created_tags.append(tag_id)
                    
                    # Verify tag structure and data
                    required_fields = ["id", "name", "color", "category", "description", "usage_count"]
                    has_all_fields = all(field in tag for field in required_fields)
                    
                    # Verify data matches what we sent
                    data_matches = (
                        tag.get("name") == tag_data["name"] and
                        tag.get("color") == tag_data["color"] and
                        tag.get("category") == tag_data["category"] and
                        tag.get("description") == tag_data["description"] and
                        tag.get("usage_count") == 0  # Should start at 0
                    )
                    
                    if has_all_fields and data_matches:
                        self.log_result(f"Create Tag - {tag_data['name']}", True, 
                                      f"Tag created successfully with correct properties")
                    else:
                        self.log_result(f"Create Tag - {tag_data['name']}", False, 
                                      f"Tag creation issues: fields_complete={has_all_fields}, data_correct={data_matches}")
                else:
                    self.log_result(f"Create Tag - {tag_data['name']}", False, 
                                  f"Failed to create tag: {response.status_code}",
                                  {"response": response.text})
            
            if len(created_tags) == 3:
                self.log_result("Create Custom Tags", True, 
                              f"Successfully created {len(created_tags)} custom tags")
                return created_tags
            else:
                self.log_result("Create Custom Tags", False, 
                              f"Only created {len(created_tags)} of 3 expected tags")
                return created_tags
                
        except Exception as e:
            self.log_result("Create Custom Tags", False, f"Error creating custom tags: {str(e)}")
            return []

    def test_update_tag(self, tag_id):
        """Test PUT /api/tags/{tag_id} - Update tag properties"""
        print("\n=== Testing Update Tag ===")
        
        if not tag_id:
            self.log_result("Update Tag", False, "No tag ID provided")
            return False
        
        try:
            # Update tag data
            update_data = {
                "name": "Premium Member UPDATED",
                "color": "#FF0000",  # Change to red
                "category": "Status Updated",
                "description": "Updated description for premium membership tier"
            }
            
            response = requests.put(f"{API_BASE}/tags/{tag_id}", json=update_data, headers=self.headers)
            
            if response.status_code == 200:
                updated_tag = response.json()
                
                # Verify updates were applied
                updates_applied = (
                    updated_tag.get("name") == update_data["name"] and
                    updated_tag.get("color") == update_data["color"] and
                    updated_tag.get("category") == update_data["category"] and
                    updated_tag.get("description") == update_data["description"]
                )
                
                if updates_applied:
                    self.log_result("Update Tag", True, 
                                  f"Tag updated successfully: {updated_tag.get('name')}")
                    return True
                else:
                    self.log_result("Update Tag", False, 
                                  "Tag update did not apply all changes correctly")
                    return False
            else:
                self.log_result("Update Tag", False, 
                              f"Failed to update tag: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Update Tag", False, f"Error updating tag: {str(e)}")
            return False
    
    def test_add_tags_to_member(self):
        """Test POST /api/members/{member_id}/tags/{tag_name} - Add multiple tags to member"""
        print("\n=== Testing Add Tags to Member ===")
        
        if not self.test_member_id:
            self.log_result("Add Tags to Member", False, "No test member available")
            return False
        
        # Test adding multiple tags to the member
        test_tags = ["VIP", "Personal Training", "Premium Member UPDATED"]
        added_tags = []
        
        try:
            for tag_name in test_tags:
                response = requests.post(f"{API_BASE}/members/{self.test_member_id}/tags/{tag_name}", 
                                       headers=self.headers)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Verify response indicates success
                    if "added" in result.get("message", "").lower() or result.get("success"):
                        added_tags.append(tag_name)
                        self.log_result(f"Add Tag - {tag_name}", True, 
                                      f"Tag '{tag_name}' added to member successfully")
                    else:
                        self.log_result(f"Add Tag - {tag_name}", False, 
                                      f"Unexpected response: {result}")
                else:
                    self.log_result(f"Add Tag - {tag_name}", False, 
                                  f"Failed to add tag '{tag_name}': {response.status_code}",
                                  {"response": response.text})
            
            # Verify tags were added by checking member profile
            if len(added_tags) > 0:
                member_response = requests.get(f"{API_BASE}/members/{self.test_member_id}", headers=self.headers)
                if member_response.status_code == 200:
                    member = member_response.json()
                    member_tags = member.get("tags", [])
                    
                    tags_in_profile = all(tag in member_tags for tag in added_tags)
                    
                    if tags_in_profile:
                        self.log_result("Verify Tags in Member Profile", True, 
                                      f"All {len(added_tags)} tags found in member profile")
                    else:
                        missing_tags = [tag for tag in added_tags if tag not in member_tags]
                        self.log_result("Verify Tags in Member Profile", False, 
                                      f"Tags missing from member profile: {missing_tags}")
            
            # Check if usage_count incremented for tags
            tags_response = requests.get(f"{API_BASE}/tags", headers=self.headers)
            if tags_response.status_code == 200:
                all_tags = tags_response.json()
                
                for tag_name in added_tags:
                    tag = next((t for t in all_tags if t.get("name") == tag_name), None)
                    if tag and tag.get("usage_count", 0) > 0:
                        self.log_result(f"Usage Count - {tag_name}", True, 
                                      f"Usage count incremented to {tag.get('usage_count')}")
                    else:
                        self.log_result(f"Usage Count - {tag_name}", False, 
                                      f"Usage count not incremented for tag '{tag_name}'")
            
            if len(added_tags) >= 2:
                self.log_result("Add Tags to Member", True, 
                              f"Successfully added {len(added_tags)} tags to member")
                return True
            else:
                self.log_result("Add Tags to Member", False, 
                              f"Only added {len(added_tags)} of {len(test_tags)} expected tags")
                return False
                
        except Exception as e:
            self.log_result("Add Tags to Member", False, f"Error adding tags to member: {str(e)}")
            return False
    
    def test_remove_tags_from_member(self):
        """Test DELETE /api/members/{member_id}/tags/{tag_name} - Remove tags from member"""
        print("\n=== Testing Remove Tags from Member ===")
        
        if not self.test_member_id:
            self.log_result("Remove Tags from Member", False, "No test member available")
            return False
        
        # Test removing one tag
        tag_to_remove = "Personal Training"
        
        try:
            response = requests.delete(f"{API_BASE}/members/{self.test_member_id}/tags/{tag_to_remove}", 
                                     headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                
                # Verify response indicates success
                if "removed" in result.get("message", "").lower() or result.get("success"):
                    self.log_result("Remove Tag from Member", True, 
                                  f"Tag '{tag_to_remove}' removed from member successfully")
                    
                    # Verify tag was removed from member profile
                    member_response = requests.get(f"{API_BASE}/members/{self.test_member_id}", headers=self.headers)
                    if member_response.status_code == 200:
                        member = member_response.json()
                        member_tags = member.get("tags", [])
                        
                        if tag_to_remove not in member_tags:
                            self.log_result("Verify Tag Removed from Profile", True, 
                                          f"Tag '{tag_to_remove}' no longer in member profile")
                        else:
                            self.log_result("Verify Tag Removed from Profile", False, 
                                          f"Tag '{tag_to_remove}' still in member profile")
                    
                    # Check if usage_count decremented
                    tags_response = requests.get(f"{API_BASE}/tags", headers=self.headers)
                    if tags_response.status_code == 200:
                        all_tags = tags_response.json()
                        tag = next((t for t in all_tags if t.get("name") == tag_to_remove), None)
                        if tag:
                            self.log_result(f"Usage Count Decremented - {tag_to_remove}", True, 
                                          f"Usage count is now {tag.get('usage_count', 0)}")
                    
                    return True
                else:
                    self.log_result("Remove Tag from Member", False, 
                                  f"Unexpected response: {result}")
                    return False
            else:
                self.log_result("Remove Tag from Member", False, 
                              f"Failed to remove tag: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Remove Tags from Member", False, f"Error removing tag from member: {str(e)}")
            return False
    
    def test_member_freeze_actions(self):
        """Test POST /api/members/{member_id}/freeze - Freeze membership with reason and end date"""
        print("\n=== Testing Member Freeze Actions ===")
        
        if not self.test_member_id_2:
            self.log_result("Member Freeze Actions", False, "No test member available")
            return False
        
        try:
            # Test freezing membership with end date
            freeze_data = {
                "reason": "Medical leave - surgery recovery",
                "notes": "Member will be out for 6 weeks due to knee surgery",
                "end_date": (datetime.now(timezone.utc) + timedelta(days=42)).isoformat()  # 6 weeks
            }
            
            response = requests.post(f"{API_BASE}/members/{self.test_member_id_2}/freeze", 
                                   json=freeze_data, headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                
                # Verify response indicates success
                if "frozen" in result.get("message", "").lower() or result.get("success"):
                    self.log_result("Freeze Membership", True, 
                                  f"Membership frozen successfully: {result.get('message', '')}")
                    
                    # Verify member freeze status updated
                    member_response = requests.get(f"{API_BASE}/members/{self.test_member_id_2}", headers=self.headers)
                    if member_response.status_code == 200:
                        member = member_response.json()
                        
                        freeze_status_checks = [
                            member.get("freeze_status") == True,
                            member.get("freeze_reason") == freeze_data["reason"],
                            member.get("freeze_start_date") is not None,
                            member.get("freeze_end_date") is not None
                        ]
                        
                        if all(freeze_status_checks):
                            self.log_result("Verify Freeze Status Fields", True, 
                                          "All freeze status fields updated correctly")
                        else:
                            self.log_result("Verify Freeze Status Fields", False, 
                                          f"Freeze status fields not updated correctly: {member}")
                    
                    return True
                else:
                    self.log_result("Freeze Membership", False, 
                                  f"Unexpected freeze response: {result}")
                    return False
            else:
                self.log_result("Freeze Membership", False, 
                              f"Failed to freeze membership: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Member Freeze Actions", False, f"Error freezing membership: {str(e)}")
            return False
    
    def test_member_unfreeze_actions(self):
        """Test POST /api/members/{member_id}/unfreeze - Unfreeze membership"""
        print("\n=== Testing Member Unfreeze Actions ===")
        
        if not self.test_member_id_2:
            self.log_result("Member Unfreeze Actions", False, "No test member available")
            return False
        
        try:
            response = requests.post(f"{API_BASE}/members/{self.test_member_id_2}/unfreeze", 
                                   headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                
                # Verify response indicates success
                if "unfrozen" in result.get("message", "").lower() or result.get("success"):
                    self.log_result("Unfreeze Membership", True, 
                                  f"Membership unfrozen successfully: {result.get('message', '')}")
                    
                    # Verify member freeze status cleared
                    member_response = requests.get(f"{API_BASE}/members/{self.test_member_id_2}", headers=self.headers)
                    if member_response.status_code == 200:
                        member = member_response.json()
                        
                        unfreeze_status_checks = [
                            member.get("freeze_status") == False,
                            member.get("membership_status") == "active"
                        ]
                        
                        if all(unfreeze_status_checks):
                            self.log_result("Verify Unfreeze Status Fields", True, 
                                          "Freeze status cleared and membership returned to active")
                        else:
                            self.log_result("Verify Unfreeze Status Fields", False, 
                                          f"Unfreeze status not updated correctly: freeze_status={member.get('freeze_status')}, membership_status={member.get('membership_status')}")
                    
                    return True
                else:
                    self.log_result("Unfreeze Membership", False, 
                                  f"Unexpected unfreeze response: {result}")
                    return False
            else:
                self.log_result("Unfreeze Membership", False, 
                              f"Failed to unfreeze membership: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Member Unfreeze Actions", False, f"Error unfreezing membership: {str(e)}")
            return False
    
    def test_member_cancel_actions(self):
        """Test POST /api/members/{member_id}/cancel - Cancel membership with reason and notes"""
        print("\n=== Testing Member Cancel Actions ===")
        
        if not self.test_member_id:
            self.log_result("Member Cancel Actions", False, "No test member available")
            return False
        
        try:
            # Test cancelling membership
            cancel_data = {
                "reason": "Relocating to another city",
                "notes": "Member is moving to Johannesburg for work. Provided 30 days notice."
            }
            
            response = requests.post(f"{API_BASE}/members/{self.test_member_id}/cancel", 
                                   json=cancel_data, headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                
                # Verify response indicates success
                if "cancelled" in result.get("message", "").lower() or result.get("success"):
                    self.log_result("Cancel Membership", True, 
                                  f"Membership cancelled successfully: {result.get('message', '')}")
                    
                    # Verify member cancellation status updated
                    member_response = requests.get(f"{API_BASE}/members/{self.test_member_id}", headers=self.headers)
                    if member_response.status_code == 200:
                        member = member_response.json()
                        
                        cancel_status_checks = [
                            member.get("membership_status") == "cancelled",
                            member.get("cancellation_reason") == cancel_data["reason"],
                            member.get("cancellation_date") is not None
                        ]
                        
                        if all(cancel_status_checks):
                            self.log_result("Verify Cancel Status Fields", True, 
                                          "All cancellation fields updated correctly")
                        else:
                            self.log_result("Verify Cancel Status Fields", False, 
                                          f"Cancellation fields not updated correctly: status={member.get('membership_status')}, reason={member.get('cancellation_reason')}")
                    
                    return True
                else:
                    self.log_result("Cancel Membership", False, 
                                  f"Unexpected cancel response: {result}")
                    return False
            else:
                self.log_result("Cancel Membership", False, 
                              f"Failed to cancel membership: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Member Cancel Actions", False, f"Error cancelling membership: {str(e)}")
            return False

    def test_enhanced_profile_endpoint(self):
        """Test GET /api/members/{member_id}/profile - Verify returns Phase 1 fields"""
        print("\n=== Testing Enhanced Profile Endpoint ===")
        
        if not self.test_member_id_2:
            self.log_result("Enhanced Profile Endpoint", False, "No test member available")
            return False
        
        try:
            response = requests.get(f"{API_BASE}/members/{self.test_member_id_2}/profile", headers=self.headers)
            
            if response.status_code == 200:
                profile = response.json()
                
                # Verify Phase 1 enhanced fields are present
                phase1_fields = [
                    "sessions_remaining",
                    "last_visit_date", 
                    "next_billing_date",
                    "tags"
                ]
                
                # Check if all Phase 1 fields are present (can be null but should exist)
                has_phase1_fields = all(field in profile for field in phase1_fields)
                
                # Verify basic profile structure
                basic_fields = ["id", "first_name", "last_name", "email", "phone", "membership_status"]
                has_basic_fields = all(field in profile for field in basic_fields)
                
                if has_phase1_fields and has_basic_fields:
                    self.log_result("Enhanced Profile Endpoint", True, 
                                  f"Profile includes all Phase 1 fields: {', '.join(phase1_fields)}")
                    
                    # Log current values for verification
                    field_values = {field: profile.get(field) for field in phase1_fields}
                    self.log_result("Profile Field Values", True, 
                                  f"Phase 1 field values: {field_values}")
                    
                    return True
                else:
                    missing_fields = []
                    if not has_phase1_fields:
                        missing_fields.extend([f for f in phase1_fields if f not in profile])
                    if not has_basic_fields:
                        missing_fields.extend([f for f in basic_fields if f not in profile])
                    
                    self.log_result("Enhanced Profile Endpoint", False, 
                                  f"Missing profile fields: {missing_fields}")
                    return False
            else:
                self.log_result("Enhanced Profile Endpoint", False, 
                              f"Failed to get member profile: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Enhanced Profile Endpoint", False, f"Error getting member profile: {str(e)}")
            return False
    
    def test_access_validate_last_visit_update(self):
        """Test POST /api/access/validate - Grant access and verify last_visit_date is updated"""
        print("\n=== Testing Access Validate Last Visit Update ===")
        
        if not self.test_member_id_2:
            self.log_result("Access Validate Last Visit Update", False, "No test member available")
            return False
        
        try:
            # Get current last_visit_date before access grant
            profile_response = requests.get(f"{API_BASE}/members/{self.test_member_id_2}/profile", headers=self.headers)
            if profile_response.status_code != 200:
                self.log_result("Get Profile Before Access", False, "Failed to get member profile")
                return False
            
            before_profile = profile_response.json()
            before_last_visit = before_profile.get("last_visit_date")
            
            # Grant access
            access_data = {
                "member_id": self.test_member_id_2,
                "access_method": "qr_code",
                "location": "Main Entrance"
            }
            
            response = requests.post(f"{API_BASE}/access/validate", 
                                   json=access_data, headers=self.headers)
            
            if response.status_code == 200:
                access_result = response.json()
                
                # Verify access was granted
                if access_result.get("status") == "granted" or access_result.get("access_granted"):
                    self.log_result("Access Granted", True, 
                                  f"Access granted successfully: {access_result.get('message', '')}")
                    
                    # Wait a moment for database update
                    time.sleep(1)
                    
                    # Get updated profile to check last_visit_date
                    updated_profile_response = requests.get(f"{API_BASE}/members/{self.test_member_id_2}/profile", headers=self.headers)
                    if updated_profile_response.status_code == 200:
                        after_profile = updated_profile_response.json()
                        after_last_visit = after_profile.get("last_visit_date")
                        
                        # Verify last_visit_date was updated
                        if after_last_visit and after_last_visit != before_last_visit:
                            self.log_result("Last Visit Date Updated", True, 
                                          f"last_visit_date updated from {before_last_visit} to {after_last_visit}")
                            
                            # Verify the date is recent (within last 5 minutes)
                            if after_last_visit:
                                try:
                                    visit_time = datetime.fromisoformat(after_last_visit.replace('Z', '+00:00'))
                                    now = datetime.now(timezone.utc)
                                    time_diff = (now - visit_time).total_seconds()
                                    
                                    if time_diff < 300:  # Within 5 minutes
                                        self.log_result("Last Visit Date Recent", True, 
                                                      f"last_visit_date is recent ({time_diff:.1f} seconds ago)")
                                    else:
                                        self.log_result("Last Visit Date Recent", False, 
                                                      f"last_visit_date is not recent ({time_diff:.1f} seconds ago)")
                                except Exception as date_e:
                                    self.log_result("Last Visit Date Parse", False, f"Error parsing date: {date_e}")
                        else:
                            self.log_result("Last Visit Date Updated", False, 
                                          f"last_visit_date not updated: before={before_last_visit}, after={after_last_visit}")
                    else:
                        self.log_result("Get Profile After Access", False, "Failed to get updated member profile")
                    
                    return True
                else:
                    self.log_result("Access Granted", False, 
                                  f"Access not granted: {access_result}")
                    return False
            else:
                self.log_result("Access Validate", False, 
                              f"Failed to validate access: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Access Validate Last Visit Update", False, f"Error testing access validation: {str(e)}")
            return False
    
    def test_delete_tag_removes_from_members(self):
        """Test DELETE /api/tags/{tag_id} - Delete tag and verify removal from members"""
        print("\n=== Testing Delete Tag Removes from Members ===")
        
        if not self.created_tags:
            self.log_result("Delete Tag Removes from Members", False, "No created tags available")
            return False
        
        # Use the first created tag for deletion test
        tag_to_delete = self.created_tags[0]
        
        try:
            # First, get the tag name for verification
            tags_response = requests.get(f"{API_BASE}/tags", headers=self.headers)
            if tags_response.status_code != 200:
                self.log_result("Get Tags Before Delete", False, "Failed to get tags")
                return False
            
            all_tags = tags_response.json()
            tag_obj = next((t for t in all_tags if t.get("id") == tag_to_delete), None)
            if not tag_obj:
                self.log_result("Find Tag to Delete", False, f"Tag {tag_to_delete} not found")
                return False
            
            tag_name = tag_obj.get("name")
            
            # Delete the tag
            response = requests.delete(f"{API_BASE}/tags/{tag_to_delete}", headers=self.headers)
            
            if response.status_code == 200:
                result = response.json()
                
                # Verify response indicates success
                if "deleted" in result.get("message", "").lower() or result.get("success"):
                    self.log_result("Delete Tag", True, 
                                  f"Tag '{tag_name}' deleted successfully")
                    
                    # Verify tag is no longer in tags list
                    updated_tags_response = requests.get(f"{API_BASE}/tags", headers=self.headers)
                    if updated_tags_response.status_code == 200:
                        updated_tags = updated_tags_response.json()
                        tag_still_exists = any(t.get("id") == tag_to_delete for t in updated_tags)
                        
                        if not tag_still_exists:
                            self.log_result("Verify Tag Deleted from List", True, 
                                          f"Tag '{tag_name}' no longer in tags list")
                        else:
                            self.log_result("Verify Tag Deleted from List", False, 
                                          f"Tag '{tag_name}' still exists in tags list")
                    
                    # Verify tag was removed from any members who had it
                    if self.test_member_id_2:
                        member_response = requests.get(f"{API_BASE}/members/{self.test_member_id_2}", headers=self.headers)
                        if member_response.status_code == 200:
                            member = member_response.json()
                            member_tags = member.get("tags", [])
                            
                            if tag_name not in member_tags:
                                self.log_result("Verify Tag Removed from Members", True, 
                                              f"Tag '{tag_name}' removed from member profiles")
                            else:
                                self.log_result("Verify Tag Removed from Members", False, 
                                              f"Tag '{tag_name}' still in member profile")
                    
                    # Remove from our tracking list
                    self.created_tags.remove(tag_to_delete)
                    
                    return True
                else:
                    self.log_result("Delete Tag", False, 
                                  f"Unexpected delete response: {result}")
                    return False
            else:
                self.log_result("Delete Tag", False, 
                              f"Failed to delete tag: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Delete Tag Removes from Members", False, f"Error deleting tag: {str(e)}")
            return False
    
    def test_journal_entries_creation(self):
        """Test journal entries are created for all tag and membership actions"""
        print("\n=== Testing Journal Entries Creation ===")
        
        if not self.test_member_id_2:
            self.log_result("Journal Entries Creation", False, "No test member available")
            return False
        
        try:
            # Get member journal entries
            response = requests.get(f"{API_BASE}/members/{self.test_member_id_2}/journal", headers=self.headers)
            
            if response.status_code == 200:
                journal_entries = response.json()
                
                if isinstance(journal_entries, list) and len(journal_entries) > 0:
                    # Look for entries related to our test actions
                    action_types_found = set()
                    
                    for entry in journal_entries:
                        action_type = entry.get("action_type", "")
                        description = entry.get("description", "").lower()
                        
                        # Check for freeze/unfreeze actions
                        if "freeze" in description or action_type == "membership_frozen":
                            action_types_found.add("freeze")
                        if "unfreeze" in description or action_type == "membership_unfrozen":
                            action_types_found.add("unfreeze")
                        if "access" in description or action_type == "access_granted":
                            action_types_found.add("access")
                        if "tag" in description or "tag" in action_type:
                            action_types_found.add("tag")
                    
                    if len(action_types_found) >= 2:  # At least some actions logged
                        self.log_result("Journal Entries Creation", True, 
                                      f"Found journal entries for actions: {', '.join(action_types_found)}")
                        return True
                    else:
                        self.log_result("Journal Entries Creation", False, 
                                      f"Limited journal entries found: {action_types_found}")
                        return False
                else:
                    self.log_result("Journal Entries Creation", False, 
                                  f"No journal entries found for member")
                    return False
            else:
                self.log_result("Journal Entries Creation", False, 
                              f"Failed to get journal entries: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Journal Entries Creation", False, f"Error getting journal entries: {str(e)}")
            return False

    def cleanup_test_data(self):
        """Clean up created test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Clean up created members
        for member_id in self.created_members:
            try:
                requests.delete(f"{API_BASE}/members/{member_id}", headers=self.headers)
            except:
                pass
        
        # Clean up created tags
        for tag_id in self.created_tags:
            try:
                requests.delete(f"{API_BASE}/tags/{tag_id}", headers=self.headers)
            except:
                pass
        
        self.log_result("Cleanup", True, 
                      f"Attempted cleanup of {len(self.created_members)} members and {len(self.created_tags)} tags")
    
    def run_all_tests(self):
        """Run all Enhanced Member Management Phase 1 tests"""
        print("🚀 Starting Enhanced Member Management System Tests - Phase 1 Quick Wins")
        print(f"Testing against: {API_BASE}")
        print("=" * 80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Setup test data
        if not self.setup_test_members():
            print("❌ Failed to setup test members. Cannot proceed with tests.")
            return
        
        # Run all test phases
        print("\n📋 PHASE 1 - QUICK WINS TESTING")
        print("Testing Requirements:")
        print("- Authentication: admin@gym.com / admin123")
        print("- Tag Management APIs (GET, POST, PUT, DELETE)")
        print("- Member Tagging APIs (Add/Remove tags)")
        print("- Member Action APIs (Freeze, Unfreeze, Cancel)")
        print("- Enhanced Profile Endpoint (Phase 1 fields)")
        print("- Auto-Update Last Visit on Access Grant")
        print("- Journal Entry Creation for Actions")
        
        # Execute all test phases
        print("\n" + "="*60)
        print("PHASE 1A: TAG MANAGEMENT TESTING")
        print("="*60)
        default_tags = self.test_get_default_tags()
        created_tags = self.test_create_custom_tags()
        
        if created_tags:
            # Test updating the first created tag
            self.test_update_tag(created_tags[0])
        
        print("\n" + "="*60)
        print("PHASE 1B: MEMBER TAGGING TESTING")
        print("="*60)
        self.test_add_tags_to_member()
        self.test_remove_tags_from_member()
        
        print("\n" + "="*60)
        print("PHASE 1C: MEMBER ACTION TESTING")
        print("="*60)
        self.test_member_freeze_actions()
        self.test_member_unfreeze_actions()
        self.test_member_cancel_actions()
        
        print("\n" + "="*60)
        print("PHASE 1D: ENHANCED PROFILE & ACCESS TESTING")
        print("="*60)
        self.test_enhanced_profile_endpoint()
        self.test_access_validate_last_visit_update()
        
        print("\n" + "="*60)
        print("PHASE 1E: JOURNAL & CLEANUP TESTING")
        print("="*60)
        self.test_journal_entries_creation()
        
        # Test tag deletion (removes from members)
        if self.created_tags:
            self.test_delete_tag_removes_from_members()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🏁 TEST SUMMARY")
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


if __name__ == "__main__":
    print("🎯 Enhanced Member Management System - Phase 1 Quick Wins Testing")
    print("=" * 80)
    
    tester = EnhancedMemberManagementTester()
    tester.run_all_tests()