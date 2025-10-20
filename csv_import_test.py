#!/usr/bin/env python3
"""
CSV Import Name Splitting Test Suite for ERP360 gym management application
Tests the CSV import functionality with name splitting fix
"""

import requests
import json
import time
import os
from datetime import datetime, timezone, timedelta

# Configuration
BASE_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://gym-management-app.preview.emergentagent.com')
API_BASE = f"{BASE_URL}/api"

# Test credentials
TEST_EMAIL = "admin@gym.com"
TEST_PASSWORD = "admin123"

class CSVImportNameSplittingTester:
    """Test CSV Import Name Splitting Fix for ERP360 gym management application"""
    
    def __init__(self):
        self.token = None
        self.headers = {}
        self.test_results = []
        self.csv_file_path = "/app/test_import_names.csv"
        self.imported_member_ids = []
        
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
    
    def test_csv_parse(self):
        """Test CSV parsing functionality"""
        print("\n=== Phase 1: Testing CSV Parse Functionality ===")
        
        try:
            # Check if CSV file exists
            if not os.path.exists(self.csv_file_path):
                self.log_result("CSV File Check", False, f"Test CSV file not found at {self.csv_file_path}")
                return False
            
            # Read the test CSV file
            with open(self.csv_file_path, 'rb') as f:
                files = {'file': ('test_import_names.csv', f, 'text/csv')}
                response = requests.post(f"{API_BASE}/import/parse-csv", 
                                       files=files, headers=self.headers)
            
            if response.status_code == 200:
                parse_result = response.json()
                headers = parse_result.get("headers", [])
                sample_data = parse_result.get("sample_data", [])
                total_rows = parse_result.get("total_rows", 0)
                
                # Verify expected headers
                expected_headers = ["Full Name", "Email", "Mobile Phone", "Member Type"]
                if set(headers) == set(expected_headers):
                    self.log_result("CSV Parse Headers", True, 
                                  f"CSV headers parsed correctly: {headers}")
                else:
                    self.log_result("CSV Parse Headers", False, 
                                  f"Headers mismatch. Expected: {expected_headers}, Got: {headers}")
                
                # Verify total rows (6 data rows)
                if total_rows == 6:
                    self.log_result("CSV Parse Row Count", True, 
                                  f"Correct row count: {total_rows}")
                else:
                    self.log_result("CSV Parse Row Count", False, 
                                  f"Expected 6 rows, got {total_rows}")
                
                # Verify sample data contains expected test cases
                sample_names = [row.get("Full Name", "") for row in sample_data]
                expected_names = ["MR JOHN DOE", "MISS JANE SMITH", "DR ROBERT JOHNSON", 
                                "SARAH WILLIAMS", "MIKE", "MRS EMILY BROWN ANDERSON"]
                
                found_names = [name for name in expected_names if name in sample_names]
                if len(found_names) >= 5:  # Allow for at least 5 out of 6 (sample data might be limited)
                    self.log_result("CSV Parse Sample Data", True, 
                                  f"Expected test cases found: {len(found_names)}/6 - {found_names}")
                else:
                    self.log_result("CSV Parse Sample Data", False, 
                                  f"Too few test cases found. Expected at least 5, got {len(found_names)}: {found_names}")
                
                return True
            else:
                self.log_result("CSV Parse", False, 
                              f"Failed to parse CSV: {response.status_code}",
                              {"response": response.text})
                return False
        except Exception as e:
            self.log_result("CSV Parse", False, f"Error parsing CSV: {str(e)}")
            return False
    
    def test_csv_import_with_name_splitting(self):
        """Test CSV import with name splitting functionality"""
        print("\n=== Phase 2: Testing CSV Import with Name Splitting ===")
        
        try:
            # First, get a membership type for the import
            response = requests.get(f"{API_BASE}/membership-types", headers=self.headers)
            if response.status_code != 200:
                self.log_result("Get Membership Types", False, "Failed to get membership types")
                return False
            
            membership_types = response.json()
            if not membership_types:
                self.log_result("Get Membership Types", False, "No membership types found")
                return False
            
            membership_type_id = membership_types[0]["id"]
            
            # Prepare field mapping
            # Map "Full Name" CSV column to "first_name" field (this should trigger name splitting)
            field_mapping = {
                "first_name": "Full Name",  # This will trigger name splitting
                "email": "Email",
                "phone": "Mobile Phone"
            }
            
            # Read and upload the CSV file with query parameters
            with open(self.csv_file_path, 'rb') as f:
                files = {
                    'file': ('test_import_names.csv', f, 'text/csv'),
                }
                params = {
                    'field_mapping': json.dumps(field_mapping),
                    'duplicate_action': 'skip'
                }
                
                response = requests.post(f"{API_BASE}/import/members", 
                                       files=files, params=params, headers=self.headers)
            
            print(f"DEBUG: Request params: {params}")
            print(f"DEBUG: Request files: {list(files.keys())}")
            print(f"DEBUG: Response status: {response.status_code}")
            print(f"DEBUG: Response text: {response.text}")
            
            if response.status_code == 200:
                import_result = response.json()
                imported_count = import_result.get("successful", 0)  # Use 'successful' key
                failed_count = import_result.get("failed", 0)
                
                # Should import all 6 members successfully
                if imported_count == 6 and failed_count == 0:
                    self.log_result("CSV Import Success", True, 
                                  f"✅ Successfully imported {imported_count} members with 0 failures")
                else:
                    self.log_result("CSV Import Success", False, 
                                  f"Import issues: {imported_count} imported, {failed_count} failed")
                    
                    # Log any errors
                    if "error_log" in import_result:
                        for error in import_result["error_log"]:
                            print(f"   Import Error: {error}")
                
                return imported_count == 6
            else:
                self.log_result("CSV Import", False, 
                              f"Failed to import CSV: {response.status_code}",
                              {"response": response.text})
                return False
        except Exception as e:
            self.log_result("CSV Import", False, f"Error importing CSV: {str(e)}")
            return False
    
    def test_member_fetch_after_import(self):
        """Test that members can be fetched successfully after import (no Pydantic errors)"""
        print("\n=== Phase 3: Testing Member Fetch After Import ===")
        
        try:
            response = requests.get(f"{API_BASE}/members", headers=self.headers)
            
            if response.status_code == 200:
                members = response.json()
                
                # Find imported members by checking for test emails
                imported_members = [m for m in members if m.get("email", "").endswith("@test.com")]
                
                if len(imported_members) >= 6:
                    self.log_result("Member Fetch Success", True, 
                                  f"✅ Successfully fetched {len(imported_members)} imported members without Pydantic errors")
                    
                    # Store member IDs for cleanup
                    self.imported_member_ids = [m["id"] for m in imported_members]
                    
                    return imported_members
                else:
                    self.log_result("Member Fetch Success", False, 
                                  f"Expected at least 6 imported members, found {len(imported_members)}")
                    return []
            else:
                self.log_result("Member Fetch", False, 
                              f"❌ Failed to fetch members: {response.status_code} - This indicates Pydantic validation errors!",
                              {"response": response.text})
                return []
        except Exception as e:
            self.log_result("Member Fetch", False, f"❌ Error fetching members (Pydantic validation failed): {str(e)}")
            return []
    
    def test_name_splitting_correctness(self, imported_members):
        """Test that name splitting was done correctly for each test case"""
        print("\n=== Phase 4: Testing Name Splitting Correctness ===")
        
        # Expected name splitting results based on the test cases
        expected_splits = {
            "john.doe@test.com": {"first_name": "JOHN", "last_name": "DOE"},
            "jane.smith@test.com": {"first_name": "JANE", "last_name": "SMITH"},
            "robert.j@test.com": {"first_name": "ROBERT", "last_name": "JOHNSON"},
            "sarah.w@test.com": {"first_name": "SARAH", "last_name": "WILLIAMS"},
            "mike@test.com": {"first_name": "MIKE", "last_name": "MIKE"},  # Single name case
            "emily.brown@test.com": {"first_name": "EMILY", "last_name": "BROWN ANDERSON"}  # Multiple last names
        }
        
        all_correct = True
        
        for member in imported_members:
            email = member.get("email", "")
            if email in expected_splits:
                expected = expected_splits[email]
                actual_first = member.get("first_name", "")
                actual_last = member.get("last_name", "")
                
                if actual_first == expected["first_name"] and actual_last == expected["last_name"]:
                    self.log_result(f"Name Split - {email}", True, 
                                  f"✅ Correct: '{actual_first}' + '{actual_last}'")
                else:
                    self.log_result(f"Name Split - {email}", False, 
                                  f"❌ Expected: '{expected['first_name']}' + '{expected['last_name']}', "
                                  f"Got: '{actual_first}' + '{actual_last}'")
                    all_correct = False
        
        if all_correct:
            self.log_result("All Name Splits Correct", True, 
                          "✅ All 6 test cases split names correctly")
        else:
            self.log_result("All Name Splits Correct", False, 
                          "❌ Some name splits were incorrect")
        
        return all_correct
    
    def test_required_fields_populated(self, imported_members):
        """Test that all required fields are populated (especially last_name)"""
        print("\n=== Phase 5: Testing Required Fields Population ===")
        
        all_valid = True
        
        for member in imported_members:
            email = member.get("email", "")
            first_name = member.get("first_name", "")
            last_name = member.get("last_name", "")
            
            # Check that both first_name and last_name are present and non-empty
            if not first_name or not last_name:
                self.log_result(f"Required Fields - {email}", False, 
                              f"❌ Missing required fields: first_name='{first_name}', last_name='{last_name}'")
                all_valid = False
            else:
                self.log_result(f"Required Fields - {email}", True, 
                              f"✅ All required fields present: '{first_name}' '{last_name}'")
        
        if all_valid:
            self.log_result("All Required Fields Valid", True, 
                          "✅ All imported members have required first_name and last_name fields")
        else:
            self.log_result("All Required Fields Valid", False, 
                          "❌ Some members missing required fields - this would cause Pydantic errors!")
        
        return all_valid
    
    def test_manual_member_creation(self):
        """Test that manual member creation still works correctly"""
        print("\n=== Phase 6: Testing Manual Member Creation Still Works ===")
        
        try:
            # Get membership type
            response = requests.get(f"{API_BASE}/membership-types", headers=self.headers)
            membership_types = response.json()
            membership_type_id = membership_types[0]["id"]
            
            # Create member manually with separate first_name and last_name
            member_data = {
                "first_name": "Manual",
                "last_name": "TestUser",
                "email": f"manual.test.{int(time.time())}@example.com",
                "phone": "+27999888777",
                "membership_type_id": membership_type_id
            }
            
            response = requests.post(f"{API_BASE}/members", json=member_data, headers=self.headers)
            
            if response.status_code == 200:
                member = response.json()
                
                # Verify fields are correct
                if (member["first_name"] == "Manual" and 
                    member["last_name"] == "TestUser"):
                    self.log_result("Manual Member Creation", True, 
                                  f"✅ Manual member created correctly: {member['first_name']} {member['last_name']}")
                    
                    # Store for cleanup
                    self.imported_member_ids.append(member["id"])
                    return True
                else:
                    self.log_result("Manual Member Creation", False, 
                                  f"❌ Manual member fields incorrect: {member['first_name']} {member['last_name']}")
                    return False
            else:
                self.log_result("Manual Member Creation", False, 
                              f"❌ Failed to create manual member: {response.status_code}",
                              {"response": response.text})
                return False
        except Exception as e:
            self.log_result("Manual Member Creation", False, f"❌ Error creating manual member: {str(e)}")
            return False
    
    def cleanup_imported_members(self):
        """Clean up imported test members"""
        print("\n=== Cleaning Up Test Members ===")
        
        cleanup_count = 0
        for member_id in self.imported_member_ids:
            try:
                response = requests.delete(f"{API_BASE}/members/{member_id}", headers=self.headers)
                if response.status_code == 200:
                    cleanup_count += 1
            except Exception as e:
                print(f"Failed to cleanup member {member_id}: {str(e)}")
        
        self.log_result("Cleanup Test Members", True, 
                      f"Cleaned up {cleanup_count} test members")
    
    def run_csv_import_tests(self):
        """Run all CSV import name splitting tests"""
        print("🚀 Starting CSV Import Name Splitting Tests")
        print("Testing CSV Import Name Splitting Fix for ERP360 gym management application")
        print(f"Testing against: {API_BASE}")
        print(f"Test CSV file: {self.csv_file_path}")
        print("=" * 80)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return
        
        # Run test sequence according to the test plan
        success_count = 0
        
        # Phase 1: Test CSV parsing
        if self.test_csv_parse():
            success_count += 1
            
            # Phase 2: Test CSV import with name splitting
            if self.test_csv_import_with_name_splitting():
                success_count += 1
                
                # Phase 3: Test member fetch (critical - this was failing before the fix)
                imported_members = self.test_member_fetch_after_import()
                if imported_members:
                    success_count += 1
                    
                    # Phase 4: Test name splitting correctness
                    if self.test_name_splitting_correctness(imported_members):
                        success_count += 1
                    
                    # Phase 5: Test required fields population
                    if self.test_required_fields_populated(imported_members):
                        success_count += 1
                
                # Phase 6: Test manual member creation still works
                if self.test_manual_member_creation():
                    success_count += 1
        
        # Cleanup
        self.cleanup_imported_members()
        
        # Print summary
        self.print_summary()
        
        # Final assessment
        print(f"\n🎯 TEST COMPLETION: {success_count}/6 phases completed successfully")
        if success_count == 6:
            print("🎉 ALL TESTS PASSED - CSV Import Name Splitting Fix is working correctly!")
        else:
            print("⚠️  Some tests failed - CSV Import Name Splitting Fix needs attention")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🏁 CSV IMPORT NAME SPLITTING TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        # Categorize results
        critical_tests = [r for r in self.test_results if "Member Fetch" in r["test"] or "Name Split" in r["test"]]
        critical_passed = len([r for r in critical_tests if r["success"]])
        
        print(f"\n🔥 CRITICAL TESTS (Name Splitting & Member Fetch): {critical_passed}/{len(critical_tests)} passed")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    # Run CSV Import Name Splitting Tests
    csv_tester = CSVImportNameSplittingTester()
    csv_tester.run_csv_import_tests()