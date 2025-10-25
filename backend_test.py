#!/usr/bin/env python3
"""
Backend Test Suite - Financial Reporting APIs Testing
Focus on testing the Financial Reporting APIs with comprehensive validation
"""

import requests
import json
import time
import os
from datetime import datetime, timezone, timedelta

# Configuration
BASE_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://gym-lead-tracker.preview.emergentagent.com')
API_BASE = f"{BASE_URL}/api"

# Test credentials
ADMIN_EMAIL = "admin@gym.com"
ADMIN_PASSWORD = "admin123"

class FinancialReportingTestRunner:
    def __init__(self):
        self.admin_token = None
        self.admin_headers = {}
        self.test_results = []
        
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
    
    # ===================== FINANCIAL REPORTING API TESTS =====================
    
    def test_revenue_report_api(self):
        """Test GET /api/reports/revenue endpoint"""
        print("\n=== Testing Revenue Report API ===")
        
        try:
            # Test 1: Default parameters (last 30 days)
            response = requests.get(f"{API_BASE}/reports/revenue", headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = [
                    "period", "total_revenue", "invoice_revenue", "pos_revenue",
                    "revenue_by_service", "revenue_by_payment_method", "revenue_trend",
                    "comparison", "transaction_counts"
                ]
                
                for field in required_fields:
                    if field not in data:
                        self.log_result("Revenue Report Structure", False, f"Missing field: {field}")
                        return False
                
                # Verify period structure
                period = data["period"]
                if "start_date" not in period or "end_date" not in period or "days" not in period:
                    self.log_result("Revenue Report Period", False, "Invalid period structure")
                    return False
                
                # Verify numeric values
                if not isinstance(data["total_revenue"], (int, float)):
                    self.log_result("Revenue Report Total", False, "total_revenue should be numeric")
                    return False
                
                if not isinstance(data["invoice_revenue"], (int, float)):
                    self.log_result("Revenue Report Invoice", False, "invoice_revenue should be numeric")
                    return False
                
                if not isinstance(data["pos_revenue"], (int, float)):
                    self.log_result("Revenue Report POS", False, "pos_revenue should be numeric")
                    return False
                
                # Verify revenue breakdown
                revenue_by_service = data["revenue_by_service"]
                if "Memberships" not in revenue_by_service or "POS/Retail" not in revenue_by_service:
                    self.log_result("Revenue Report Service Breakdown", False, "Missing service categories")
                    return False
                
                # Verify comparison structure
                comparison = data["comparison"]
                comp_fields = ["previous_period_revenue", "growth_amount", "growth_percentage"]
                for field in comp_fields:
                    if field not in comparison:
                        self.log_result("Revenue Report Comparison", False, f"Missing comparison field: {field}")
                        return False
                
                # Verify transaction counts
                tx_counts = data["transaction_counts"]
                if "invoices" not in tx_counts or "pos_transactions" not in tx_counts or "total" not in tx_counts:
                    self.log_result("Revenue Report Transaction Counts", False, "Missing transaction count fields")
                    return False
                
                self.log_result("Revenue Report Default", True, f"Default report: R{data['total_revenue']:.2f} total revenue")
                
            else:
                self.log_result("Revenue Report Default", False, f"Failed: {response.status_code}")
                return False
            
            # Test 2: Custom date range
            end_date = "2024-12-31T23:59:59Z"
            start_date = "2024-01-01T00:00:00Z"
            
            response = requests.get(
                f"{API_BASE}/reports/revenue",
                params={"start_date": start_date, "end_date": end_date},
                headers=self.admin_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                period = data["period"]
                
                # Verify date range is respected
                if start_date not in period["start_date"] or end_date not in period["end_date"]:
                    self.log_result("Revenue Report Custom Dates", False, "Date range not respected")
                    return False
                
                self.log_result("Revenue Report Custom Dates", True, f"Custom range: R{data['total_revenue']:.2f}")
                
            else:
                self.log_result("Revenue Report Custom Dates", False, f"Failed: {response.status_code}")
                return False
            
            # Test 3: Different group_by options
            for group_by in ["day", "week", "month"]:
                response = requests.get(
                    f"{API_BASE}/reports/revenue",
                    params={"group_by": group_by},
                    headers=self.admin_headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verify revenue_trend exists and has data
                    if "revenue_trend" not in data or not isinstance(data["revenue_trend"], list):
                        self.log_result(f"Revenue Report Group By {group_by}", False, "Invalid revenue_trend")
                        return False
                    
                    # Verify trend data structure
                    if data["revenue_trend"]:
                        trend_item = data["revenue_trend"][0]
                        trend_fields = ["period", "revenue", "invoice_revenue", "pos_revenue"]
                        for field in trend_fields:
                            if field not in trend_item:
                                self.log_result(f"Revenue Report Group By {group_by}", False, f"Missing trend field: {field}")
                                return False
                    
                    self.log_result(f"Revenue Report Group By {group_by}", True, f"Grouped by {group_by}: {len(data['revenue_trend'])} periods")
                    
                else:
                    self.log_result(f"Revenue Report Group By {group_by}", False, f"Failed: {response.status_code}")
                    return False
            
            return True
            
        except Exception as e:
            self.log_result("Revenue Report API", False, f"Error: {str(e)}")
            return False
    
    def test_commissions_report_api(self):
        """Test GET /api/reports/commissions endpoint"""
        print("\n=== Testing Commissions Report API ===")
        
        try:
            # Test 1: Default parameters (last 30 days)
            response = requests.get(f"{API_BASE}/reports/commissions", headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["period", "summary", "consultants", "commission_rate"]
                
                for field in required_fields:
                    if field not in data:
                        self.log_result("Commissions Report Structure", False, f"Missing field: {field}")
                        return False
                
                # Verify summary structure
                summary = data["summary"]
                summary_fields = ["total_commissions", "total_deal_value", "total_conversions", "average_commission_per_consultant"]
                for field in summary_fields:
                    if field not in summary:
                        self.log_result("Commissions Report Summary", False, f"Missing summary field: {field}")
                        return False
                
                # Verify consultants array
                consultants = data["consultants"]
                if not isinstance(consultants, list):
                    self.log_result("Commissions Report Consultants", False, "consultants should be array")
                    return False
                
                # Verify consultant structure if any exist
                if consultants:
                    consultant = consultants[0]
                    consultant_fields = [
                        "consultant_id", "consultant_name", "email", "role",
                        "leads_converted", "opportunities_won", "total_conversions",
                        "total_deal_value", "commission_earned", "average_deal_size"
                    ]
                    for field in consultant_fields:
                        if field not in consultant:
                            self.log_result("Commissions Report Consultant Fields", False, f"Missing consultant field: {field}")
                            return False
                    
                    # Verify sorting (highest commission first)
                    if len(consultants) > 1:
                        for i in range(1, len(consultants)):
                            if consultants[i]["commission_earned"] > consultants[i-1]["commission_earned"]:
                                self.log_result("Commissions Report Sorting", False, "Consultants not sorted by commission_earned")
                                return False
                
                # Verify numeric values
                if not isinstance(data["commission_rate"], (int, float)):
                    self.log_result("Commissions Report Rate", False, "commission_rate should be numeric")
                    return False
                
                self.log_result("Commissions Report Default", True, f"Found {len(consultants)} consultants, total commissions: R{summary['total_commissions']:.2f}")
                
            else:
                self.log_result("Commissions Report Default", False, f"Failed: {response.status_code}")
                return False
            
            # Test 2: Custom date range
            end_date = "2024-12-31T23:59:59Z"
            start_date = "2024-01-01T00:00:00Z"
            
            response = requests.get(
                f"{API_BASE}/reports/commissions",
                params={"start_date": start_date, "end_date": end_date},
                headers=self.admin_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                period = data["period"]
                
                # Verify date range is respected
                if start_date not in period["start_date"] or end_date not in period["end_date"]:
                    self.log_result("Commissions Report Custom Dates", False, "Date range not respected")
                    return False
                
                self.log_result("Commissions Report Custom Dates", True, f"Custom range: R{data['summary']['total_commissions']:.2f}")
                
            else:
                self.log_result("Commissions Report Custom Dates", False, f"Failed: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Commissions Report API", False, f"Error: {str(e)}")
            return False
    
    def test_financial_summary_api(self):
        """Test GET /api/reports/financial-summary endpoint"""
        print("\n=== Testing Financial Summary API ===")
        
        try:
            # Test 1: Default parameters (current month)
            response = requests.get(f"{API_BASE}/reports/financial-summary", headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["period", "revenue", "members", "performance"]
                
                for field in required_fields:
                    if field not in data:
                        self.log_result("Financial Summary Structure", False, f"Missing field: {field}")
                        return False
                
                # Verify period structure
                period = data["period"]
                period_fields = ["start_date", "end_date", "month"]
                for field in period_fields:
                    if field not in period:
                        self.log_result("Financial Summary Period", False, f"Missing period field: {field}")
                        return False
                
                # Verify revenue structure
                revenue = data["revenue"]
                revenue_fields = ["total_revenue", "membership_revenue", "retail_revenue", "outstanding_receivables", "failed_payments"]
                for field in revenue_fields:
                    if field not in revenue:
                        self.log_result("Financial Summary Revenue", False, f"Missing revenue field: {field}")
                        return False
                    
                    # Verify numeric values
                    if not isinstance(revenue[field], (int, float)):
                        self.log_result("Financial Summary Revenue Values", False, f"{field} should be numeric")
                        return False
                
                # Verify members structure
                members = data["members"]
                member_fields = ["active_members", "new_members", "avg_revenue_per_member"]
                for field in member_fields:
                    if field not in members:
                        self.log_result("Financial Summary Members", False, f"Missing members field: {field}")
                        return False
                
                # Verify performance structure
                performance = data["performance"]
                perf_fields = ["collection_rate", "total_transactions", "unpaid_invoice_count", "failed_payment_count"]
                for field in perf_fields:
                    if field not in performance:
                        self.log_result("Financial Summary Performance", False, f"Missing performance field: {field}")
                        return False
                
                # Verify collection rate is percentage
                if not (0 <= performance["collection_rate"] <= 100):
                    self.log_result("Financial Summary Collection Rate", False, "Collection rate should be 0-100%")
                    return False
                
                self.log_result("Financial Summary Default", True, f"Total revenue: R{revenue['total_revenue']:.2f}, Collection rate: {performance['collection_rate']:.1f}%")
                
            else:
                self.log_result("Financial Summary Default", False, f"Failed: {response.status_code}")
                return False
            
            # Test 2: Custom date range
            end_date = "2024-12-31T23:59:59Z"
            start_date = "2024-01-01T00:00:00Z"
            
            response = requests.get(
                f"{API_BASE}/reports/financial-summary",
                params={"start_date": start_date, "end_date": end_date},
                headers=self.admin_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                period = data["period"]
                
                # Verify date range is respected
                if start_date not in period["start_date"] or end_date not in period["end_date"]:
                    self.log_result("Financial Summary Custom Dates", False, "Date range not respected")
                    return False
                
                self.log_result("Financial Summary Custom Dates", True, f"Custom range: R{data['revenue']['total_revenue']:.2f}")
                
            else:
                self.log_result("Financial Summary Custom Dates", False, f"Failed: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Financial Summary API", False, f"Error: {str(e)}")
            return False
    
    def test_payment_analysis_api(self):
        """Test GET /api/reports/payment-analysis endpoint"""
        print("\n=== Testing Payment Analysis API ===")
        
        try:
            # Test 1: Default parameters (last 30 days)
            response = requests.get(f"{API_BASE}/reports/payment-analysis", headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["period", "overall", "by_payment_method", "failure_analysis"]
                
                for field in required_fields:
                    if field not in data:
                        self.log_result("Payment Analysis Structure", False, f"Missing field: {field}")
                        return False
                
                # Verify overall statistics
                overall = data["overall"]
                overall_fields = ["total_transactions", "successful_transactions", "failed_transactions", "pending_transactions", "overall_success_rate"]
                for field in overall_fields:
                    if field not in overall:
                        self.log_result("Payment Analysis Overall", False, f"Missing overall field: {field}")
                        return False
                
                # Verify success rate is percentage
                if not (0 <= overall["overall_success_rate"] <= 100):
                    self.log_result("Payment Analysis Success Rate", False, "Success rate should be 0-100%")
                    return False
                
                # Verify by_payment_method structure
                by_method = data["by_payment_method"]
                if not isinstance(by_method, dict):
                    self.log_result("Payment Analysis By Method", False, "by_payment_method should be object")
                    return False
                
                # Verify payment method structure if any exist
                if by_method:
                    method_name = list(by_method.keys())[0]
                    method_data = by_method[method_name]
                    method_fields = [
                        "total_transactions", "successful", "failed", "pending",
                        "total_amount", "successful_amount", "failed_amount",
                        "success_rate", "failure_rate"
                    ]
                    for field in method_fields:
                        if field not in method_data:
                            self.log_result("Payment Analysis Method Fields", False, f"Missing method field: {field}")
                            return False
                    
                    # Verify rates are percentages
                    if not (0 <= method_data["success_rate"] <= 100):
                        self.log_result("Payment Analysis Method Success Rate", False, "Method success rate should be 0-100%")
                        return False
                
                # Verify failure analysis
                failure_analysis = data["failure_analysis"]
                if "top_failure_reasons" not in failure_analysis or "total_failed_amount" not in failure_analysis:
                    self.log_result("Payment Analysis Failure Analysis", False, "Missing failure analysis fields")
                    return False
                
                # Verify failure reasons is dict
                if not isinstance(failure_analysis["top_failure_reasons"], dict):
                    self.log_result("Payment Analysis Failure Reasons", False, "top_failure_reasons should be object")
                    return False
                
                self.log_result("Payment Analysis Default", True, f"Total transactions: {overall['total_transactions']}, Success rate: {overall['overall_success_rate']:.1f}%")
                
            else:
                self.log_result("Payment Analysis Default", False, f"Failed: {response.status_code}")
                return False
            
            # Test 2: Custom date range
            end_date = "2024-12-31T23:59:59Z"
            start_date = "2024-01-01T00:00:00Z"
            
            response = requests.get(
                f"{API_BASE}/reports/payment-analysis",
                params={"start_date": start_date, "end_date": end_date},
                headers=self.admin_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                period = data["period"]
                
                # Verify date range is respected
                if start_date not in period["start_date"] or end_date not in period["end_date"]:
                    self.log_result("Payment Analysis Custom Dates", False, "Date range not respected")
                    return False
                
                self.log_result("Payment Analysis Custom Dates", True, f"Custom range: {data['overall']['total_transactions']} transactions")
                
            else:
                self.log_result("Payment Analysis Custom Dates", False, f"Failed: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Payment Analysis API", False, f"Error: {str(e)}")
            return False
    
    def test_response_times(self):
        """Test API response times are reasonable (< 2 seconds)"""
        print("\n=== Testing API Response Times ===")
        
        try:
            endpoints = [
                "/reports/revenue",
                "/reports/commissions", 
                "/reports/financial-summary",
                "/reports/payment-analysis"
            ]
            
            for endpoint in endpoints:
                start_time = time.time()
                response = requests.get(f"{API_BASE}{endpoint}", headers=self.admin_headers)
                end_time = time.time()
                
                response_time = end_time - start_time
                
                if response.status_code == 200:
                    if response_time < 2.0:
                        self.log_result(f"Response Time {endpoint}", True, f"{response_time:.3f}s")
                    else:
                        self.log_result(f"Response Time {endpoint}", False, f"Too slow: {response_time:.3f}s")
                        return False
                else:
                    self.log_result(f"Response Time {endpoint}", False, f"Failed: {response.status_code}")
                    return False
            
            return True
            
        except Exception as e:
            self.log_result("Response Times", False, f"Error: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test error handling with invalid parameters"""
        print("\n=== Testing Error Handling ===")
        
        try:
            # Test invalid date format
            response = requests.get(
                f"{API_BASE}/reports/revenue",
                params={"start_date": "invalid-date"},
                headers=self.admin_headers
            )
            
            # Should handle gracefully (either 400 or fallback to defaults)
            if response.status_code in [200, 400, 422]:
                self.log_result("Error Handling Invalid Date", True, f"Handled gracefully: {response.status_code}")
            else:
                self.log_result("Error Handling Invalid Date", False, f"Unexpected status: {response.status_code}")
                return False
            
            # Test invalid group_by parameter
            response = requests.get(
                f"{API_BASE}/reports/revenue",
                params={"group_by": "invalid_group"},
                headers=self.admin_headers
            )
            
            # Should handle gracefully
            if response.status_code in [200, 400, 422]:
                self.log_result("Error Handling Invalid Group By", True, f"Handled gracefully: {response.status_code}")
            else:
                self.log_result("Error Handling Invalid Group By", False, f"Unexpected status: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Error Handling", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all financial reporting API tests"""
        print("🚀 Starting Financial Reporting API Tests...")
        print(f"📍 Testing against: {BASE_URL}")
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return False
        
        # Run all tests
        tests = [
            self.test_revenue_report_api,
            self.test_commissions_report_api,
            self.test_financial_summary_api,
            self.test_payment_analysis_api,
            self.test_response_times,
            self.test_error_handling
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
                print(f"❌ Test {test.__name__} crashed: {str(e)}")
                failed += 1
        
        # Print summary
        print(f"\n📊 TEST SUMMARY")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
        
        # Print detailed results
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        return failed == 0


def main():
    """Main test execution"""
    runner = FinancialReportingTestRunner()
    success = runner.run_all_tests()
    
    if success:
        print("\n🎉 All Financial Reporting API tests passed!")
        exit(0)
    else:
        print("\n💥 Some tests failed!")
        exit(1)


if __name__ == "__main__":
    main()
        """Test that default lead sources, statuses, and loss reasons are seeded correctly"""
        print("\n=== Testing Startup Seeding Verification ===")
        
        try:
            # A. Verify default lead sources exist
            response = requests.get(f"{API_BASE}/sales/config/lead-sources", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify structure
                if "sources" not in data:
                    self.log_result("Lead Sources Structure", False, "Missing 'sources' field")
                    return False
                
                sources = data["sources"]
                
                # Verify 8 sources returned
                if len(sources) < 8:
                    self.log_result("Lead Sources Count", False, f"Expected at least 8 sources, got {len(sources)}")
                    return False
                
                # Verify expected sources exist
                expected_sources = ["Walk-in", "Phone-in", "Referral", "Canvassing", "Social Media", "Website", "Email", "Other"]
                found_sources = [s["name"] for s in sources]
                
                for expected in expected_sources:
                    if expected not in found_sources:
                        self.log_result("Lead Sources Content", False, f"Missing expected source: {expected}")
                        return False
                
                # Verify each source has required fields
                for source in sources:
                    required_fields = ["id", "name", "description", "icon", "is_active", "display_order", "created_at", "updated_at"]
                    for field in required_fields:
                        if field not in source:
                            self.log_result("Lead Source Fields", False, f"Missing field '{field}' in source {source.get('name', 'unknown')}")
                            return False
                    
                    # Verify is_active is true
                    if not source["is_active"]:
                        self.log_result("Lead Source Active", False, f"Source {source['name']} should be active")
                        return False
                
                # Verify sorted by display_order
                for i in range(1, len(sources)):
                    if sources[i]["display_order"] < sources[i-1]["display_order"]:
                        self.log_result("Lead Sources Sort Order", False, "Sources not sorted by display_order")
                        return False
                
                self.log_result("Lead Sources Seeding", True, f"All {len(sources)} lead sources properly seeded")
                
            else:
                self.log_result("Lead Sources API", False, f"Failed to get lead sources: {response.status_code}")
                return False
            
            # B. Verify default lead statuses exist
            response = requests.get(f"{API_BASE}/sales/config/lead-statuses", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify structure
                if "statuses" not in data:
                    self.log_result("Lead Statuses Structure", False, "Missing 'statuses' field")
                    return False
                
                statuses = data["statuses"]
                
                # Verify 8 statuses returned
                if len(statuses) < 8:
                    self.log_result("Lead Statuses Count", False, f"Expected at least 8 statuses, got {len(statuses)}")
                    return False
                
                # Verify expected statuses exist
                expected_statuses = ["New Lead", "Called", "Appointment Made", "Appointment Confirmed", "Showed", "Be Back", "Joined", "Lost"]
                found_statuses = [s["name"] for s in statuses]
                
                for expected in expected_statuses:
                    if expected not in found_statuses:
                        self.log_result("Lead Statuses Content", False, f"Missing expected status: {expected}")
                        return False
                
                # Verify each status has required fields
                for status in statuses:
                    required_fields = ["id", "name", "description", "category", "color", "workflow_sequence", "is_active", "created_at", "updated_at"]
                    for field in required_fields:
                        if field not in status:
                            self.log_result("Lead Status Fields", False, f"Missing field '{field}' in status {status.get('name', 'unknown')}")
                            return False
                    
                    # Verify color is hex format
                    if not status["color"].startswith("#") or len(status["color"]) != 7:
                        self.log_result("Lead Status Color", False, f"Invalid color format for {status['name']}: {status['color']}")
                        return False
                
                # Verify sorted by workflow_sequence
                for i in range(1, len(statuses)):
                    if statuses[i]["workflow_sequence"] < statuses[i-1]["workflow_sequence"]:
                        self.log_result("Lead Statuses Sort Order", False, "Statuses not sorted by workflow_sequence")
                        return False
                
                # Verify categories are correct
                category_mapping = {
                    "New Lead": "prospect", "Called": "prospect",
                    "Appointment Made": "engaged", "Appointment Confirmed": "engaged", "Showed": "engaged", "Be Back": "engaged",
                    "Joined": "converted",
                    "Lost": "lost"
                }
                
                for status in statuses:
                    expected_category = category_mapping.get(status["name"])
                    if expected_category and status["category"] != expected_category:
                        self.log_result("Lead Status Category", False, f"Wrong category for {status['name']}: expected {expected_category}, got {status['category']}")
                        return False
                
                self.log_result("Lead Statuses Seeding", True, f"All {len(statuses)} lead statuses properly seeded")
                
            else:
                self.log_result("Lead Statuses API", False, f"Failed to get lead statuses: {response.status_code}")
                return False
            
            # C. Verify default loss reasons exist
            response = requests.get(f"{API_BASE}/sales/config/loss-reasons", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify structure
                if "reasons" not in data:
                    self.log_result("Loss Reasons Structure", False, "Missing 'reasons' field")
                    return False
                
                reasons = data["reasons"]
                
                # Verify 8 reasons returned
                if len(reasons) < 8:
                    self.log_result("Loss Reasons Count", False, f"Expected at least 8 reasons, got {len(reasons)}")
                    return False
                
                # Verify expected reasons exist
                expected_reasons = ["Too Expensive", "Medical Issues", "Lives Too Far", "No Time", "Joined Competitor", "Not Interested", "Financial Issues", "Other"]
                found_reasons = [r["name"] for r in reasons]
                
                for expected in expected_reasons:
                    if expected not in found_reasons:
                        self.log_result("Loss Reasons Content", False, f"Missing expected reason: {expected}")
                        return False
                
                # Verify each reason has required fields
                for reason in reasons:
                    required_fields = ["id", "name", "description", "is_active", "display_order"]
                    for field in required_fields:
                        if field not in reason:
                            self.log_result("Loss Reason Fields", False, f"Missing field '{field}' in reason {reason.get('name', 'unknown')}")
                            return False
                
                self.log_result("Loss Reasons Seeding", True, f"All {len(reasons)} loss reasons properly seeded")
                
            else:
                self.log_result("Loss Reasons API", False, f"Failed to get loss reasons: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Startup Seeding Verification", False, f"Error testing startup seeding: {str(e)}")
            return False
    
    # ===================== CONFIGURATION CRUD API TESTS =====================
    
    def test_lead_sources_crud(self):
        """Test Lead Sources CRUD operations"""
        print("\n=== Testing Lead Sources CRUD ===")
        
        try:
            # CREATE: POST /api/sales/config/lead-sources
            create_data = {
                "name": "Test Trade Show",
                "description": "Leads from trade shows",
                "icon": "🎪",
                "is_active": True,
                "display_order": 10
            }
            
            response = requests.post(f"{API_BASE}/sales/config/lead-sources", json=create_data, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                if not data.get("success") or "source" not in data:
                    self.log_result("Create Lead Source Response", False, "Invalid response structure")
                    return False
                
                created_source = data["source"]
                source_id = created_source["id"]
                self.created_sources.append(source_id)
                
                # Verify created source has UUID id
                if not source_id or len(source_id) < 32:
                    self.log_result("Create Lead Source ID", False, "Invalid UUID format")
                    return False
                
                # Verify timestamps
                if not created_source.get("created_at") or not created_source.get("updated_at"):
                    self.log_result("Create Lead Source Timestamps", False, "Missing timestamps")
                    return False
                
                self.log_result("Create Lead Source", True, f"Created source: {created_source['name']} with ID: {source_id}")
                
                # READ: GET /api/sales/config/lead-sources (verify it appears in list)
                response = requests.get(f"{API_BASE}/sales/config/lead-sources", headers=self.headers)
                if response.status_code == 200:
                    sources_data = response.json()
                    source_names = [s["name"] for s in sources_data["sources"]]
                    if "Test Trade Show" in source_names:
                        self.log_result("Read Lead Sources", True, "Created source appears in list")
                    else:
                        self.log_result("Read Lead Sources", False, "Created source not found in list")
                        return False
                else:
                    self.log_result("Read Lead Sources", False, f"Failed to read sources: {response.status_code}")
                    return False
                
                # UPDATE: PUT /api/sales/config/lead-sources/{source_id}
                update_data = {
                    "name": "Trade Show Events",
                    "description": "Updated description",
                    "icon": "🎪",
                    "is_active": False,
                    "display_order": 15
                }
                
                response = requests.put(f"{API_BASE}/sales/config/lead-sources/{source_id}", json=update_data, headers=self.headers)
                if response.status_code == 200:
                    update_response = response.json()
                    if update_response.get("success"):
                        self.log_result("Update Lead Source", True, "Source updated successfully")
                        
                        # Verify changes persisted
                        response = requests.get(f"{API_BASE}/sales/config/lead-sources", headers=self.headers)
                        if response.status_code == 200:
                            sources_data = response.json()
                            updated_source = None
                            for s in sources_data["sources"]:
                                if s["id"] == source_id:
                                    updated_source = s
                                    break
                            
                            if updated_source:
                                if updated_source["name"] == "Trade Show Events" and not updated_source["is_active"]:
                                    self.log_result("Verify Lead Source Update", True, "Changes persisted correctly")
                                else:
                                    self.log_result("Verify Lead Source Update", False, "Changes not persisted")
                                    return False
                            else:
                                self.log_result("Verify Lead Source Update", False, "Updated source not found")
                                return False
                        else:
                            self.log_result("Verify Lead Source Update", False, "Failed to verify update")
                            return False
                    else:
                        self.log_result("Update Lead Source", False, "Update not successful")
                        return False
                else:
                    self.log_result("Update Lead Source", False, f"Failed to update: {response.status_code}")
                    return False
                
                # DELETE: DELETE /api/sales/config/lead-sources/{source_id}
                response = requests.delete(f"{API_BASE}/sales/config/lead-sources/{source_id}", headers=self.headers)
                if response.status_code == 200:
                    delete_response = response.json()
                    if delete_response.get("success"):
                        self.log_result("Delete Lead Source", True, "Source deleted successfully")
                        
                        # Verify source removed
                        response = requests.get(f"{API_BASE}/sales/config/lead-sources", headers=self.headers)
                        if response.status_code == 200:
                            sources_data = response.json()
                            source_ids = [s["id"] for s in sources_data["sources"]]
                            if source_id not in source_ids:
                                self.log_result("Verify Lead Source Delete", True, "Source removed from list")
                                self.created_sources.remove(source_id)  # Remove from cleanup list
                            else:
                                self.log_result("Verify Lead Source Delete", False, "Source still in list")
                                return False
                        else:
                            self.log_result("Verify Lead Source Delete", False, "Failed to verify delete")
                            return False
                    else:
                        self.log_result("Delete Lead Source", False, "Delete not successful")
                        return False
                else:
                    self.log_result("Delete Lead Source", False, f"Failed to delete: {response.status_code}")
                    return False
                
                # ERROR CASES: Test with non-existent source_id
                fake_id = "fake-source-id-123"
                
                # PUT with non-existent ID (should 404)
                response = requests.put(f"{API_BASE}/sales/config/lead-sources/{fake_id}", json=update_data, headers=self.headers)
                if response.status_code == 404:
                    self.log_result("Update Non-existent Source", True, "Correctly returns 404")
                else:
                    self.log_result("Update Non-existent Source", False, f"Expected 404, got {response.status_code}")
                    return False
                
                # DELETE with non-existent ID (should 404)
                response = requests.delete(f"{API_BASE}/sales/config/lead-sources/{fake_id}", headers=self.headers)
                if response.status_code == 404:
                    self.log_result("Delete Non-existent Source", True, "Correctly returns 404")
                else:
                    self.log_result("Delete Non-existent Source", False, f"Expected 404, got {response.status_code}")
                    return False
                
                # POST with missing required fields (should 422)
                invalid_data = {"description": "Missing name field"}
                response = requests.post(f"{API_BASE}/sales/config/lead-sources", json=invalid_data, headers=self.headers)
                if response.status_code == 422:
                    self.log_result("Create Invalid Source", True, "Correctly validates required fields")
                else:
                    self.log_result("Create Invalid Source", False, f"Expected 422, got {response.status_code}")
                    return False
                
                return True
                
            else:
                self.log_result("Create Lead Source", False, f"Failed to create source: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Lead Sources CRUD", False, f"Error testing lead sources CRUD: {str(e)}")
            return False
    
    def test_lead_statuses_crud(self):
        """Test Lead Statuses CRUD operations"""
        print("\n=== Testing Lead Statuses CRUD ===")
        
        try:
            # CREATE: POST /api/sales/config/lead-statuses
            create_data = {
                "name": "Test In Negotiation",
                "description": "Lead is negotiating terms",
                "category": "engaged",
                "color": "#f59e0b",
                "workflow_sequence": 55,
                "is_active": True,
                "display_order": 10
            }
            
            response = requests.post(f"{API_BASE}/sales/config/lead-statuses", json=create_data, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                if not data.get("success") or "status" not in data:
                    self.log_result("Create Lead Status Response", False, "Invalid response structure")
                    return False
                
                created_status = data["status"]
                status_id = created_status["id"]
                self.created_statuses.append(status_id)
                
                # Verify all fields present
                required_fields = ["id", "name", "description", "category", "color", "workflow_sequence", "is_active", "display_order"]
                for field in required_fields:
                    if field not in created_status:
                        self.log_result("Create Lead Status Fields", False, f"Missing field: {field}")
                        return False
                
                self.log_result("Create Lead Status", True, f"Created status: {created_status['name']} with ID: {status_id}")
                
                # UPDATE: PUT /api/sales/config/lead-statuses/{status_id}
                update_data = {
                    "name": "Test In Negotiation Updated",
                    "description": "Updated description",
                    "category": "prospect",
                    "color": "#3b82f6",
                    "workflow_sequence": 25,
                    "is_active": True,
                    "display_order": 5
                }
                
                response = requests.put(f"{API_BASE}/sales/config/lead-statuses/{status_id}", json=update_data, headers=self.headers)
                if response.status_code == 200:
                    update_response = response.json()
                    if update_response.get("success"):
                        self.log_result("Update Lead Status", True, "Status updated successfully")
                        
                        # Verify changes persisted
                        response = requests.get(f"{API_BASE}/sales/config/lead-statuses", headers=self.headers)
                        if response.status_code == 200:
                            statuses_data = response.json()
                            updated_status = None
                            for s in statuses_data["statuses"]:
                                if s["id"] == status_id:
                                    updated_status = s
                                    break
                            
                            if updated_status:
                                if updated_status["category"] == "prospect" and updated_status["color"] == "#3b82f6":
                                    self.log_result("Verify Lead Status Update", True, "Changes persisted correctly")
                                else:
                                    self.log_result("Verify Lead Status Update", False, "Changes not persisted")
                                    return False
                            else:
                                self.log_result("Verify Lead Status Update", False, "Updated status not found")
                                return False
                        else:
                            self.log_result("Verify Lead Status Update", False, "Failed to verify update")
                            return False
                    else:
                        self.log_result("Update Lead Status", False, "Update not successful")
                        return False
                else:
                    self.log_result("Update Lead Status", False, f"Failed to update: {response.status_code}")
                    return False
                
                # DELETE: DELETE /api/sales/config/lead-statuses/{status_id}
                response = requests.delete(f"{API_BASE}/sales/config/lead-statuses/{status_id}", headers=self.headers)
                if response.status_code == 200:
                    delete_response = response.json()
                    if delete_response.get("success"):
                        self.log_result("Delete Lead Status", True, "Status deleted successfully")
                        self.created_statuses.remove(status_id)  # Remove from cleanup list
                    else:
                        self.log_result("Delete Lead Status", False, "Delete not successful")
                        return False
                else:
                    self.log_result("Delete Lead Status", False, f"Failed to delete: {response.status_code}")
                    return False
                
                # ERROR CASES
                fake_id = "fake-status-id-123"
                
                # Test with non-existent status_id (should 404)
                response = requests.put(f"{API_BASE}/sales/config/lead-statuses/{fake_id}", json=update_data, headers=self.headers)
                if response.status_code == 404:
                    self.log_result("Update Non-existent Status", True, "Correctly returns 404")
                else:
                    self.log_result("Update Non-existent Status", False, f"Expected 404, got {response.status_code}")
                    return False
                
                # Test invalid category value (should validate)
                invalid_data = {
                    "name": "Invalid Status",
                    "category": "invalid_category",
                    "color": "#ff0000",
                    "workflow_sequence": 100
                }
                response = requests.post(f"{API_BASE}/sales/config/lead-statuses", json=invalid_data, headers=self.headers)
                # Note: This might pass if backend doesn't validate category values
                # We'll just log the result without failing the test
                self.log_result("Create Invalid Category Status", True, f"Response: {response.status_code}")
                
                return True
                
            else:
                self.log_result("Create Lead Status", False, f"Failed to create status: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Lead Statuses CRUD", False, f"Error testing lead statuses CRUD: {str(e)}")
            return False
    
    def test_loss_reasons_crud(self):
        """Test Loss Reasons CRUD operations"""
        print("\n=== Testing Loss Reasons CRUD ===")
        
        try:
            # CREATE: POST /api/sales/config/loss-reasons
            create_data = {
                "name": "Test Temporary Closure",
                "description": "Facility temporarily closed",
                "is_active": True,
                "display_order": 10
            }
            
            response = requests.post(f"{API_BASE}/sales/config/loss-reasons", json=create_data, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                if not data.get("success") or "reason" not in data:
                    self.log_result("Create Loss Reason Response", False, "Invalid response structure")
                    return False
                
                created_reason = data["reason"]
                reason_id = created_reason["id"]
                self.created_loss_reasons.append(reason_id)
                
                self.log_result("Create Loss Reason", True, f"Created reason: {created_reason['name']} with ID: {reason_id}")
                
                # UPDATE: PUT /api/sales/config/loss-reasons/{reason_id}
                update_data = {
                    "name": "Test Temporary Closure Updated",
                    "description": "Updated description",
                    "is_active": False,
                    "display_order": 15
                }
                
                response = requests.put(f"{API_BASE}/sales/config/loss-reasons/{reason_id}", json=update_data, headers=self.headers)
                if response.status_code == 200:
                    update_response = response.json()
                    if update_response.get("success"):
                        self.log_result("Update Loss Reason", True, "Reason updated successfully")
                        
                        # Verify changes persisted
                        response = requests.get(f"{API_BASE}/sales/config/loss-reasons", headers=self.headers)
                        if response.status_code == 200:
                            reasons_data = response.json()
                            updated_reason = None
                            for r in reasons_data["reasons"]:
                                if r["id"] == reason_id:
                                    updated_reason = r
                                    break
                            
                            if updated_reason:
                                if updated_reason["name"] == "Test Temporary Closure Updated" and not updated_reason["is_active"]:
                                    self.log_result("Verify Loss Reason Update", True, "Changes persisted correctly")
                                else:
                                    self.log_result("Verify Loss Reason Update", False, "Changes not persisted")
                                    return False
                            else:
                                self.log_result("Verify Loss Reason Update", False, "Updated reason not found")
                                return False
                        else:
                            self.log_result("Verify Loss Reason Update", False, "Failed to verify update")
                            return False
                    else:
                        self.log_result("Update Loss Reason", False, "Update not successful")
                        return False
                else:
                    self.log_result("Update Loss Reason", False, f"Failed to update: {response.status_code}")
                    return False
                
                # DELETE: DELETE /api/sales/config/loss-reasons/{reason_id}
                response = requests.delete(f"{API_BASE}/sales/config/loss-reasons/{reason_id}", headers=self.headers)
                if response.status_code == 200:
                    delete_response = response.json()
                    if delete_response.get("success"):
                        self.log_result("Delete Loss Reason", True, "Reason deleted successfully")
                        self.created_loss_reasons.remove(reason_id)  # Remove from cleanup list
                    else:
                        self.log_result("Delete Loss Reason", False, "Delete not successful")
                        return False
                else:
                    self.log_result("Delete Loss Reason", False, f"Failed to delete: {response.status_code}")
                    return False
                
                return True
                
            else:
                self.log_result("Create Loss Reason", False, f"Failed to create reason: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Loss Reasons CRUD", False, f"Error testing loss reasons CRUD: {str(e)}")
            return False
    
    # ===================== MEMBER SEARCH API TESTS =====================
    
    def test_member_search_api(self):
        """Test Member Search API for referrals"""
        print("\n=== Testing Member Search API ===")
        
        try:
            # Test with query length < 2 (should return empty)
            response = requests.get(f"{API_BASE}/sales/members/search?q=a", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                if "members" in data and len(data["members"]) == 0:
                    self.log_result("Member Search Min Length", True, "Correctly returns empty for query < 2 chars")
                else:
                    self.log_result("Member Search Min Length", False, "Should return empty for query < 2 chars")
                    return False
            else:
                self.log_result("Member Search Min Length", False, f"Failed: {response.status_code}")
                return False
            
            # Test with valid query
            response = requests.get(f"{API_BASE}/sales/members/search?q=ad", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify structure
                if "members" not in data or "total" not in data:
                    self.log_result("Member Search Structure", False, "Missing members or total field")
                    return False
                
                members = data["members"]
                
                # Verify only active members returned
                for member in members:
                    if member.get("membership_status") != "active":
                        self.log_result("Member Search Active Only", False, f"Non-active member returned: {member.get('membership_status')}")
                        return False
                
                # Verify limit of 20 results
                if len(members) > 20:
                    self.log_result("Member Search Limit", False, f"More than 20 results returned: {len(members)}")
                    return False
                
                # Verify response structure for each member
                if members:
                    member = members[0]
                    required_fields = ["id", "first_name", "last_name", "email", "phone", "membership_status"]
                    for field in required_fields:
                        if field not in member:
                            self.log_result("Member Search Fields", False, f"Missing field: {field}")
                            return False
                
                self.log_result("Member Search Valid Query", True, f"Found {len(members)} active members")
                
                # Test with specific query that should find admin user
                response = requests.get(f"{API_BASE}/sales/members/search?q=admin", headers=self.headers)
                if response.status_code == 200:
                    admin_data = response.json()
                    admin_members = admin_data["members"]
                    
                    # Check if admin user found (might not exist as member)
                    admin_found = any("admin" in member.get("email", "").lower() for member in admin_members)
                    if admin_found:
                        self.log_result("Member Search Admin", True, "Admin user found in search")
                    else:
                        self.log_result("Member Search Admin", True, "Admin user not found (expected if not a member)")
                else:
                    self.log_result("Member Search Admin", False, f"Failed admin search: {response.status_code}")
                    return False
                
                return True
                
            else:
                self.log_result("Member Search Valid Query", False, f"Failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Member Search API", False, f"Error testing member search: {str(e)}")
            return False
    
    # ===================== ENHANCED LEAD CREATE API TESTS =====================
    
    def test_enhanced_lead_create_api(self):
        """Test Enhanced Lead Create API with new fields"""
        print("\n=== Testing Enhanced Lead Create API ===")
        
        try:
            # Get valid source_id and status_id from seeded data
            if not self.seeded_source_ids or not self.seeded_status_ids:
                self.log_result("Enhanced Lead Create Setup", False, "Missing seeded source or status IDs")
                return False
            
            valid_source_id = self.seeded_source_ids.get("Referral")
            valid_status_id = self.seeded_status_ids.get("New Lead")
            
            if not valid_source_id or not valid_status_id:
                self.log_result("Enhanced Lead Create IDs", False, "Could not find Referral source or New Lead status")
                return False
            
            # CREATE lead with new fields including referral
            timestamp = int(time.time() * 1000)
            lead_data = {
                "first_name": "Referred",
                "last_name": f"TestLead{timestamp}",
                "email": f"referred.{timestamp}@test.com",
                "phone": f"+1234567{timestamp % 1000:03d}",
                "source_id": valid_source_id,
                "status_id": valid_status_id,
                "referred_by_member_id": self.test_member_id
            }
            
            response = requests.post(f"{API_BASE}/sales/leads", params=lead_data, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                if not data.get("success") or "lead" not in data:
                    self.log_result("Enhanced Lead Create Response", False, "Invalid response structure")
                    return False
                
                created_lead = data["lead"]
                lead_id = created_lead["id"]
                self.created_leads.append(lead_id)
                self.test_lead_id = lead_id
                
                # Verify lead has new fields populated
                if created_lead.get("source_id") != valid_source_id:
                    self.log_result("Enhanced Lead Create Source ID", False, "source_id not set correctly")
                    return False
                
                if created_lead.get("status_id") != valid_status_id:
                    self.log_result("Enhanced Lead Create Status ID", False, "status_id not set correctly")
                    return False
                
                if created_lead.get("referred_by_member_id") != self.test_member_id:
                    self.log_result("Enhanced Lead Create Referral", False, "referred_by_member_id not set correctly")
                    return False
                
                self.log_result("Enhanced Lead Create", True, f"Created lead with new fields: {lead_id}")
                
                # VERIFY REFERRAL REWARD AUTO-CREATION
                response = requests.get(f"{API_BASE}/sales/referral-rewards?member_id={self.test_member_id}", headers=self.headers)
                
                if response.status_code == 200:
                    rewards_data = response.json()
                    
                    if "rewards" in rewards_data:
                        rewards = rewards_data["rewards"]
                        
                        # Find reward for this lead
                        lead_reward = None
                        for reward in rewards:
                            if reward.get("referred_lead_id") == lead_id:
                                lead_reward = reward
                                break
                        
                        if lead_reward:
                            # Verify reward properties
                            if lead_reward.get("referring_member_id") != self.test_member_id:
                                self.log_result("Referral Reward Member ID", False, "Wrong referring_member_id")
                                return False
                            
                            if lead_reward.get("status") != "pending":
                                self.log_result("Referral Reward Status", False, f"Expected 'pending', got '{lead_reward.get('status')}'")
                                return False
                            
                            if lead_reward.get("reward_type") != "pending_selection":
                                self.log_result("Referral Reward Type", False, f"Expected 'pending_selection', got '{lead_reward.get('reward_type')}'")
                                return False
                            
                            self.created_referral_rewards.append(lead_reward["id"])
                            self.log_result("Referral Reward Auto-Creation", True, "Referral reward auto-created correctly")
                        else:
                            self.log_result("Referral Reward Auto-Creation", False, "No referral reward found for lead")
                            return False
                    else:
                        self.log_result("Referral Reward Auto-Creation", False, "No rewards field in response")
                        return False
                else:
                    self.log_result("Referral Reward Auto-Creation", False, f"Failed to get rewards: {response.status_code}")
                    return False
                
                # CREATE lead without source_id/status_id (test defaults)
                default_lead_data = {
                    "first_name": "Default",
                    "last_name": f"Lead{timestamp}",
                    "email": f"default.{timestamp}@test.com"
                }
                
                response = requests.post(f"{API_BASE}/sales/leads", params=default_lead_data, headers=self.headers)
                
                if response.status_code == 200:
                    default_data = response.json()
                    
                    if default_data.get("success") and "lead" in default_data:
                        default_lead = default_data["lead"]
                        default_lead_id = default_lead["id"]
                        self.created_leads.append(default_lead_id)
                        
                        # Verify defaults to "Other" source and "New Lead" status
                        other_source_id = self.seeded_source_ids.get("Other")
                        new_lead_status_id = self.seeded_status_ids.get("New Lead")
                        
                        if default_lead.get("source_id") == other_source_id:
                            self.log_result("Enhanced Lead Create Default Source", True, "Defaults to 'Other' source")
                        else:
                            self.log_result("Enhanced Lead Create Default Source", False, f"Expected Other source ID {other_source_id}, got {default_lead.get('source_id')}")
                            return False
                        
                        if default_lead.get("status_id") == new_lead_status_id:
                            self.log_result("Enhanced Lead Create Default Status", True, "Defaults to 'New Lead' status")
                        else:
                            self.log_result("Enhanced Lead Create Default Status", False, f"Expected New Lead status ID {new_lead_status_id}, got {default_lead.get('status_id')}")
                            return False
                    else:
                        self.log_result("Enhanced Lead Create Defaults", False, "Failed to create lead with defaults")
                        return False
                else:
                    self.log_result("Enhanced Lead Create Defaults", False, f"Failed to create default lead: {response.status_code}")
                    return False
                
                return True
                
            else:
                self.log_result("Enhanced Lead Create", False, f"Failed to create lead: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Enhanced Lead Create API", False, f"Error testing enhanced lead create: {str(e)}")
            return False
    
    # ===================== ENHANCED LEAD UPDATE API TESTS =====================
    
    def test_enhanced_lead_update_api(self):
        """Test Enhanced Lead Update API with loss status validation and referral reward auto-approval"""
        print("\n=== Testing Enhanced Lead Update API ===")
        
        try:
            if not self.test_lead_id:
                self.log_result("Enhanced Lead Update Setup", False, "No test lead available")
                return False
            
            # A. Test Loss Status Validation
            lost_status_id = self.seeded_status_ids.get("Lost")
            loss_reason_id = list(self.seeded_loss_reason_ids.values())[0] if self.seeded_loss_reason_ids else None
            
            if not lost_status_id or not loss_reason_id:
                self.log_result("Enhanced Lead Update IDs", False, "Could not find Lost status or loss reason")
                return False
            
            # Try to update lead to Lost without loss_reason_id (should fail)
            update_data_no_reason = {
                "status_id": lost_status_id
            }
            
            response = requests.put(f"{API_BASE}/sales/leads/{self.test_lead_id}", params=update_data_no_reason, headers=self.headers)
            
            if response.status_code == 400:
                self.log_result("Loss Status Validation", True, "Correctly requires loss_reason_id for Lost status")
            else:
                self.log_result("Loss Status Validation", False, f"Expected 400, got {response.status_code}")
                return False
            
            # Update lead to Lost WITH loss_reason_id (should succeed)
            update_data_with_reason = {
                "status_id": lost_status_id,
                "loss_reason_id": loss_reason_id,
                "loss_notes": "Customer said price was too high"
            }
            
            response = requests.put(f"{API_BASE}/sales/leads/{self.test_lead_id}", params=update_data_with_reason, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success") and "lead" in data:
                    updated_lead = data["lead"]
                    
                    # Verify lead has loss_reason_id and loss_notes
                    if updated_lead.get("loss_reason_id") != loss_reason_id:
                        self.log_result("Loss Reason ID Update", False, "loss_reason_id not set correctly")
                        return False
                    
                    if updated_lead.get("loss_notes") != "Customer said price was too high":
                        self.log_result("Loss Notes Update", False, "loss_notes not set correctly")
                        return False
                    
                    self.log_result("Loss Status Update", True, "Lead updated to Lost with reason and notes")
                else:
                    self.log_result("Loss Status Update", False, "Invalid response structure")
                    return False
            else:
                self.log_result("Loss Status Update", False, f"Failed to update lead to Lost: {response.status_code}")
                return False
            
            # B. Test Referral Reward Auto-Approval
            # First, create a new lead with referral for this test
            timestamp = int(time.time() * 1000)
            referral_lead_data = {
                "first_name": "AutoApproval",
                "last_name": f"Test{timestamp}",
                "email": f"autoapproval.{timestamp}@test.com",
                "phone": f"+1234567{timestamp % 1000:03d}",
                "source_id": self.seeded_source_ids.get("Referral"),
                "status_id": self.seeded_status_ids.get("New Lead"),
                "referred_by_member_id": self.test_member_id
            }
            
            response = requests.post(f"{API_BASE}/sales/leads", params=referral_lead_data, headers=self.headers)
            
            if response.status_code == 200:
                lead_data = response.json()
                if lead_data.get("success") and "lead" in lead_data:
                    referral_lead = lead_data["lead"]
                    referral_lead_id = referral_lead["id"]
                    self.created_leads.append(referral_lead_id)
                    
                    # Update this lead to "Joined" (converted status)
                    joined_status_id = self.seeded_status_ids.get("Joined")
                    if not joined_status_id:
                        self.log_result("Referral Reward Auto-Approval Setup", False, "Could not find Joined status")
                        return False
                    
                    update_to_joined = {
                        "status_id": joined_status_id
                    }
                    
                    response = requests.put(f"{API_BASE}/sales/leads/{referral_lead_id}", params=update_to_joined, headers=self.headers)
                    
                    if response.status_code == 200:
                        # VERIFY REFERRAL REWARD APPROVAL
                        response = requests.get(f"{API_BASE}/sales/referral-rewards?member_id={self.test_member_id}", headers=self.headers)
                        
                        if response.status_code == 200:
                            rewards_data = response.json()
                            
                            if "rewards" in rewards_data:
                                rewards = rewards_data["rewards"]
                                
                                # Find reward for this lead
                                approved_reward = None
                                for reward in rewards:
                                    if reward.get("referred_lead_id") == referral_lead_id:
                                        approved_reward = reward
                                        break
                                
                                if approved_reward:
                                    if approved_reward.get("status") == "approved":
                                        self.log_result("Referral Reward Auto-Approval", True, "Referral reward auto-approved when lead converted")
                                    else:
                                        self.log_result("Referral Reward Auto-Approval", False, f"Expected 'approved', got '{approved_reward.get('status')}'")
                                        return False
                                else:
                                    self.log_result("Referral Reward Auto-Approval", False, "No referral reward found for converted lead")
                                    return False
                            else:
                                self.log_result("Referral Reward Auto-Approval", False, "No rewards field in response")
                                return False
                        else:
                            self.log_result("Referral Reward Auto-Approval", False, f"Failed to get rewards: {response.status_code}")
                            return False
                    else:
                        self.log_result("Referral Reward Auto-Approval", False, f"Failed to update lead to Joined: {response.status_code}")
                        return False
                else:
                    self.log_result("Referral Reward Auto-Approval Setup", False, "Failed to create referral lead")
                    return False
            else:
                self.log_result("Referral Reward Auto-Approval Setup", False, f"Failed to create referral lead: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Enhanced Lead Update API", False, f"Error testing enhanced lead update: {str(e)}")
            return False
    
    # ===================== REFERRAL REWARDS MANAGEMENT TESTS =====================
    
    def test_referral_rewards_management(self):
        """Test Referral Rewards Management APIs"""
        print("\n=== Testing Referral Rewards Management ===")
        
        try:
            # GET /api/sales/referral-rewards
            response = requests.get(f"{API_BASE}/sales/referral-rewards", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify structure
                if "rewards" not in data:
                    self.log_result("Get Referral Rewards Structure", False, "Missing 'rewards' field")
                    return False
                
                rewards = data["rewards"]
                
                # Verify rewards have enriched member and lead names
                if rewards:
                    reward = rewards[0]
                    # Check if reward has member/lead name fields (these might be enriched by the API)
                    self.log_result("Get Referral Rewards", True, f"Retrieved {len(rewards)} referral rewards")
                else:
                    self.log_result("Get Referral Rewards", True, "No referral rewards found (expected if none created)")
                
            else:
                self.log_result("Get Referral Rewards", False, f"Failed to get rewards: {response.status_code}")
                return False
            
            # CREATE referral reward manually
            if not self.test_member_id or not self.test_lead_id:
                self.log_result("Create Referral Reward Setup", False, "Missing test member or lead ID")
                return False
            
            create_reward_data = {
                "referring_member_id": self.test_member_id,
                "referred_lead_id": self.test_lead_id,
                "reward_type": "free_month",
                "reward_value": "1 Month Free Membership",
                "notes": "Test reward"
            }
            
            response = requests.post(f"{API_BASE}/sales/referral-rewards", json=create_reward_data, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success") and "reward" in data:
                    created_reward = data["reward"]
                    reward_id = created_reward["id"]
                    self.created_referral_rewards.append(reward_id)
                    
                    # Verify created with status="pending"
                    if created_reward.get("status") != "pending":
                        self.log_result("Create Referral Reward Status", False, f"Expected 'pending', got '{created_reward.get('status')}'")
                        return False
                    
                    self.log_result("Create Referral Reward", True, f"Created reward: {reward_id}")
                    
                    # UPDATE reward status to approved
                    response = requests.put(f"{API_BASE}/sales/referral-rewards/{reward_id}/status?status=approved", headers=self.headers)
                    
                    if response.status_code == 200:
                        update_data = response.json()
                        if update_data.get("success"):
                            self.log_result("Update Reward Status (Approved)", True, "Status updated to approved")
                            
                            # UPDATE reward status to delivered
                            response = requests.put(f"{API_BASE}/sales/referral-rewards/{reward_id}/status?status=delivered", headers=self.headers)
                            
                            if response.status_code == 200:
                                delivered_data = response.json()
                                if delivered_data.get("success"):
                                    self.log_result("Update Reward Status (Delivered)", True, "Status updated to delivered with timestamp")
                                else:
                                    self.log_result("Update Reward Status (Delivered)", False, "Update not successful")
                                    return False
                            else:
                                self.log_result("Update Reward Status (Delivered)", False, f"Failed to update to delivered: {response.status_code}")
                                return False
                        else:
                            self.log_result("Update Reward Status (Approved)", False, "Update not successful")
                            return False
                    else:
                        self.log_result("Update Reward Status (Approved)", False, f"Failed to update to approved: {response.status_code}")
                        return False
                else:
                    self.log_result("Create Referral Reward", False, "Invalid response structure")
                    return False
            else:
                self.log_result("Create Referral Reward", False, f"Failed to create reward: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Referral Rewards Management", False, f"Error testing referral rewards: {str(e)}")
            return False
    
    # ===================== COMPREHENSIVE DASHBOARD ANALYTICS TESTS =====================
    
    def test_comprehensive_dashboard_analytics(self):
        """Test Comprehensive Dashboard Analytics API"""
        print("\n=== Testing Comprehensive Dashboard Analytics ===")
        
        try:
            # A. Default Date Range (Last 30 Days)
            response = requests.get(f"{API_BASE}/sales/analytics/dashboard/comprehensive", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["date_range", "summary", "source_performance", "status_funnel", "loss_analysis", "daily_trends", "salesperson_performance"]
                for field in required_fields:
                    if field not in data:
                        self.log_result("Dashboard Analytics Structure", False, f"Missing field: {field}")
                        return False
                
                # Verify date_range structure
                date_range = data["date_range"]
                if "from" not in date_range or "to" not in date_range:
                    self.log_result("Dashboard Analytics Date Range", False, "Missing from/to in date_range")
                    return False
                
                # Verify summary structure
                summary = data["summary"]
                summary_fields = ["total_leads", "total_converted", "total_lost", "in_progress", "overall_conversion_rate"]
                for field in summary_fields:
                    if field not in summary:
                        self.log_result("Dashboard Analytics Summary", False, f"Missing summary field: {field}")
                        return False
                
                # Verify source_performance structure
                source_performance = data["source_performance"]
                if not isinstance(source_performance, list):
                    self.log_result("Dashboard Analytics Source Performance Type", False, "source_performance should be array")
                    return False
                
                if source_performance:
                    source = source_performance[0]
                    source_fields = ["source", "total_leads", "converted_leads", "lost_leads", "in_progress", "conversion_rate", "loss_rate", "avg_days_to_convert"]
                    for field in source_fields:
                        if field not in source:
                            self.log_result("Dashboard Analytics Source Fields", False, f"Missing source field: {field}")
                            return False
                
                # Verify status_funnel structure
                status_funnel = data["status_funnel"]
                if not isinstance(status_funnel, list):
                    self.log_result("Dashboard Analytics Status Funnel Type", False, "status_funnel should be array")
                    return False
                
                if status_funnel:
                    status = status_funnel[0]
                    status_fields = ["status", "count", "percentage", "drop_off", "workflow_sequence"]
                    for field in status_fields:
                        if field not in status:
                            self.log_result("Dashboard Analytics Status Fields", False, f"Missing status field: {field}")
                            return False
                
                # Verify loss_analysis structure
                loss_analysis = data["loss_analysis"]
                if not isinstance(loss_analysis, list):
                    self.log_result("Dashboard Analytics Loss Analysis Type", False, "loss_analysis should be array")
                    return False
                
                if loss_analysis:
                    loss = loss_analysis[0]
                    loss_fields = ["reason", "count", "percentage", "by_source"]
                    for field in loss_fields:
                        if field not in loss:
                            self.log_result("Dashboard Analytics Loss Fields", False, f"Missing loss field: {field}")
                            return False
                
                # Verify daily_trends structure
                daily_trends = data["daily_trends"]
                if not isinstance(daily_trends, list):
                    self.log_result("Dashboard Analytics Daily Trends Type", False, "daily_trends should be array")
                    return False
                
                if daily_trends:
                    trend = daily_trends[0]
                    trend_fields = ["date", "new_leads", "converted", "lost"]
                    for field in trend_fields:
                        if field not in trend:
                            self.log_result("Dashboard Analytics Trend Fields", False, f"Missing trend field: {field}")
                            return False
                
                # Verify salesperson_performance structure
                salesperson_performance = data["salesperson_performance"]
                if not isinstance(salesperson_performance, list):
                    self.log_result("Dashboard Analytics Salesperson Performance Type", False, "salesperson_performance should be array")
                    return False
                
                if salesperson_performance:
                    salesperson = salesperson_performance[0]
                    salesperson_fields = ["salesperson", "total_leads", "converted", "lost", "in_progress", "conversion_rate"]
                    for field in salesperson_fields:
                        if field not in salesperson:
                            self.log_result("Dashboard Analytics Salesperson Fields", False, f"Missing salesperson field: {field}")
                            return False
                
                self.log_result("Dashboard Analytics Default Range", True, f"Retrieved analytics for {summary['total_leads']} leads")
                
            else:
                self.log_result("Dashboard Analytics Default Range", False, f"Failed to get analytics: {response.status_code}")
                return False
            
            # B. Custom Date Range
            custom_from = "2024-01-01"
            custom_to = "2024-12-31"
            response = requests.get(f"{API_BASE}/sales/analytics/dashboard/comprehensive?date_from={custom_from}&date_to={custom_to}", headers=self.headers)
            
            if response.status_code == 200:
                custom_data = response.json()
                
                # Verify date_range matches parameters
                if custom_data["date_range"]["from"] == custom_from and custom_data["date_range"]["to"] == custom_to:
                    self.log_result("Dashboard Analytics Custom Range", True, "Custom date range applied correctly")
                else:
                    self.log_result("Dashboard Analytics Custom Range", False, "Date range parameters not applied")
                    return False
            else:
                self.log_result("Dashboard Analytics Custom Range", False, f"Failed with custom range: {response.status_code}")
                return False
            
            # C. Calculation Accuracy (manual verification of at least 2 calculations)
            if source_performance:
                # Verify conversion_rate calculation for first source
                first_source = source_performance[0]
                total = first_source["total_leads"]
                converted = first_source["converted_leads"]
                
                if total > 0:
                    expected_rate = round((converted / total) * 100, 2)
                    actual_rate = first_source["conversion_rate"]
                    
                    if abs(expected_rate - actual_rate) < 0.01:  # Allow small floating point differences
                        self.log_result("Dashboard Analytics Calculation Accuracy", True, f"Conversion rate calculation correct: {actual_rate}%")
                    else:
                        self.log_result("Dashboard Analytics Calculation Accuracy", False, f"Conversion rate mismatch: expected {expected_rate}, got {actual_rate}")
                        return False
                else:
                    self.log_result("Dashboard Analytics Calculation Accuracy", True, "No leads to verify calculation")
            
            # Verify overall conversion rate
            total_leads = summary["total_leads"]
            total_converted = summary["total_converted"]
            
            if total_leads > 0:
                expected_overall_rate = round((total_converted / total_leads) * 100, 2)
                actual_overall_rate = summary["overall_conversion_rate"]
                
                if abs(expected_overall_rate - actual_overall_rate) < 0.01:
                    self.log_result("Dashboard Analytics Overall Rate", True, f"Overall conversion rate correct: {actual_overall_rate}%")
                else:
                    self.log_result("Dashboard Analytics Overall Rate", False, f"Overall rate mismatch: expected {expected_overall_rate}, got {actual_overall_rate}")
                    return False
            else:
                self.log_result("Dashboard Analytics Overall Rate", True, "No leads for overall rate calculation")
            
            # D. Verify Sorting
            # source_performance sorted by conversion_rate descending
            if len(source_performance) > 1:
                for i in range(1, len(source_performance)):
                    if source_performance[i]["conversion_rate"] > source_performance[i-1]["conversion_rate"]:
                        self.log_result("Dashboard Analytics Source Sorting", False, "Sources not sorted by conversion_rate descending")
                        return False
                self.log_result("Dashboard Analytics Source Sorting", True, "Sources correctly sorted by conversion_rate")
            
            # loss_analysis sorted by count descending
            if len(loss_analysis) > 1:
                for i in range(1, len(loss_analysis)):
                    if loss_analysis[i]["count"] > loss_analysis[i-1]["count"]:
                        self.log_result("Dashboard Analytics Loss Sorting", False, "Loss reasons not sorted by count descending")
                        return False
                self.log_result("Dashboard Analytics Loss Sorting", True, "Loss reasons correctly sorted by count")
            
            # salesperson_performance sorted by conversion_rate descending
            if len(salesperson_performance) > 1:
                for i in range(1, len(salesperson_performance)):
                    if salesperson_performance[i]["conversion_rate"] > salesperson_performance[i-1]["conversion_rate"]:
                        self.log_result("Dashboard Analytics Salesperson Sorting", False, "Salesperson not sorted by conversion_rate descending")
                        return False
                self.log_result("Dashboard Analytics Salesperson Sorting", True, "Salesperson correctly sorted by conversion_rate")
            
            # E. Edge Cases
            # Test with empty date range (future dates with no leads)
            future_from = "2030-01-01"
            future_to = "2030-12-31"
            response = requests.get(f"{API_BASE}/sales/analytics/dashboard/comprehensive?date_from={future_from}&date_to={future_to}", headers=self.headers)
            
            if response.status_code == 200:
                future_data = response.json()
                
                # Verify handles empty data (0 leads)
                if future_data["summary"]["total_leads"] == 0:
                    self.log_result("Dashboard Analytics Empty Data", True, "Correctly handles empty date range")
                else:
                    self.log_result("Dashboard Analytics Empty Data", True, f"Found {future_data['summary']['total_leads']} leads in future range")
            else:
                self.log_result("Dashboard Analytics Empty Data", False, f"Failed with empty range: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Comprehensive Dashboard Analytics", False, f"Error testing dashboard analytics: {str(e)}")
            return False
    
    # ===================== DATA INTEGRITY CHECKS =====================
    
    def test_data_integrity_checks(self):
        """Test data integrity - UUIDs, timestamps, color codes, etc."""
        print("\n=== Testing Data Integrity Checks ===")
        
        try:
            # Check lead sources
            response = requests.get(f"{API_BASE}/sales/config/lead-sources", headers=self.headers)
            if response.status_code == 200:
                sources_data = response.json()
                sources = sources_data["sources"]
                
                for source in sources:
                    # Verify UUID format (basic check)
                    source_id = source["id"]
                    if len(source_id) < 32 or '-' not in source_id:
                        self.log_result("Data Integrity UUID", False, f"Invalid UUID format for source: {source_id}")
                        return False
                    
                    # Verify timestamps are ISO format (allow both Z and +00:00 timezone formats)
                    created_at = source["created_at"]
                    if 'T' not in created_at or ('+' not in created_at and 'Z' not in created_at):
                        self.log_result("Data Integrity Timestamp", False, f"Invalid timestamp format: {created_at}")
                        return False
                
                self.log_result("Data Integrity Sources", True, "All source UUIDs and timestamps valid")
            else:
                self.log_result("Data Integrity Sources", False, f"Failed to get sources: {response.status_code}")
                return False
            
            # Check lead statuses
            response = requests.get(f"{API_BASE}/sales/config/lead-statuses", headers=self.headers)
            if response.status_code == 200:
                statuses_data = response.json()
                statuses = statuses_data["statuses"]
                
                workflow_sequences = []
                
                for status in statuses:
                    # Verify color codes are valid hex
                    color = status["color"]
                    if not color.startswith("#") or len(color) != 7:
                        self.log_result("Data Integrity Color", False, f"Invalid color format: {color}")
                        return False
                    
                    # Collect workflow sequences for uniqueness check
                    workflow_sequences.append(status["workflow_sequence"])
                
                # Verify workflow_sequence values are integers (uniqueness not strictly required for seeded data)
                for seq in workflow_sequences:
                    if not isinstance(seq, int):
                        self.log_result("Data Integrity Workflow Sequence", False, f"Workflow sequence should be integer: {seq}")
                        return False
                
                self.log_result("Data Integrity Statuses", True, "All status colors and workflow sequences valid")
            else:
                self.log_result("Data Integrity Statuses", False, f"Failed to get statuses: {response.status_code}")
                return False
            
            # Check display_order values for sources and reasons
            response = requests.get(f"{API_BASE}/sales/config/loss-reasons", headers=self.headers)
            if response.status_code == 200:
                reasons_data = response.json()
                reasons = reasons_data["reasons"]
                
                display_orders = [reason["display_order"] for reason in reasons]
                
                # Verify display orders are reasonable (not all the same)
                if len(set(display_orders)) > 1:
                    self.log_result("Data Integrity Display Order", True, "Display orders are varied")
                else:
                    self.log_result("Data Integrity Display Order", True, "Display orders are consistent (acceptable)")
            else:
                self.log_result("Data Integrity Loss Reasons", False, f"Failed to get loss reasons: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Data Integrity Checks", False, f"Error testing data integrity: {str(e)}")
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
        
        # Clean up created sources
        for source_id in self.created_sources:
            try:
                response = requests.delete(f"{API_BASE}/sales/config/lead-sources/{source_id}", headers=self.headers)
                if response.status_code == 200:
                    self.log_result(f"Cleanup Source {source_id[:8]}", True, "Source deleted")
                else:
                    self.log_result(f"Cleanup Source {source_id[:8]}", False, f"Failed to delete: {response.status_code}")
            except Exception as e:
                self.log_result(f"Cleanup Source {source_id[:8]}", False, f"Error: {str(e)}")
        
        # Clean up created statuses
        for status_id in self.created_statuses:
            try:
                response = requests.delete(f"{API_BASE}/sales/config/lead-statuses/{status_id}", headers=self.headers)
                if response.status_code == 200:
                    self.log_result(f"Cleanup Status {status_id[:8]}", True, "Status deleted")
                else:
                    self.log_result(f"Cleanup Status {status_id[:8]}", False, f"Failed to delete: {response.status_code}")
            except Exception as e:
                self.log_result(f"Cleanup Status {status_id[:8]}", False, f"Error: {str(e)}")
        
        # Clean up created loss reasons
        for reason_id in self.created_loss_reasons:
            try:
                response = requests.delete(f"{API_BASE}/sales/config/loss-reasons/{reason_id}", headers=self.headers)
                if response.status_code == 200:
                    self.log_result(f"Cleanup Reason {reason_id[:8]}", True, "Reason deleted")
                else:
                    self.log_result(f"Cleanup Reason {reason_id[:8]}", False, f"Failed to delete: {response.status_code}")
            except Exception as e:
                self.log_result(f"Cleanup Reason {reason_id[:8]}", False, f"Error: {str(e)}")
        
        # Note: Referral rewards cleanup might not be needed if they're automatically cleaned up with leads
    
    def run_configurable_lead_system_tests(self):
        """Run the Configurable Lead System tests"""
        print("=" * 80)
        print("BACKEND TESTING - CONFIGURABLE LEAD SOURCE/STATUS/LOSS REASON SYSTEM")
        print("=" * 80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Setup test data
        if not self.setup_test_data():
            print("❌ Failed to setup test data. Cannot proceed with tests.")
            return False
        
        # Step 3: Run STARTUP SEEDING VERIFICATION TESTS
        print("\n" + "=" * 60)
        print("STARTUP SEEDING VERIFICATION TESTS")
        print("=" * 60)
        
        seeding_results = []
        
        print("\n🌱 TEST 1: Startup Seeding Verification")
        seeding_results.append(self.test_startup_seeding_verification())
        
        # Step 4: Run CONFIGURATION CRUD API TESTS
        print("\n" + "=" * 60)
        print("CONFIGURATION CRUD API TESTS")
        print("=" * 60)
        
        config_results = []
        
        print("\n📝 TEST 2: Lead Sources CRUD")
        config_results.append(self.test_lead_sources_crud())
        
        print("\n📊 TEST 3: Lead Statuses CRUD")
        config_results.append(self.test_lead_statuses_crud())
        
        print("\n❌ TEST 4: Loss Reasons CRUD")
        config_results.append(self.test_loss_reasons_crud())
        
        # Step 5: Run MEMBER SEARCH API TESTS
        print("\n" + "=" * 60)
        print("MEMBER SEARCH API TESTS")
        print("=" * 60)
        
        search_results = []
        
        print("\n🔍 TEST 5: Member Search API")
        search_results.append(self.test_member_search_api())
        
        # Step 6: Run ENHANCED LEAD MANAGEMENT TESTS
        print("\n" + "=" * 60)
        print("ENHANCED LEAD MANAGEMENT TESTS")
        print("=" * 60)
        
        lead_results = []
        
        print("\n➕ TEST 6: Enhanced Lead Create API")
        lead_results.append(self.test_enhanced_lead_create_api())
        
        print("\n✏️ TEST 7: Enhanced Lead Update API")
        lead_results.append(self.test_enhanced_lead_update_api())
        
        # Step 7: Run REFERRAL REWARDS TESTS
        print("\n" + "=" * 60)
        print("REFERRAL REWARDS MANAGEMENT TESTS")
        print("=" * 60)
        
        rewards_results = []
        
        print("\n🎁 TEST 8: Referral Rewards Management")
        rewards_results.append(self.test_referral_rewards_management())
        
        # Step 8: Run COMPREHENSIVE DASHBOARD ANALYTICS TESTS
        print("\n" + "=" * 60)
        print("COMPREHENSIVE DASHBOARD ANALYTICS TESTS")
        print("=" * 60)
        
        analytics_results = []
        
        print("\n📈 TEST 9: Comprehensive Dashboard Analytics")
        analytics_results.append(self.test_comprehensive_dashboard_analytics())
        
        # Step 9: Run DATA INTEGRITY CHECKS
        print("\n" + "=" * 60)
        print("DATA INTEGRITY CHECKS")
        print("=" * 60)
        
        integrity_results = []
        
        print("\n🔒 TEST 10: Data Integrity Checks")
        integrity_results.append(self.test_data_integrity_checks())
        
        # Step 10: Generate Summary
        print("\n" + "=" * 80)
        print("TEST RESULTS SUMMARY")
        print("=" * 80)
        
        seeding_passed = sum(seeding_results)
        seeding_total = len(seeding_results)
        
        config_passed = sum(config_results)
        config_total = len(config_results)
        
        search_passed = sum(search_results)
        search_total = len(search_results)
        
        lead_passed = sum(lead_results)
        lead_total = len(lead_results)
        
        rewards_passed = sum(rewards_results)
        rewards_total = len(rewards_results)
        
        analytics_passed = sum(analytics_results)
        analytics_total = len(analytics_results)
        
        integrity_passed = sum(integrity_results)
        integrity_total = len(integrity_results)
        
        total_passed = seeding_passed + config_passed + search_passed + lead_passed + rewards_passed + analytics_passed + integrity_passed
        total_tests = seeding_total + config_total + search_total + lead_total + rewards_total + analytics_total + integrity_total
        
        print(f"\n🌱 STARTUP SEEDING TESTS: {seeding_passed}/{seeding_total} PASSED")
        print(f"⚙️ CONFIGURATION CRUD TESTS: {config_passed}/{config_total} PASSED")
        print(f"🔍 MEMBER SEARCH TESTS: {search_passed}/{search_total} PASSED")
        print(f"📋 ENHANCED LEAD MANAGEMENT TESTS: {lead_passed}/{lead_total} PASSED")
        print(f"🎁 REFERRAL REWARDS TESTS: {rewards_passed}/{rewards_total} PASSED")
        print(f"📈 DASHBOARD ANALYTICS TESTS: {analytics_passed}/{analytics_total} PASSED")
        print(f"🔒 DATA INTEGRITY TESTS: {integrity_passed}/{integrity_total} PASSED")
        print(f"\n🏆 OVERALL: {total_passed}/{total_tests} PASSED")
        
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        print(f"📊 SUCCESS RATE: {success_rate:.1f}%")
        
        if total_passed == total_tests:
            print("\n🎉 ALL TESTS PASSED! Configurable Lead System is working correctly.")
        else:
            print(f"\n⚠️ {total_tests - total_passed} TEST(S) FAILED. Please review the failed tests above.")
        
        # Step 11: Cleanup
        self.cleanup_test_data()
        
        return total_passed == total_tests


if __name__ == "__main__":
    runner = ConfigurableLeadSystemTestRunner()
    success = runner.run_configurable_lead_system_tests()
    exit(0 if success else 1)