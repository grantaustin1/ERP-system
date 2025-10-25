#!/usr/bin/env python3
"""
Backend Test Suite - Complimentary Membership Tracking System Testing
Focus on testing the Complimentary Membership APIs with role-based access control
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
ADMIN_EMAIL = "admin@gym.com"
ADMIN_PASSWORD = "admin123"

class ComplimentaryMembershipTestRunner:
    def __init__(self):
        self.admin_token = None
        self.admin_headers = {}
        self.test_results = []
        self.test_consultant_id = None
        self.created_types = []
        self.created_memberships = []
        self.test_type_id = None
        self.test_membership_id = None
        
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
        """Authenticate as admin"""
        try:
            # Authenticate as admin
            response = requests.post(f"{API_BASE}/auth/login", json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data["access_token"]
                self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
                self.log_result("Admin Authentication", True, "Successfully authenticated as admin")
                return True
            else:
                self.log_result("Admin Authentication", False, f"Failed to authenticate admin: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def get_consultant_id(self):
        """Get a consultant ID for testing"""
        try:
            response = requests.get(f"{API_BASE}/sales/consultants", headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                consultants = data.get("consultants", [])
                if consultants:
                    self.test_consultant_id = consultants[0]["id"]
                    self.log_result("Get Consultant ID", True, f"Found consultant: {consultants[0]['full_name']}")
                    return True
                else:
                    self.log_result("Get Consultant ID", False, "No consultants found")
                    return False
            else:
                self.log_result("Get Consultant ID", False, f"Failed to get consultants: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Get Consultant ID", False, f"Error getting consultant: {str(e)}")
            return False
    
    # ===================== COMPLIMENTARY MEMBERSHIP API TESTS =====================
    
    def test_get_complimentary_types(self):
        """Test GET /api/complimentary-types"""
        print("\n=== Testing GET /api/complimentary-types ===")
        
        try:
            response = requests.get(f"{API_BASE}/complimentary-types", headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify structure
                if "total" not in data or "types" not in data:
                    self.log_result("Get Complimentary Types Structure", False, "Missing 'total' or 'types' field")
                    return False
                
                types = data["types"]
                total = data["total"]
                
                # Verify total matches length
                if total != len(types):
                    self.log_result("Get Complimentary Types Count", False, f"Total {total} doesn't match types length {len(types)}")
                    return False
                
                self.log_result("Get Complimentary Types", True, f"Retrieved {total} complimentary types")
                return True
                
            else:
                self.log_result("Get Complimentary Types", False, f"Failed to get types: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Get Complimentary Types", False, f"Error testing get types: {str(e)}")
            return False
    
    def test_create_complimentary_type(self):
        """Test POST /api/complimentary-types"""
        print("\n=== Testing POST /api/complimentary-types ===")
        
        try:
            # Create first type: 3-Day Trial Pass
            type_data = {
                "name": "3-Day Trial Pass",
                "description": "Trial membership for new prospects",
                "time_limit_days": 7,
                "visit_limit": 3,
                "no_access_alert_days": 3,
                "notification_on_visits": [1, 2, 3],
                "is_active": True,
                "color": "#3b82f6",
                "icon": "🎁"
            }
            
            response = requests.post(f"{API_BASE}/complimentary-types", json=type_data, headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success") and "complimentary_type" in data:
                    created_type = data["complimentary_type"]
                    self.test_type_id = created_type["id"]
                    self.created_types.append(self.test_type_id)
                    
                    # Verify all fields are present
                    required_fields = ["id", "name", "description", "time_limit_days", "visit_limit", "no_access_alert_days", "notification_on_visits", "is_active", "color", "icon"]
                    for field in required_fields:
                        if field not in created_type:
                            self.log_result("Create Type Fields", False, f"Missing field: {field}")
                            return False
                    
                    self.log_result("Create Complimentary Type 1", True, f"Created type: {created_type['name']} with ID: {self.test_type_id}")
                    
                    # Create second type: Week Pass
                    type_data_2 = {
                        "name": "Week Pass",
                        "description": "One week unlimited access",
                        "time_limit_days": 7,
                        "visit_limit": 5,
                        "no_access_alert_days": 2,
                        "notification_on_visits": [1, 3, 5],
                        "is_active": True,
                        "color": "#10b981",
                        "icon": "📅"
                    }
                    
                    response2 = requests.post(f"{API_BASE}/complimentary-types", json=type_data_2, headers=self.admin_headers)
                    
                    if response2.status_code == 200:
                        data2 = response2.json()
                        if data2.get("success") and "complimentary_type" in data2:
                            created_type_2 = data2["complimentary_type"]
                            self.created_types.append(created_type_2["id"])
                            self.log_result("Create Complimentary Type 2", True, f"Created type: {created_type_2['name']}")
                            return True
                        else:
                            self.log_result("Create Complimentary Type 2", False, "Invalid response structure")
                            return False
                    else:
                        self.log_result("Create Complimentary Type 2", False, f"Failed to create second type: {response2.status_code}")
                        return False
                else:
                    self.log_result("Create Complimentary Type 1", False, "Invalid response structure")
                    return False
            else:
                self.log_result("Create Complimentary Type 1", False, f"Failed to create type: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Create Complimentary Type", False, f"Error testing create type: {str(e)}")
            return False
    
    def test_get_complimentary_types_after_create(self):
        """Test GET /api/complimentary-types after creating types"""
        print("\n=== Testing GET /api/complimentary-types (after create) ===")
        
        try:
            response = requests.get(f"{API_BASE}/complimentary-types", headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                types = data.get("types", [])
                
                # Should now have 2 types
                if len(types) >= 2:
                    # Verify our created types are present
                    type_names = [t["name"] for t in types]
                    if "3-Day Trial Pass" in type_names and "Week Pass" in type_names:
                        self.log_result("Get Types After Create", True, f"Found {len(types)} types including created ones")
                        return True
                    else:
                        self.log_result("Get Types After Create", False, "Created types not found in list")
                        return False
                else:
                    self.log_result("Get Types After Create", False, f"Expected at least 2 types, got {len(types)}")
                    return False
            else:
                self.log_result("Get Types After Create", False, f"Failed to get types: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Get Types After Create", False, f"Error testing get types after create: {str(e)}")
            return False
    
    def test_update_complimentary_type(self):
        """Test PUT /api/complimentary-types/{type_id}"""
        print("\n=== Testing PUT /api/complimentary-types/{type_id} ===")
        
        try:
            if not self.test_type_id:
                self.log_result("Update Type Setup", False, "No test type ID available")
                return False
            
            # Update the first type: change visit_limit to 5
            update_data = {
                "name": "3-Day Trial Pass",
                "description": "Trial membership for new prospects",
                "time_limit_days": 7,
                "visit_limit": 5,  # Changed from 3 to 5
                "no_access_alert_days": 3,
                "notification_on_visits": [1, 2, 3, 4, 5],
                "is_active": True,
                "color": "#3b82f6",
                "icon": "🎁"
            }
            
            response = requests.put(f"{API_BASE}/complimentary-types/{self.test_type_id}", json=update_data, headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_result("Update Complimentary Type", True, "Type updated successfully")
                    
                    # Verify the update by getting the type again
                    get_response = requests.get(f"{API_BASE}/complimentary-types", headers=self.admin_headers)
                    if get_response.status_code == 200:
                        get_data = get_response.json()
                        types = get_data.get("types", [])
                        
                        # Find our updated type
                        updated_type = None
                        for t in types:
                            if t["id"] == self.test_type_id:
                                updated_type = t
                                break
                        
                        if updated_type and updated_type["visit_limit"] == 5:
                            self.log_result("Verify Type Update", True, "Visit limit updated to 5")
                            return True
                        else:
                            self.log_result("Verify Type Update", False, "Update not reflected in data")
                            return False
                    else:
                        self.log_result("Verify Type Update", False, "Failed to verify update")
                        return False
                else:
                    self.log_result("Update Complimentary Type", False, "Update not successful")
                    return False
            else:
                self.log_result("Update Complimentary Type", False, f"Failed to update type: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Update Complimentary Type", False, f"Error testing update type: {str(e)}")
            return False
    
    def test_get_sales_consultants(self):
        """Test GET /api/sales/consultants"""
        print("\n=== Testing GET /api/sales/consultants ===")
        
        try:
            response = requests.get(f"{API_BASE}/sales/consultants", headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify structure
                if "total" not in data or "consultants" not in data:
                    self.log_result("Get Consultants Structure", False, "Missing 'total' or 'consultants' field")
                    return False
                
                consultants = data["consultants"]
                total = data["total"]
                
                if total > 0 and len(consultants) > 0:
                    # Save consultant ID for later use
                    self.test_consultant_id = consultants[0]["id"]
                    
                    # Verify consultant has required fields
                    consultant = consultants[0]
                    required_fields = ["id", "email", "full_name", "role"]
                    for field in required_fields:
                        if field not in consultant:
                            self.log_result("Consultant Fields", False, f"Missing field: {field}")
                            return False
                    
                    self.log_result("Get Sales Consultants", True, f"Found {total} consultants")
                    return True
                else:
                    self.log_result("Get Sales Consultants", False, "No consultants found")
                    return False
            else:
                self.log_result("Get Sales Consultants", False, f"Failed to get consultants: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Get Sales Consultants", False, f"Error testing get consultants: {str(e)}")
            return False
    
    def test_issue_complimentary_membership(self):
        """Test POST /api/complimentary-memberships"""
        print("\n=== Testing POST /api/complimentary-memberships ===")
        
        try:
            if not self.test_type_id or not self.test_consultant_id:
                self.log_result("Issue Membership Setup", False, "Missing test type ID or consultant ID")
                return False
            
            # Issue a complimentary pass
            membership_data = {
                "first_name": "Test",
                "last_name": "User",
                "email": "testuser@example.com",
                "phone": "+27123456789",
                "complimentary_type_id": self.test_type_id,
                "assigned_consultant_id": self.test_consultant_id,
                "notes": "Test pass for backend testing",
                "auto_create_lead": True
            }
            
            response = requests.post(f"{API_BASE}/complimentary-memberships", json=membership_data, headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success") and "complimentary_membership" in data:
                    membership = data["complimentary_membership"]
                    self.test_membership_id = membership["id"]
                    self.created_memberships.append(self.test_membership_id)
                    
                    # Verify membership fields
                    required_fields = ["id", "member_id", "member_name", "member_email", "member_phone", "complimentary_type_id", "visits_used", "visits_remaining", "status"]
                    for field in required_fields:
                        if field not in membership:
                            self.log_result("Membership Fields", False, f"Missing field: {field}")
                            return False
                    
                    # Verify initial values
                    if membership["visits_used"] != 0:
                        self.log_result("Initial Visits Used", False, f"Expected 0, got {membership['visits_used']}")
                        return False
                    
                    if membership["visits_remaining"] != 5:  # Updated visit limit
                        self.log_result("Initial Visits Remaining", False, f"Expected 5, got {membership['visits_remaining']}")
                        return False
                    
                    if membership["status"] != "active":
                        self.log_result("Initial Status", False, f"Expected 'active', got {membership['status']}")
                        return False
                    
                    # Verify lead was created
                    lead_id = data.get("lead_id")
                    if not lead_id:
                        self.log_result("Auto Create Lead", False, "No lead_id returned")
                        return False
                    
                    self.log_result("Issue Complimentary Membership", True, f"Issued membership with ID: {self.test_membership_id}, Lead ID: {lead_id}")
                    return True
                else:
                    self.log_result("Issue Complimentary Membership", False, "Invalid response structure")
                    return False
            else:
                self.log_result("Issue Complimentary Membership", False, f"Failed to issue membership: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Issue Complimentary Membership", False, f"Error testing issue membership: {str(e)}")
            return False
    
    def test_get_complimentary_memberships(self):
        """Test GET /api/complimentary-memberships"""
        print("\n=== Testing GET /api/complimentary-memberships ===")
        
        try:
            # Test without filters
            response = requests.get(f"{API_BASE}/complimentary-memberships", headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify structure
                if "total" not in data or "memberships" not in data:
                    self.log_result("Get Memberships Structure", False, "Missing 'total' or 'memberships' field")
                    return False
                
                memberships = data["memberships"]
                total = data["total"]
                
                if total >= 1 and len(memberships) >= 1:
                    # Verify our membership is in the list
                    membership_ids = [m["id"] for m in memberships]
                    if self.test_membership_id in membership_ids:
                        self.log_result("Get Memberships (All)", True, f"Found {total} memberships including test membership")
                    else:
                        self.log_result("Get Memberships (All)", False, "Test membership not found in list")
                        return False
                else:
                    self.log_result("Get Memberships (All)", False, f"Expected at least 1 membership, got {total}")
                    return False
            else:
                self.log_result("Get Memberships (All)", False, f"Failed to get memberships: {response.status_code}")
                return False
            
            # Test with status filter
            response = requests.get(f"{API_BASE}/complimentary-memberships?status=active", headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                memberships = data.get("memberships", [])
                
                # All should be active
                for membership in memberships:
                    if membership["status"] != "active":
                        self.log_result("Get Memberships (Status Filter)", False, f"Non-active membership in active filter: {membership['status']}")
                        return False
                
                self.log_result("Get Memberships (Status Filter)", True, f"Found {len(memberships)} active memberships")
            else:
                self.log_result("Get Memberships (Status Filter)", False, f"Failed to get active memberships: {response.status_code}")
                return False
            
            # Test with type filter
            if self.test_type_id:
                response = requests.get(f"{API_BASE}/complimentary-memberships?complimentary_type_id={self.test_type_id}", headers=self.admin_headers)
                
                if response.status_code == 200:
                    data = response.json()
                    memberships = data.get("memberships", [])
                    
                    # All should have our type ID
                    for membership in memberships:
                        if membership["complimentary_type_id"] != self.test_type_id:
                            self.log_result("Get Memberships (Type Filter)", False, f"Wrong type ID in filter: {membership['complimentary_type_id']}")
                            return False
                    
                    self.log_result("Get Memberships (Type Filter)", True, f"Found {len(memberships)} memberships with test type")
                else:
                    self.log_result("Get Memberships (Type Filter)", False, f"Failed to get memberships by type: {response.status_code}")
                    return False
            
            # Test with consultant filter
            if self.test_consultant_id:
                response = requests.get(f"{API_BASE}/complimentary-memberships?assigned_consultant_id={self.test_consultant_id}", headers=self.admin_headers)
                
                if response.status_code == 200:
                    data = response.json()
                    memberships = data.get("memberships", [])
                    
                    # All should have our consultant ID
                    for membership in memberships:
                        if membership["assigned_consultant_id"] != self.test_consultant_id:
                            self.log_result("Get Memberships (Consultant Filter)", False, f"Wrong consultant ID in filter: {membership['assigned_consultant_id']}")
                            return False
                    
                    self.log_result("Get Memberships (Consultant Filter)", True, f"Found {len(memberships)} memberships with test consultant")
                    return True
                else:
                    self.log_result("Get Memberships (Consultant Filter)", False, f"Failed to get memberships by consultant: {response.status_code}")
                    return False
            
            return True
                
        except Exception as e:
            self.log_result("Get Complimentary Memberships", False, f"Error testing get memberships: {str(e)}")
            return False
    
    def test_complimentary_dashboard(self):
        """Test GET /api/complimentary-dashboard"""
        print("\n=== Testing GET /api/complimentary-dashboard ===")
        
        try:
            response = requests.get(f"{API_BASE}/complimentary-dashboard", headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required fields
                required_fields = ["period_days", "total_issued", "active_memberships", "accessing_count", "not_accessing_count", "utilization_rate", "conversion_rate", "utilization_by_type"]
                for field in required_fields:
                    if field not in data:
                        self.log_result("Dashboard Fields", False, f"Missing field: {field}")
                        return False
                
                # Verify metrics make sense
                total_issued = data["total_issued"]
                active_memberships = data["active_memberships"]
                accessing_count = data["accessing_count"]
                not_accessing_count = data["not_accessing_count"]
                utilization_rate = data["utilization_rate"]
                conversion_rate = data["conversion_rate"]
                
                # Should have at least 1 issued (our test membership)
                if total_issued < 1:
                    self.log_result("Dashboard Total Issued", False, f"Expected at least 1, got {total_issued}")
                    return False
                
                # Should have 1 active membership (our test membership)
                if active_memberships < 1:
                    self.log_result("Dashboard Active Memberships", False, f"Expected at least 1, got {active_memberships}")
                    return False
                
                # Should have 0 accessing (no visits yet)
                if accessing_count != 0:
                    self.log_result("Dashboard Accessing Count", False, f"Expected 0, got {accessing_count}")
                    return False
                
                # Should have 1 not accessing (our test membership)
                if not_accessing_count < 1:
                    self.log_result("Dashboard Not Accessing Count", False, f"Expected at least 1, got {not_accessing_count}")
                    return False
                
                # Utilization rate should be 0% (no visits yet)
                if utilization_rate != 0:
                    self.log_result("Dashboard Utilization Rate", False, f"Expected 0%, got {utilization_rate}%")
                    return False
                
                # Conversion rate should be 0% (no conversions yet)
                if conversion_rate != 0:
                    self.log_result("Dashboard Conversion Rate", False, f"Expected 0%, got {conversion_rate}%")
                    return False
                
                # Verify utilization_by_type structure
                utilization_by_type = data["utilization_by_type"]
                if not isinstance(utilization_by_type, list):
                    self.log_result("Dashboard Utilization By Type", False, "utilization_by_type should be a list")
                    return False
                
                if len(utilization_by_type) > 0:
                    type_data = utilization_by_type[0]
                    required_type_fields = ["_id", "type_name", "total_issued", "total_visits", "members_accessed", "members_converted", "utilization_percentage", "conversion_rate"]
                    for field in required_type_fields:
                        if field not in type_data:
                            self.log_result("Dashboard Type Data Fields", False, f"Missing field in type data: {field}")
                            return False
                
                self.log_result("Get Complimentary Dashboard", True, f"Dashboard metrics: {total_issued} issued, {active_memberships} active, {utilization_rate}% utilization")
                return True
                
            else:
                self.log_result("Get Complimentary Dashboard", False, f"Failed to get dashboard: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Get Complimentary Dashboard", False, f"Error testing dashboard: {str(e)}")
            return False
    
    def test_record_visit(self):
        """Test POST /api/complimentary-memberships/{membership_id}/record-visit"""
        print("\n=== Testing POST /api/complimentary-memberships/{membership_id}/record-visit ===")
        
        try:
            if not self.test_membership_id:
                self.log_result("Record Visit Setup", False, "No test membership ID available")
                return False
            
            # Record first visit
            response = requests.post(f"{API_BASE}/complimentary-memberships/{self.test_membership_id}/record-visit", headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    visits_used = data.get("visits_used")
                    visits_remaining = data.get("visits_remaining")
                    notification_sent = data.get("notification_sent")
                    
                    # Verify first visit
                    if visits_used != 1:
                        self.log_result("Record First Visit - Visits Used", False, f"Expected 1, got {visits_used}")
                        return False
                    
                    if visits_remaining != 4:  # 5 - 1 = 4
                        self.log_result("Record First Visit - Visits Remaining", False, f"Expected 4, got {visits_remaining}")
                        return False
                    
                    self.log_result("Record First Visit", True, f"Visit recorded: {visits_used} used, {visits_remaining} remaining")
                    
                    # Record second visit
                    response2 = requests.post(f"{API_BASE}/complimentary-memberships/{self.test_membership_id}/record-visit", headers=self.admin_headers)
                    
                    if response2.status_code == 200:
                        data2 = response2.json()
                        
                        if data2.get("success"):
                            visits_used_2 = data2.get("visits_used")
                            visits_remaining_2 = data2.get("visits_remaining")
                            
                            # Verify second visit
                            if visits_used_2 != 2:
                                self.log_result("Record Second Visit - Visits Used", False, f"Expected 2, got {visits_used_2}")
                                return False
                            
                            if visits_remaining_2 != 3:  # 5 - 2 = 3
                                self.log_result("Record Second Visit - Visits Remaining", False, f"Expected 3, got {visits_remaining_2}")
                                return False
                            
                            self.log_result("Record Second Visit", True, f"Second visit recorded: {visits_used_2} used, {visits_remaining_2} remaining")
                            return True
                        else:
                            self.log_result("Record Second Visit", False, "Second visit not successful")
                            return False
                    else:
                        self.log_result("Record Second Visit", False, f"Failed to record second visit: {response2.status_code}")
                        return False
                else:
                    self.log_result("Record First Visit", False, "First visit not successful")
                    return False
            else:
                self.log_result("Record First Visit", False, f"Failed to record first visit: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Record Visit", False, f"Error testing record visit: {str(e)}")
            return False
    
    def test_dashboard_after_visits(self):
        """Test GET /api/complimentary-dashboard after recording visits"""
        print("\n=== Testing GET /api/complimentary-dashboard (after visits) ===")
        
        try:
            response = requests.get(f"{API_BASE}/complimentary-dashboard", headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                accessing_count = data.get("accessing_count", 0)
                utilization_rate = data.get("utilization_rate", 0)
                utilization_by_type = data.get("utilization_by_type", [])
                
                # Should now have 1 accessing member (our test membership with visits)
                if accessing_count < 1:
                    self.log_result("Dashboard Accessing After Visits", False, f"Expected at least 1, got {accessing_count}")
                    return False
                
                # Utilization rate should be > 0% now
                if utilization_rate <= 0:
                    self.log_result("Dashboard Utilization After Visits", False, f"Expected > 0%, got {utilization_rate}%")
                    return False
                
                # Verify utilization_by_type shows visits_used
                if len(utilization_by_type) > 0:
                    type_data = utilization_by_type[0]
                    total_visits = type_data.get("total_visits", 0)
                    
                    if total_visits < 2:  # Should have at least 2 visits from our tests
                        self.log_result("Dashboard Type Visits", False, f"Expected at least 2 visits, got {total_visits}")
                        return False
                
                self.log_result("Dashboard After Visits", True, f"Updated metrics: {accessing_count} accessing, {utilization_rate}% utilization")
                return True
                
            else:
                self.log_result("Dashboard After Visits", False, f"Failed to get dashboard: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Dashboard After Visits", False, f"Error testing dashboard after visits: {str(e)}")
            return False
    
    def test_delete_complimentary_type_with_active_memberships(self):
        """Test DELETE /api/complimentary-types/{type_id} with active memberships (should fail)"""
        print("\n=== Testing DELETE /api/complimentary-types/{type_id} (with active memberships) ===")
        
        try:
            if not self.test_type_id:
                self.log_result("Delete Type Setup", False, "No test type ID available")
                return False
            
            # Try to delete the type that has active memberships (should fail)
            response = requests.delete(f"{API_BASE}/complimentary-types/{self.test_type_id}", headers=self.admin_headers)
            
            if response.status_code == 400:
                data = response.json()
                detail = data.get("detail", "")
                
                if "active memberships" in detail.lower():
                    self.log_result("Delete Type With Active Memberships", True, "Correctly prevented deletion due to active memberships")
                    return True
                else:
                    self.log_result("Delete Type With Active Memberships", False, f"Wrong error message: {detail}")
                    return False
            else:
                self.log_result("Delete Type With Active Memberships", False, f"Expected 400, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Delete Type With Active Memberships", False, f"Error testing delete type: {str(e)}")
            return False
    
    def test_delete_complimentary_type_without_memberships(self):
        """Test DELETE /api/complimentary-types/{type_id} without active memberships (should succeed)"""
        print("\n=== Testing DELETE /api/complimentary-types/{type_id} (without memberships) ===")
        
        try:
            # Find the second type we created (should have no memberships)
            if len(self.created_types) < 2:
                self.log_result("Delete Type Setup", False, "Need second type for deletion test")
                return False
            
            second_type_id = self.created_types[1]  # The "Week Pass" type
            
            # Try to delete the type without memberships (should succeed)
            response = requests.delete(f"{API_BASE}/complimentary-types/{second_type_id}", headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    self.log_result("Delete Type Without Memberships", True, "Successfully deleted type without active memberships")
                    
                    # Remove from our tracking list
                    self.created_types.remove(second_type_id)
                    return True
                else:
                    self.log_result("Delete Type Without Memberships", False, "Delete not successful")
                    return False
            else:
                self.log_result("Delete Type Without Memberships", False, f"Failed to delete type: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Delete Type Without Memberships", False, f"Error testing delete type: {str(e)}")
            return False
    
    def test_edge_cases(self):
        """Test edge cases and error conditions"""
        print("\n=== Testing Edge Cases ===")
        
        try:
            # Test invalid type_id for issuing membership
            invalid_membership_data = {
                "first_name": "Invalid",
                "last_name": "Test",
                "email": "invalid@test.com",
                "phone": "+27123456789",
                "complimentary_type_id": "invalid-type-id",
                "assigned_consultant_id": self.test_consultant_id,
                "auto_create_lead": False
            }
            
            response = requests.post(f"{API_BASE}/complimentary-memberships", json=invalid_membership_data, headers=self.admin_headers)
            
            if response.status_code == 404:
                self.log_result("Invalid Type ID", True, "Correctly returns 404 for invalid type ID")
            else:
                self.log_result("Invalid Type ID", False, f"Expected 404, got {response.status_code}")
                return False
            
            # Test recording visit on non-existent membership
            response = requests.post(f"{API_BASE}/complimentary-memberships/invalid-membership-id/record-visit", headers=self.admin_headers)
            
            if response.status_code == 404:
                self.log_result("Invalid Membership ID", True, "Correctly returns 404 for invalid membership ID")
            else:
                self.log_result("Invalid Membership ID", False, f"Expected 404, got {response.status_code}")
                return False
            
            return True
                
        except Exception as e:
            self.log_result("Edge Cases", False, f"Error testing edge cases: {str(e)}")
            return False
    
    def cleanup(self):
        """Clean up created test data"""
        print("\n=== Cleaning Up Test Data ===")
        
        # Note: In a real scenario, you might want to clean up created data
        # For this test, we'll leave the data as it demonstrates the system working
        
        self.log_result("Cleanup", True, f"Left {len(self.created_types)} types and {len(self.created_memberships)} memberships for inspection")
    
    def run_all_tests(self):
        """Run all complimentary membership tests in order"""
        print("🏋️ Starting Complimentary Membership Tracking System Backend Tests")
        print("=" * 80)
        
        # Authentication
        if not self.authenticate():
            return False
        
        # Test sequence as specified in the requirements
        tests = [
            self.test_get_complimentary_types,
            self.test_create_complimentary_type,
            self.test_get_complimentary_types_after_create,
            self.test_update_complimentary_type,
            self.test_get_sales_consultants,
            self.test_issue_complimentary_membership,
            self.test_get_complimentary_memberships,
            self.test_complimentary_dashboard,
            self.test_record_visit,
            self.test_dashboard_after_visits,
            self.test_delete_complimentary_type_with_active_memberships,
            self.test_delete_complimentary_type_without_memberships,
            self.test_edge_cases
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
                print(f"❌ EXCEPTION in {test.__name__}: {str(e)}")
                failed += 1
        
        # Cleanup
        self.cleanup()
        
        # Summary
        print("\n" + "=" * 80)
        print("🏁 TEST SUMMARY")
        print("=" * 80)
        print(f"✅ PASSED: {passed}")
        print(f"❌ FAILED: {failed}")
        print(f"📊 TOTAL:  {passed + failed}")
        
        if failed == 0:
            print("\n🎉 ALL TESTS PASSED! Complimentary Membership Tracking System is working correctly.")
        else:
            print(f"\n⚠️  {failed} tests failed. Please review the failures above.")
        
        return failed == 0

def main():
    """Main function to run the tests"""
    runner = ComplimentaryMembershipTestRunner()
    success = runner.run_all_tests()
    
    if success:
        print("\n✅ Backend testing completed successfully!")
        exit(0)
    else:
        print("\n❌ Backend testing completed with failures!")
        exit(1)

if __name__ == "__main__":
    main()