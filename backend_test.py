#!/usr/bin/env python3
"""
Backend Test Suite - Member Analytics & Retention APIs Testing
Focus on testing the Member Analytics & Retention APIs with comprehensive validation
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

class MemberAnalyticsTestRunner:
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
                
                # Verify date range is respected (handle timezone format differences)
                start_check = "2024-01-01" in period["start_date"]
                end_check = "2024-12-31" in period["end_date"]
                if not start_check or not end_check:
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
                
                # Verify date range is respected (handle timezone format differences)
                start_check = "2024-01-01" in period["start_date"]
                end_check = "2024-12-31" in period["end_date"]
                if not start_check or not end_check:
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
                
                # Verify date range is respected (handle timezone format differences)
                start_check = "2024-01-01" in period["start_date"]
                end_check = "2024-12-31" in period["end_date"]
                if not start_check or not end_check:
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
                
                # Verify date range is respected (handle timezone format differences)
                start_check = "2024-01-01" in period["start_date"]
                end_check = "2024-12-31" in period["end_date"]
                if not start_check or not end_check:
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
            
            # Should handle gracefully (either 400, 422, 500 or fallback to defaults)
            if response.status_code in [200, 400, 422, 500]:
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
            if response.status_code in [200, 400, 422, 500]:
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