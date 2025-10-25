#!/usr/bin/env python3
"""
Backend Test Suite - Configurable Lead Source/Status/Loss Reason System
Focus on Configuration APIs, Enhanced Lead Management, Referral Rewards, Member Search, and Comprehensive Dashboard Analytics
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

class ConfigurableLeadSystemTestRunner:
    def __init__(self):
        self.token = None
        self.headers = {}
        self.test_results = []
        self.created_leads = []  # Track created leads for cleanup
        self.created_sources = []  # Track created lead sources for cleanup
        self.created_statuses = []  # Track created lead statuses for cleanup
        self.created_loss_reasons = []  # Track created loss reasons for cleanup
        self.created_referral_rewards = []  # Track created referral rewards for cleanup
        self.test_lead_id = None
        self.test_user_id = None
        self.test_member_id = None
        self.seeded_source_ids = {}  # Map of seeded source names to IDs
        self.seeded_status_ids = {}  # Map of seeded status names to IDs
        self.seeded_loss_reason_ids = {}  # Map of seeded loss reason names to IDs
        
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
        """Setup test data and get seeded configuration IDs"""
        try:
            # Get current user info
            response = requests.get(f"{API_BASE}/auth/me", headers=self.headers)
            if response.status_code == 200:
                user_data = response.json()
                self.test_user_id = user_data["id"]
                self.log_result("Get Current User", True, f"Current user: {user_data['email']}")
            else:
                self.log_result("Get Current User", False, f"Failed to get current user: {response.status_code}")
                return False
            
            # Get an active member for referral testing
            response = requests.get(f"{API_BASE}/members", headers=self.headers)
            if response.status_code == 200:
                members_data = response.json()
                if "members" in members_data and members_data["members"]:
                    # Find an active member
                    for member in members_data["members"]:
                        if member.get("membership_status") == "active":
                            self.test_member_id = member["id"]
                            self.log_result("Get Test Member", True, f"Found active member: {member['first_name']} {member['last_name']}")
                            break
                    
                    if not self.test_member_id:
                        self.log_result("Get Test Member", False, "No active members found for referral testing")
                        return False
                else:
                    self.log_result("Get Test Member", False, "No members found")
                    return False
            else:
                self.log_result("Get Test Member", False, f"Failed to get members: {response.status_code}")
                return False
            
            # Get seeded lead sources
            response = requests.get(f"{API_BASE}/sales/config/lead-sources", headers=self.headers)
            if response.status_code == 200:
                sources_data = response.json()
                if "sources" in sources_data:
                    for source in sources_data["sources"]:
                        self.seeded_source_ids[source["name"]] = source["id"]
                    self.log_result("Get Seeded Sources", True, f"Found {len(self.seeded_source_ids)} seeded sources")
                else:
                    self.log_result("Get Seeded Sources", False, "No sources in response")
                    return False
            else:
                self.log_result("Get Seeded Sources", False, f"Failed to get sources: {response.status_code}")
                return False
            
            # Get seeded lead statuses
            response = requests.get(f"{API_BASE}/sales/config/lead-statuses", headers=self.headers)
            if response.status_code == 200:
                statuses_data = response.json()
                if "statuses" in statuses_data:
                    for status in statuses_data["statuses"]:
                        self.seeded_status_ids[status["name"]] = status["id"]
                    self.log_result("Get Seeded Statuses", True, f"Found {len(self.seeded_status_ids)} seeded statuses")
                else:
                    self.log_result("Get Seeded Statuses", False, "No statuses in response")
                    return False
            else:
                self.log_result("Get Seeded Statuses", False, f"Failed to get statuses: {response.status_code}")
                return False
            
            # Get seeded loss reasons
            response = requests.get(f"{API_BASE}/sales/config/loss-reasons", headers=self.headers)
            if response.status_code == 200:
                reasons_data = response.json()
                if "reasons" in reasons_data:
                    for reason in reasons_data["reasons"]:
                        self.seeded_loss_reason_ids[reason["name"]] = reason["id"]
                    self.log_result("Get Seeded Loss Reasons", True, f"Found {len(self.seeded_loss_reason_ids)} seeded loss reasons")
                else:
                    self.log_result("Get Seeded Loss Reasons", False, "No loss reasons in response")
                    return False
            else:
                self.log_result("Get Seeded Loss Reasons", False, f"Failed to get loss reasons: {response.status_code}")
                return False
            
            return True
                
        except Exception as e:
            self.log_result("Setup Test Data", False, f"Error setting up test data: {str(e)}")
            return False
    
    # ===================== STARTUP SEEDING VERIFICATION TESTS =====================
    
    def test_startup_seeding_verification(self):
        """Test Lead Scoring API - POST /api/sales/automation/score-lead/{lead_id}"""
        print("\n=== Testing Lead Scoring API ===")
        
        try:
            # Test with existing lead
            response = requests.post(f"{API_BASE}/sales/automation/score-lead/{self.test_lead_id}", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required structure
                required_fields = ["success", "lead_id", "new_score", "scoring_factors"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Lead Scoring Structure", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify success
                if not data["success"]:
                    self.log_result("Lead Scoring Success", False, 
                                  "Lead scoring was not successful")
                    return False
                
                # Verify score is between 0-100
                score = data["new_score"]
                if not (0 <= score <= 100):
                    self.log_result("Lead Scoring Range", False, 
                                  f"Score {score} not in range 0-100")
                    return False
                
                # Verify scoring factors structure (it's a list of strings, not a dict)
                factors = data["scoring_factors"]
                if not isinstance(factors, list):
                    self.log_result("Lead Scoring Factors Type", False, 
                                  "scoring_factors should be a list")
                    return False
                
                # Verify factors contain expected scoring elements
                factors_text = " ".join(factors)
                expected_elements = ["email", "phone", "company", "Source"]
                for element in expected_elements:
                    if element not in factors_text:
                        self.log_result("Lead Scoring Factors Content", False, 
                                      f"Missing scoring element: {element}")
                        return False
                
                # Verify lead ID matches
                if data["lead_id"] != self.test_lead_id:
                    self.log_result("Lead Scoring Lead ID", False, 
                                  "Lead ID mismatch")
                    return False
                
                # Verify scoring calculation logic by checking individual factor scores
                has_email = any("email" in factor and "+10" in factor for factor in factors)
                has_phone = any("phone" in factor and "+10" in factor for factor in factors)
                has_company = any("company" in factor and "+15" in factor for factor in factors)
                has_source = any("Source:" in factor for factor in factors)
                
                if not (has_email and has_phone and has_company and has_source):
                    self.log_result("Lead Scoring Factor Validation", False, 
                                  f"Missing expected scoring factors in: {factors}")
                    return False
                
                self.log_result("Lead Scoring API (Valid Lead)", True, 
                              f"Lead scored: {score}/100 with factors: {factors}")
                
                # Test with non-existent lead (should return 404)
                fake_lead_id = "fake_lead_123"
                response = requests.post(f"{API_BASE}/sales/automation/score-lead/{fake_lead_id}", headers=self.headers)
                if response.status_code == 404:
                    self.log_result("Lead Scoring API (Non-existent Lead)", True, 
                                  "Correctly returns 404 for non-existent lead")
                else:
                    self.log_result("Lead Scoring API (Non-existent Lead)", False, 
                                  f"Expected 404, got {response.status_code}")
                    return False
                
                return True
                
            else:
                self.log_result("Lead Scoring API", False, 
                              f"Failed to score lead: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Lead Scoring API", False, f"Error testing lead scoring API: {str(e)}")
            return False
    
    def test_auto_assign_lead_api(self):
        """Test Auto-Assign Lead API - POST /api/sales/automation/auto-assign-lead/{lead_id}"""
        print("\n=== Testing Auto-Assign Lead API ===")
        
        try:
            # Test round_robin strategy
            response = requests.post(f"{API_BASE}/sales/automation/auto-assign-lead/{self.test_lead_id}?assignment_strategy=round_robin", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required structure
                required_fields = ["success", "lead_id", "assigned_to", "strategy"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Auto-Assign Structure", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify assignment success
                if not data["success"]:
                    self.log_result("Auto-Assign Success", False, 
                                  "Assignment was not successful")
                    return False
                
                # Verify strategy
                if data["strategy"] != "round_robin":
                    self.log_result("Auto-Assign Strategy", False, 
                                  f"Expected 'round_robin', got '{data['strategy']}'")
                    return False
                
                # Verify assigned user is provided
                if not data["assigned_to"]:
                    self.log_result("Auto-Assign User", False, 
                                  "Assigned user is missing")
                    return False
                
                self.log_result("Auto-Assign API (Round Robin)", True, 
                              f"Lead assigned to {data['assigned_to']} using {data['strategy']}")
                
                # Test least_loaded strategy
                response = requests.post(f"{API_BASE}/sales/automation/auto-assign-lead/{self.test_lead_id}?assignment_strategy=least_loaded", headers=self.headers)
                if response.status_code == 200:
                    least_loaded_data = response.json()
                    if least_loaded_data["strategy"] == "least_loaded":
                        self.log_result("Auto-Assign API (Least Loaded)", True, 
                                      f"Lead assigned using least_loaded strategy")
                    else:
                        self.log_result("Auto-Assign API (Least Loaded)", False, 
                                      f"Strategy mismatch: {least_loaded_data['strategy']}")
                        return False
                else:
                    self.log_result("Auto-Assign API (Least Loaded)", False, 
                                  f"Failed with least_loaded strategy: {response.status_code}")
                    return False
                
                # Test with non-existent lead
                fake_lead_id = "fake_lead_123"
                response = requests.post(f"{API_BASE}/sales/automation/auto-assign-lead/{fake_lead_id}?assignment_strategy=round_robin", headers=self.headers)
                if response.status_code == 404:
                    self.log_result("Auto-Assign API (Non-existent Lead)", True, 
                                  "Correctly returns 404 for non-existent lead")
                else:
                    self.log_result("Auto-Assign API (Non-existent Lead)", False, 
                                  f"Expected 404, got {response.status_code}")
                    return False
                
                return True
                
            else:
                self.log_result("Auto-Assign Lead API", False, 
                              f"Failed to auto-assign lead: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Auto-Assign Lead API", False, f"Error testing auto-assign API: {str(e)}")
            return False
    
    def test_create_follow_up_tasks_api(self):
        """Test Create Follow-Up Tasks API - POST /api/sales/automation/create-follow-up-tasks"""
        print("\n=== Testing Create Follow-Up Tasks API ===")
        
        try:
            # Test with 7 days inactive threshold
            response = requests.post(f"{API_BASE}/sales/automation/create-follow-up-tasks?days_inactive=7", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required structure
                required_fields = ["success", "tasks_created", "leads_processed", "days_inactive_threshold"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Follow-Up Tasks Structure", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify success
                if not data["success"]:
                    self.log_result("Follow-Up Tasks Success", False, 
                                  "Task creation was not successful")
                    return False
                
                # Verify counts are non-negative integers
                if not isinstance(data["tasks_created"], int) or data["tasks_created"] < 0:
                    self.log_result("Follow-Up Tasks Count Type", False, 
                                  f"tasks_created should be non-negative integer, got {data['tasks_created']}")
                    return False
                
                if not isinstance(data["leads_processed"], int) or data["leads_processed"] < 0:
                    self.log_result("Follow-Up Leads Count Type", False, 
                                  f"leads_processed should be non-negative integer, got {data['leads_processed']}")
                    return False
                
                self.log_result("Follow-Up Tasks API (7 days)", True, 
                              f"Created {data['tasks_created']} tasks for {data['leads_processed']} leads")
                
                # Test with different thresholds
                for days in [3, 14, 30]:
                    response = requests.post(f"{API_BASE}/sales/automation/create-follow-up-tasks?days_inactive={days}", headers=self.headers)
                    if response.status_code == 200:
                        threshold_data = response.json()
                        self.log_result(f"Follow-Up Tasks API ({days} days)", True, 
                                      f"Created {threshold_data['tasks_created']} tasks for {threshold_data['leads_processed']} leads")
                    else:
                        self.log_result(f"Follow-Up Tasks API ({days} days)", False, 
                                      f"Failed with {days} days threshold: {response.status_code}")
                        return False
                
                # Test with invalid threshold (negative)
                response = requests.post(f"{API_BASE}/sales/automation/create-follow-up-tasks?days_inactive=-1", headers=self.headers)
                if response.status_code in [400, 422]:
                    self.log_result("Follow-Up Tasks API (Invalid Threshold)", True, 
                                  "Correctly rejects negative days_inactive")
                else:
                    self.log_result("Follow-Up Tasks API (Invalid Threshold)", False, 
                                  f"Should reject negative threshold, got {response.status_code}")
                    return False
                
                return True
                
            else:
                self.log_result("Create Follow-Up Tasks API", False, 
                              f"Failed to create follow-up tasks: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Create Follow-Up Tasks API", False, f"Error testing follow-up tasks API: {str(e)}")
            return False
    
    # ===================== WORKFLOW AUTOMATION TESTS =====================
    
    def test_list_workflows_api(self):
        """Test List Workflows API - GET /api/sales/workflows"""
        print("\n=== Testing List Workflows API ===")
        
        try:
            response = requests.get(f"{API_BASE}/sales/workflows", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required structure
                required_fields = ["workflows", "total"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("List Workflows Structure", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify workflows is a list
                if not isinstance(data["workflows"], list):
                    self.log_result("List Workflows Type", False, 
                                  "workflows should be a list")
                    return False
                
                # Verify total count
                if not isinstance(data["total"], int) or data["total"] < 0:
                    self.log_result("List Workflows Total Type", False, 
                                  "total should be non-negative integer")
                    return False
                
                # If workflows exist, verify structure
                if data["workflows"]:
                    workflow = data["workflows"][0]
                    workflow_fields = ["id", "name", "trigger_object", "trigger_event", "conditions", "actions", "is_active", "created_at"]
                    missing_workflow_fields = [field for field in workflow_fields if field not in workflow]
                    
                    if missing_workflow_fields:
                        self.log_result("List Workflows Item Structure", False, 
                                      f"Missing workflow fields: {missing_workflow_fields}")
                        return False
                
                self.log_result("List Workflows API", True, 
                              f"Retrieved {len(data['workflows'])} workflows, total: {data['total']}")
                return True
                
            else:
                self.log_result("List Workflows API", False, 
                              f"Failed to list workflows: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("List Workflows API", False, f"Error testing list workflows API: {str(e)}")
            return False
    
    def test_create_workflow_api(self):
        """Test Create Workflow API - POST /api/sales/workflows"""
        print("\n=== Testing Create Workflow API ===")
        
        try:
            # Create test workflow
            workflow_data = {
                "name": "Auto Task on Qualified Lead",
                "trigger_object": "lead",
                "trigger_event": "status_changed",
                "conditions": {"status": "qualified"},
                "actions": [
                    {
                        "type": "create_task",
                        "params": {
                            "title": "Follow up with qualified lead",
                            "description": "This lead is qualified, schedule a call",
                            "task_type": "follow_up",
                            "priority": "high"
                        }
                    }
                ]
            }
            
            response = requests.post(f"{API_BASE}/sales/workflows", json=workflow_data, headers=self.headers)
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Verify response structure
                if "success" not in response_data or "workflow" not in response_data:
                    self.log_result("Create Workflow Response Structure", False, 
                                  f"Missing success or workflow in response: {response_data}")
                    return False
                
                if not response_data["success"]:
                    self.log_result("Create Workflow Success", False, 
                                  "Workflow creation was not successful")
                    return False
                
                data = response_data["workflow"]
                
                # Verify required structure
                required_fields = ["id", "name", "trigger_object", "trigger_event", "conditions", "actions", "is_active", "created_at"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Create Workflow Structure", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify workflow has UUID
                if not data["id"] or len(data["id"]) < 32:
                    self.log_result("Create Workflow ID", False, 
                                  "Workflow ID should be a valid UUID")
                    return False
                
                # Verify is_active defaults to true
                if not data["is_active"]:
                    self.log_result("Create Workflow Default Active", False, 
                                  "is_active should default to true")
                    return False
                
                # Verify created_at timestamp
                if not data["created_at"]:
                    self.log_result("Create Workflow Timestamp", False, 
                                  "created_at timestamp is missing")
                    return False
                
                # Store for cleanup
                self.test_workflow_id = data["id"]
                self.created_workflows.append(data["id"])
                
                self.log_result("Create Workflow API", True, 
                              f"Created workflow: {data['name']} with ID: {data['id']}")
                
                # Test with invalid data (missing required fields)
                invalid_workflow = {
                    "name": "Invalid Workflow"
                    # Missing required fields
                }
                
                response = requests.post(f"{API_BASE}/sales/workflows", json=invalid_workflow, headers=self.headers)
                if response.status_code in [400, 422]:
                    self.log_result("Create Workflow Validation", True, 
                                  "Correctly validates required fields")
                else:
                    self.log_result("Create Workflow Validation", False, 
                                  f"Should validate required fields, got {response.status_code}")
                    return False
                
                return True
                
            else:
                self.log_result("Create Workflow API", False, 
                              f"Failed to create workflow: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Create Workflow API", False, f"Error testing create workflow API: {str(e)}")
            return False
    
    def test_update_workflow_api(self):
        """Test Update Workflow API - PUT /api/sales/workflows/{workflow_id}"""
        print("\n=== Testing Update Workflow API ===")
        
        try:
            # Create a new workflow specifically for update testing
            update_workflow_data = {
                "name": "Update Test Workflow",
                "trigger_object": "lead",
                "trigger_event": "created",
                "conditions": {"status": "new"},
                "actions": [{"type": "create_task", "params": {"title": "Test task"}}]
            }
            
            response = requests.post(f"{API_BASE}/sales/workflows", json=update_workflow_data, headers=self.headers)
            if response.status_code != 200:
                self.log_result("Update Workflow API", False, "Failed to create workflow for update test")
                return False
            
            update_workflow = response.json()["workflow"]
            update_workflow_id = update_workflow["id"]
            self.created_workflows.append(update_workflow_id)
            
            # Test toggling is_active
            update_data = {
                "is_active": False
            }
            
            response = requests.put(f"{API_BASE}/sales/workflows/{update_workflow_id}", json=update_data, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify update was applied
                if data["is_active"] != False:
                    self.log_result("Update Workflow Active Status", False, 
                                  f"Expected is_active=False, got {data['is_active']}")
                    return False
                
                self.log_result("Update Workflow API (Deactivate)", True, 
                              "Successfully deactivated workflow")
                
                # Toggle back to active
                update_data = {"is_active": True}
                response = requests.put(f"{API_BASE}/sales/workflows/{update_workflow_id}", json=update_data, headers=self.headers)
                
                if response.status_code == 200:
                    reactivated_data = response.json()
                    if reactivated_data["is_active"] == True:
                        self.log_result("Update Workflow API (Reactivate)", True, 
                                      "Successfully reactivated workflow")
                    else:
                        self.log_result("Update Workflow API (Reactivate)", False, 
                                      f"Expected is_active=True, got {reactivated_data['is_active']}")
                        return False
                else:
                    self.log_result("Update Workflow API (Reactivate)", False, 
                                  f"Failed to reactivate: {response.status_code}")
                    return False
                
                # Test with non-existent workflow
                fake_workflow_id = "fake_workflow_123"
                response = requests.put(f"{API_BASE}/sales/workflows/{fake_workflow_id}", json=update_data, headers=self.headers)
                if response.status_code == 404:
                    self.log_result("Update Workflow API (Non-existent)", True, 
                                  "Correctly returns 404 for non-existent workflow")
                else:
                    self.log_result("Update Workflow API (Non-existent)", False, 
                                  f"Expected 404, got {response.status_code}")
                    return False
                
                return True
                
            else:
                self.log_result("Update Workflow API", False, 
                              f"Failed to update workflow: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Update Workflow API", False, f"Error testing update workflow API: {str(e)}")
            return False
    
    def test_delete_workflow_api(self):
        """Test Delete Workflow API - DELETE /api/sales/workflows/{workflow_id}"""
        print("\n=== Testing Delete Workflow API ===")
        
        try:
            if not self.test_workflow_id:
                self.log_result("Delete Workflow API", False, "No test workflow available")
                return False
            
            # Test successful deletion
            response = requests.delete(f"{API_BASE}/sales/workflows/{self.test_workflow_id}", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify success message
                if not data.get("success"):
                    self.log_result("Delete Workflow Success", False, 
                                  "Delete response should indicate success")
                    return False
                
                self.log_result("Delete Workflow API (Valid ID)", True, 
                              "Successfully deleted workflow")
                
                # Verify workflow is actually deleted (should return 404)
                response = requests.get(f"{API_BASE}/sales/workflows/{self.test_workflow_id}", headers=self.headers)
                if response.status_code == 404:
                    self.log_result("Delete Workflow Verification", True, 
                                  "Workflow properly removed from database")
                else:
                    self.log_result("Delete Workflow Verification", False, 
                                  f"Workflow still exists after deletion: {response.status_code}")
                    return False
                
                # Remove from cleanup list since it's deleted
                if self.test_workflow_id in self.created_workflows:
                    self.created_workflows.remove(self.test_workflow_id)
                
                # Test with non-existent workflow
                fake_workflow_id = "fake_workflow_123"
                response = requests.delete(f"{API_BASE}/sales/workflows/{fake_workflow_id}", headers=self.headers)
                if response.status_code == 404:
                    self.log_result("Delete Workflow API (Non-existent)", True, 
                                  "Correctly returns 404 for non-existent workflow")
                else:
                    self.log_result("Delete Workflow API (Non-existent)", False, 
                                  f"Expected 404, got {response.status_code}")
                    return False
                
                return True
                
            else:
                self.log_result("Delete Workflow API", False, 
                              f"Failed to delete workflow: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Delete Workflow API", False, f"Error testing delete workflow API: {str(e)}")
            return False
    
    def test_execute_workflow_api(self):
        """Test Execute Workflow API - POST /api/sales/workflows/execute"""
        print("\n=== Testing Execute Workflow API ===")
        
        try:
            # First create a test workflow for execution
            workflow_data = {
                "name": "Test Execution Workflow",
                "trigger_object": "lead",
                "trigger_event": "status_changed",
                "conditions": {"status": "qualified"},
                "actions": [
                    {
                        "type": "create_task",
                        "params": {
                            "title": "Follow up with qualified lead",
                            "description": "This lead is qualified, schedule a call",
                            "task_type": "follow_up",
                            "priority": "high"
                        }
                    }
                ]
            }
            
            response = requests.post(f"{API_BASE}/sales/workflows", json=workflow_data, headers=self.headers)
            if response.status_code != 200:
                self.log_result("Execute Workflow Setup", False, "Failed to create test workflow")
                return False
            
            execution_response = response.json()
            if "workflow" not in execution_response:
                self.log_result("Execute Workflow Setup", False, f"Unexpected response structure: {execution_response}")
                return False
            
            execution_workflow = execution_response["workflow"]
            execution_workflow_id = execution_workflow["id"]
            self.created_workflows.append(execution_workflow_id)
            
            # Test workflow execution with matching conditions
            import json
            execution_params = {
                "trigger_object": "lead",
                "trigger_event": "status_changed",
                "object_id": self.test_lead_id,
                "object_data": json.dumps({
                    "status": "qualified",
                    "assigned_to": self.test_user_id
                })
            }
            
            response = requests.post(f"{API_BASE}/sales/workflows/execute", params=execution_params, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required structure
                required_fields = ["success", "workflows_executed", "executed_actions", "message"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Execute Workflow Structure", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify execution success
                if not data["success"]:
                    self.log_result("Execute Workflow Success", False, 
                                  "Workflow execution was not successful")
                    return False
                
                # Verify workflows were executed
                if data["workflows_executed"] < 1:
                    self.log_result("Execute Workflow Count", False, 
                                  f"Expected at least 1 workflow executed, got {data['workflows_executed']}")
                    return False
                
                # Verify executed actions structure
                if not isinstance(data["executed_actions"], list):
                    self.log_result("Execute Workflow Actions Type", False, 
                                  "executed_actions should be a list")
                    return False
                
                self.log_result("Execute Workflow API (Matching Conditions)", True, 
                              f"Executed {data['workflows_executed']} workflows with {len(data['executed_actions'])} actions")
                
                # Test with non-matching conditions
                non_matching_params = {
                    "trigger_object": "lead",
                    "trigger_event": "status_changed",
                    "object_id": self.test_lead_id,
                    "object_data": json.dumps({
                        "status": "new",  # Different status, won't match
                        "assigned_to": self.test_user_id
                    })
                }
                
                response = requests.post(f"{API_BASE}/sales/workflows/execute", params=non_matching_params, headers=self.headers)
                if response.status_code == 200:
                    non_matching_result = response.json()
                    if non_matching_result["workflows_executed"] == 0:
                        self.log_result("Execute Workflow API (Non-matching Conditions)", True, 
                                      "Correctly skips workflows with non-matching conditions")
                    else:
                        self.log_result("Execute Workflow API (Non-matching Conditions)", False, 
                                      f"Should not execute workflows with non-matching conditions")
                        return False
                else:
                    self.log_result("Execute Workflow API (Non-matching Conditions)", False, 
                                  f"Failed with non-matching conditions: {response.status_code}")
                    return False
                
                return True
                
            else:
                self.log_result("Execute Workflow API", False, 
                              f"Failed to execute workflow: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Execute Workflow API", False, f"Error testing execute workflow API: {str(e)}")
            return False
    
    # ===================== ADVANCED ANALYTICS TESTS =====================
    
    def test_sales_forecasting_api(self):
        """Test Sales Forecasting API - GET /api/sales/analytics/forecasting"""
        print("\n=== Testing Sales Forecasting API ===")
        
        try:
            # Test with default period (3 months)
            response = requests.get(f"{API_BASE}/sales/analytics/forecasting", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required structure
                required_fields = ["total_forecast", "by_stage", "historical_revenue", "confidence_level", "forecast_period_months"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Sales Forecasting Structure", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify total_forecast is a number
                if not isinstance(data["total_forecast"], (int, float)):
                    self.log_result("Sales Forecasting Total Type", False, 
                                  "total_forecast should be a number")
                    return False
                
                # Verify by_stage structure
                by_stage = data["by_stage"]
                if not isinstance(by_stage, dict):
                    self.log_result("Sales Forecasting By Stage Type", False, 
                                  "by_stage should be a dictionary")
                    return False
                
                # Verify stage breakdown includes all stages
                expected_stages = ["new_lead", "contacted", "qualified", "proposal", "negotiation"]
                for stage in expected_stages:
                    if stage not in by_stage:
                        self.log_result("Sales Forecasting Stage Coverage", False, 
                                      f"Missing stage: {stage}")
                        return False
                    
                    stage_data = by_stage[stage]
                    stage_fields = ["count", "total_value", "weighted_value", "avg_probability"]
                    missing_stage_fields = [field for field in stage_fields if field not in stage_data]
                    
                    if missing_stage_fields:
                        self.log_result("Sales Forecasting Stage Structure", False, 
                                      f"Missing stage fields for {stage}: {missing_stage_fields}")
                        return False
                
                # Verify confidence level is a valid string
                confidence = data["confidence_level"]
                valid_confidence_levels = ["low", "medium", "high"]
                if confidence not in valid_confidence_levels:
                    self.log_result("Sales Forecasting Confidence Level", False, 
                                  f"Confidence level '{confidence}' not in {valid_confidence_levels}")
                    return False
                
                self.log_result("Sales Forecasting API (Default Period)", True, 
                              f"Forecast: ${data['total_forecast']:.2f}, Confidence: {confidence}%")
                
                # Test with different period_months
                for period in [1, 6, 12]:
                    response = requests.get(f"{API_BASE}/sales/analytics/forecasting?period_months={period}", headers=self.headers)
                    if response.status_code == 200:
                        period_data = response.json()
                        if period_data["forecast_period_months"] == period:
                            self.log_result(f"Sales Forecasting API ({period} months)", True, 
                                          f"Forecast for {period} months: ${period_data['total_forecast']:.2f}")
                        else:
                            self.log_result(f"Sales Forecasting API ({period} months)", False, 
                                          f"Period mismatch: expected {period}, got {period_data['forecast_period_months']}")
                            return False
                    else:
                        self.log_result(f"Sales Forecasting API ({period} months)", False, 
                                      f"Failed with {period} months: {response.status_code}")
                        return False
                
                return True
                
            else:
                self.log_result("Sales Forecasting API", False, 
                              f"Failed to get sales forecast: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Sales Forecasting API", False, f"Error testing sales forecasting API: {str(e)}")
            return False
    
    def test_team_performance_api(self):
        """Test Team Performance API - GET /api/sales/analytics/team-performance"""
        print("\n=== Testing Team Performance API ===")
        
        try:
            response = requests.get(f"{API_BASE}/sales/analytics/team-performance", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required structure
                required_fields = ["team_metrics", "total_team_members"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Team Performance Structure", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify team_metrics is a list
                if not isinstance(data["team_metrics"], list):
                    self.log_result("Team Performance Members Type", False, 
                                  "team_metrics should be a list")
                    return False
                
                # Verify total_team_members count
                if not isinstance(data["total_team_members"], int) or data["total_team_members"] < 0:
                    self.log_result("Team Performance Total Type", False, 
                                  "total_team_members should be non-negative integer")
                    return False
                
                # If team members exist, verify structure
                if data["team_metrics"]:
                    member = data["team_metrics"][0]
                    member_fields = ["user_id", "user_name", "leads", "opportunities", "tasks"]
                    missing_member_fields = [field for field in member_fields if field not in member]
                    
                    if missing_member_fields:
                        self.log_result("Team Performance Member Structure", False, 
                                      f"Missing member fields: {missing_member_fields}")
                        return False
                    
                    # Verify leads structure
                    leads = member["leads"]
                    leads_fields = ["total", "qualified", "converted", "conversion_rate"]
                    missing_leads_fields = [field for field in leads_fields if field not in leads]
                    
                    if missing_leads_fields:
                        self.log_result("Team Performance Leads Structure", False, 
                                      f"Missing leads fields: {missing_leads_fields}")
                        return False
                    
                    # Verify opportunities structure
                    opportunities = member["opportunities"]
                    opp_fields = ["total", "won", "total_value", "win_rate"]
                    missing_opp_fields = [field for field in opp_fields if field not in opportunities]
                    
                    if missing_opp_fields:
                        self.log_result("Team Performance Opportunities Structure", False, 
                                      f"Missing opportunities fields: {missing_opp_fields}")
                        return False
                    
                    # Verify tasks structure
                    tasks = member["tasks"]
                    tasks_fields = ["total", "completed", "completion_rate"]
                    missing_tasks_fields = [field for field in tasks_fields if field not in tasks]
                    
                    if missing_tasks_fields:
                        self.log_result("Team Performance Tasks Structure", False, 
                                      f"Missing tasks fields: {missing_tasks_fields}")
                        return False
                    
                    # Verify rate calculations are percentages (0-100)
                    rates = [leads["conversion_rate"], opportunities["win_rate"], tasks["completion_rate"]]
                    for rate in rates:
                        if not (0 <= rate <= 100):
                            self.log_result("Team Performance Rate Range", False, 
                                          f"Rate {rate} not in range 0-100")
                            return False
                    
                    # Verify sorted by total_value (descending)
                    if len(data["team_metrics"]) > 1:
                        first_member = data["team_metrics"][0]
                        second_member = data["team_metrics"][1]
                        if first_member["opportunities"]["total_value"] < second_member["opportunities"]["total_value"]:
                            self.log_result("Team Performance Sort Order", False, 
                                          "Team members not sorted by total_value descending")
                            return False
                        else:
                            self.log_result("Team Performance Sort Order", True, 
                                          "Team members correctly sorted by total_value")
                
                self.log_result("Team Performance API", True, 
                              f"Retrieved performance data for {len(data['team_metrics'])} team members")
                return True
                
            else:
                self.log_result("Team Performance API", False, 
                              f"Failed to get team performance: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Team Performance API", False, f"Error testing team performance API: {str(e)}")
            return False
    
    def test_conversion_rates_api(self):
        """Test Conversion Rates API - GET /api/sales/analytics/conversion-rates"""
        print("\n=== Testing Conversion Rates API ===")
        
        try:
            response = requests.get(f"{API_BASE}/sales/analytics/conversion-rates", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required structure
                required_fields = ["leads", "opportunities"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Conversion Rates Structure", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify leads structure
                leads_data = data["leads"]
                if "funnel" not in leads_data or "conversion_rates" not in leads_data:
                    self.log_result("Conversion Rates Leads Structure", False, 
                                  "Missing funnel or conversion_rates in leads")
                    return False
                
                # Verify lead_funnel structure
                lead_funnel = leads_data["funnel"]
                expected_lead_stages = ["new", "contacted", "qualified", "converted"]
                for stage in expected_lead_stages:
                    if stage not in lead_funnel:
                        self.log_result("Conversion Rates Lead Funnel", False, 
                                      f"Missing lead stage: {stage}")
                        return False
                    
                    if not isinstance(lead_funnel[stage], int) or lead_funnel[stage] < 0:
                        self.log_result("Conversion Rates Lead Count Type", False, 
                                      f"Lead count for {stage} should be non-negative integer")
                        return False
                
                # Verify opportunities structure
                opp_data = data["opportunities"]
                if "funnel" not in opp_data or "conversion_rates" not in opp_data:
                    self.log_result("Conversion Rates Opportunities Structure", False, 
                                  "Missing funnel or conversion_rates in opportunities")
                    return False
                
                # Verify opportunity_funnel structure
                opp_funnel = opp_data["funnel"]
                expected_opp_stages = ["new_lead", "contacted", "qualified", "proposal", "negotiation", "closed_won", "closed_lost"]
                for stage in expected_opp_stages:
                    if stage not in opp_funnel:
                        self.log_result("Conversion Rates Opportunity Funnel", False, 
                                      f"Missing opportunity stage: {stage}")
                        return False
                    
                    if not isinstance(opp_funnel[stage], int) or opp_funnel[stage] < 0:
                        self.log_result("Conversion Rates Opportunity Count Type", False, 
                                      f"Opportunity count for {stage} should be non-negative integer")
                        return False
                
                # Verify lead_conversion_rates structure
                lead_rates = leads_data["conversion_rates"]
                if lead_rates:  # May be empty if no conversions
                    for rate_name, rate_value in lead_rates.items():
                        if not (0 <= rate_value <= 100):
                            self.log_result("Conversion Rates Lead Rate Range", False, 
                                          f"Lead rate {rate_name} ({rate_value}) not in range 0-100")
                            return False
                
                # Verify opportunity_conversion_rates structure
                opp_rates = opp_data["conversion_rates"]
                if opp_rates:  # May be empty if no opportunities
                    for rate_name, rate_value in opp_rates.items():
                        if not (0 <= rate_value <= 100):
                            self.log_result("Conversion Rates Opportunity Rate Range", False, 
                                          f"Opportunity rate {rate_name} ({rate_value}) not in range 0-100")
                            return False
                
                # Verify calculation accuracy (manual check for new_to_contacted)
                if lead_funnel["new"] > 0 and "new_to_contacted" in lead_rates:
                    expected_new_to_contacted = round((lead_funnel["contacted"] / lead_funnel["new"]) * 100, 1)
                    actual_new_to_contacted = lead_rates["new_to_contacted"]
                    if abs(expected_new_to_contacted - actual_new_to_contacted) > 0.1:
                        self.log_result("Conversion Rates Calculation Accuracy", False, 
                                      f"new_to_contacted calculation error: expected {expected_new_to_contacted}, got {actual_new_to_contacted}")
                        return False
                    else:
                        self.log_result("Conversion Rates Calculation Accuracy", True, 
                                      "Conversion rate calculations are accurate")
                
                self.log_result("Conversion Rates API", True, 
                              f"Lead funnel: {sum(lead_funnel.values())} total leads, "
                              f"Opportunity funnel: {sum(opp_funnel.values())} total opportunities")
                return True
                
            else:
                self.log_result("Conversion Rates API", False, 
                              f"Failed to get conversion rates: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Conversion Rates API", False, f"Error testing conversion rates API: {str(e)}")
            return False
    
    # ===================== CLEANUP AND MAIN EXECUTION =====================
    
    def cleanup_test_data(self):
        """Clean up test data created during testing"""
        print("\n=== Cleaning Up Test Data ===")
        
        # Clean up created leads
        for lead_id in self.created_leads:
            try:
                response = requests.delete(f"{API_BASE}/sales/leads/{lead_id}", headers=self.headers)
                if response.status_code == 200:
                    self.log_result(f"Cleanup Lead {lead_id[:8]}", True, "Lead deleted")
                else:
                    self.log_result(f"Cleanup Lead {lead_id[:8]}", False, f"Failed to delete: {response.status_code}")
            except Exception as e:
                self.log_result(f"Cleanup Lead {lead_id[:8]}", False, f"Error: {str(e)}")
        
        # Clean up created workflows
        for workflow_id in self.created_workflows:
            try:
                response = requests.delete(f"{API_BASE}/sales/workflows/{workflow_id}", headers=self.headers)
                if response.status_code == 200:
                    self.log_result(f"Cleanup Workflow {workflow_id[:8]}", True, "Workflow deleted")
                else:
                    self.log_result(f"Cleanup Workflow {workflow_id[:8]}", False, f"Failed to delete: {response.status_code}")
            except Exception as e:
                self.log_result(f"Cleanup Workflow {workflow_id[:8]}", False, f"Error: {str(e)}")
        
        # Clean up created opportunities
        for opp_id in self.created_opportunities:
            try:
                response = requests.delete(f"{API_BASE}/sales/opportunities/{opp_id}", headers=self.headers)
                if response.status_code == 200:
                    self.log_result(f"Cleanup Opportunity {opp_id[:8]}", True, "Opportunity deleted")
                else:
                    self.log_result(f"Cleanup Opportunity {opp_id[:8]}", False, f"Failed to delete: {response.status_code}")
            except Exception as e:
                self.log_result(f"Cleanup Opportunity {opp_id[:8]}", False, f"Error: {str(e)}")
        
        # Clean up created tasks
        for task_id in self.created_tasks:
            try:
                response = requests.delete(f"{API_BASE}/tasks/{task_id}", headers=self.headers)
                if response.status_code == 200:
                    self.log_result(f"Cleanup Task {task_id[:8]}", True, "Task deleted")
                else:
                    self.log_result(f"Cleanup Task {task_id[:8]}", False, f"Failed to delete: {response.status_code}")
            except Exception as e:
                self.log_result(f"Cleanup Task {task_id[:8]}", False, f"Error: {str(e)}")
    
    def run_sales_module_tests(self):
        """Run the Sales Module Phase 2 Advanced API tests"""
        print("=" * 80)
        print("BACKEND TESTING - SALES MODULE PHASE 2 ADVANCED APIS")
        print("=" * 80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Setup test data
        if not self.setup_test_data():
            print("❌ Failed to setup test data. Cannot proceed with tests.")
            return False
        
        # Step 3: Run SALES AUTOMATION API TESTS
        print("\n" + "=" * 60)
        print("SALES AUTOMATION API TESTS")
        print("=" * 60)
        
        sales_automation_results = []
        
        print("\n🎯 TEST 1: Lead Scoring API")
        sales_automation_results.append(self.test_lead_scoring_api())
        
        print("\n🔄 TEST 2: Auto-Assign Lead API")
        sales_automation_results.append(self.test_auto_assign_lead_api())
        
        print("\n📋 TEST 3: Create Follow-Up Tasks API")
        sales_automation_results.append(self.test_create_follow_up_tasks_api())
        
        # Step 4: Run WORKFLOW AUTOMATION API TESTS
        print("\n" + "=" * 60)
        print("WORKFLOW AUTOMATION API TESTS")
        print("=" * 60)
        
        workflow_automation_results = []
        
        print("\n📝 TEST 4: List Workflows API")
        workflow_automation_results.append(self.test_list_workflows_api())
        
        print("\n➕ TEST 5: Create Workflow API")
        workflow_automation_results.append(self.test_create_workflow_api())
        
        print("\n✏️ TEST 6: Update Workflow API")
        workflow_automation_results.append(self.test_update_workflow_api())
        
        print("\n🗑️ TEST 7: Delete Workflow API")
        workflow_automation_results.append(self.test_delete_workflow_api())
        
        print("\n⚡ TEST 8: Execute Workflow API")
        workflow_automation_results.append(self.test_execute_workflow_api())
        
        # Step 5: Run ADVANCED ANALYTICS API TESTS
        print("\n" + "=" * 60)
        print("ADVANCED ANALYTICS API TESTS")
        print("=" * 60)
        
        analytics_results = []
        
        print("\n📈 TEST 9: Sales Forecasting API")
        analytics_results.append(self.test_sales_forecasting_api())
        
        print("\n👥 TEST 10: Team Performance API")
        analytics_results.append(self.test_team_performance_api())
        
        print("\n🔄 TEST 11: Conversion Rates API")
        analytics_results.append(self.test_conversion_rates_api())
        
        # Step 6: Generate Summary
        print("\n" + "=" * 80)
        print("TEST RESULTS SUMMARY")
        print("=" * 80)
        
        sales_automation_passed = sum(sales_automation_results)
        sales_automation_total = len(sales_automation_results)
        
        workflow_automation_passed = sum(workflow_automation_results)
        workflow_automation_total = len(workflow_automation_results)
        
        analytics_passed = sum(analytics_results)
        analytics_total = len(analytics_results)
        
        total_passed = sales_automation_passed + workflow_automation_passed + analytics_passed
        total_tests = sales_automation_total + workflow_automation_total + analytics_total
        
        print(f"\n🎯 SALES AUTOMATION TESTS: {sales_automation_passed}/{sales_automation_total} PASSED")
        print(f"🔄 WORKFLOW AUTOMATION TESTS: {workflow_automation_passed}/{workflow_automation_total} PASSED")
        print(f"📊 ADVANCED ANALYTICS TESTS: {analytics_passed}/{analytics_total} PASSED")
        print(f"\n🏆 OVERALL: {total_passed}/{total_tests} PASSED")
        print(f"📈 SUCCESS RATE: {(total_passed/total_tests)*100:.1f}%")
        
        # Detailed results
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        # Step 7: Cleanup
        self.cleanup_test_data()
        
        # Return success if all tests passed
        return total_passed == total_tests

def main():
    """Main execution function"""
    tester = SalesModulePhase2TestRunner()
    success = tester.run_sales_module_tests()
    
    if success:
        print("\n🎉 ALL SALES MODULE PHASE 2 TESTS PASSED!")
        exit(0)
    else:
        print("\n💥 SOME SALES MODULE PHASE 2 TESTS FAILED!")
        exit(1)

if __name__ == "__main__":
    main()