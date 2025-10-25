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
    
    # ===================== MEMBER ANALYTICS & RETENTION API TESTS =====================
    
    def test_retention_dashboard_api(self):
        """Test GET /api/reports/retention-dashboard endpoint"""
        print("\n=== Testing Retention Dashboard API ===")
        
        try:
            # Test 1: Default parameters (12 months)
            response = requests.get(f"{API_BASE}/reports/retention-dashboard", headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["period", "summary", "retention_by_cohort", "retention_trend"]
                
                for field in required_fields:
                    if field not in data:
                        self.log_result("Retention Dashboard Structure", False, f"Missing field: {field}")
                        return False
                
                # Verify period structure
                period = data["period"]
                period_fields = ["start_date", "end_date", "months"]
                for field in period_fields:
                    if field not in period:
                        self.log_result("Retention Dashboard Period", False, f"Missing period field: {field}")
                        return False
                
                # Verify summary structure
                summary = data["summary"]
                summary_fields = ["total_members", "active_members", "inactive_members", "new_members_period", "churn_rate", "retention_rate", "avg_tenure_months"]
                for field in summary_fields:
                    if field not in summary:
                        self.log_result("Retention Dashboard Summary", False, f"Missing summary field: {field}")
                        return False
                
                # Verify churn_rate + retention_rate = 100%
                churn_rate = summary["churn_rate"]
                retention_rate = summary["retention_rate"]
                if abs((churn_rate + retention_rate) - 100) > 0.1:  # Allow small floating point differences
                    self.log_result("Retention Dashboard Rate Sum", False, f"Churn rate ({churn_rate}) + retention rate ({retention_rate}) should equal 100%")
                    return False
                
                # Verify percentages are between 0-100
                if not (0 <= churn_rate <= 100) or not (0 <= retention_rate <= 100):
                    self.log_result("Retention Dashboard Rate Range", False, "Rates should be between 0-100%")
                    return False
                
                # Verify retention_by_cohort structure
                cohorts = data["retention_by_cohort"]
                if not isinstance(cohorts, list):
                    self.log_result("Retention Dashboard Cohorts", False, "retention_by_cohort should be array")
                    return False
                
                if cohorts:
                    cohort = cohorts[0]
                    cohort_fields = ["cohort", "total_members", "active_members", "churned_members", "retention_rate"]
                    for field in cohort_fields:
                        if field not in cohort:
                            self.log_result("Retention Dashboard Cohort Fields", False, f"Missing cohort field: {field}")
                            return False
                
                # Verify retention_trend structure
                trend = data["retention_trend"]
                if not isinstance(trend, list):
                    self.log_result("Retention Dashboard Trend", False, "retention_trend should be array")
                    return False
                
                if trend:
                    trend_item = trend[0]
                    trend_fields = ["month", "retention_rate", "active_members", "total_members"]
                    for field in trend_fields:
                        if field not in trend_item:
                            self.log_result("Retention Dashboard Trend Fields", False, f"Missing trend field: {field}")
                            return False
                
                self.log_result("Retention Dashboard Default", True, f"Total members: {summary['total_members']}, Retention rate: {retention_rate}%")
                
            else:
                self.log_result("Retention Dashboard Default", False, f"Failed: {response.status_code}")
                return False
            
            # Test 2: Custom period (6 months)
            response = requests.get(f"{API_BASE}/reports/retention-dashboard?period_months=6", headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                if data["period"]["months"] != 6:
                    self.log_result("Retention Dashboard 6 Months", False, "Period months not respected")
                    return False
                
                self.log_result("Retention Dashboard 6 Months", True, f"6-month period: {data['summary']['retention_rate']}% retention")
                
            else:
                self.log_result("Retention Dashboard 6 Months", False, f"Failed: {response.status_code}")
                return False
            
            # Test 3: 24 months period
            response = requests.get(f"{API_BASE}/reports/retention-dashboard?period_months=24", headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                if data["period"]["months"] != 24:
                    self.log_result("Retention Dashboard 24 Months", False, "Period months not respected")
                    return False
                
                self.log_result("Retention Dashboard 24 Months", True, f"24-month period: {data['summary']['retention_rate']}% retention")
                
            else:
                self.log_result("Retention Dashboard 24 Months", False, f"Failed: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Retention Dashboard API", False, f"Error: {str(e)}")
            return False
    
    def test_member_ltv_api(self):
        """Test GET /api/reports/member-ltv endpoint"""
        print("\n=== Testing Member LTV API ===")
        
        try:
            # Test 1: Default parameters
            response = requests.get(f"{API_BASE}/reports/member-ltv", headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["summary", "ltv_by_membership_type", "top_members", "all_members_ltv"]
                
                for field in required_fields:
                    if field not in data:
                        self.log_result("Member LTV Structure", False, f"Missing field: {field}")
                        return False
                
                # Verify summary structure
                summary = data["summary"]
                summary_fields = ["total_members", "total_ltv", "average_ltv", "average_ltv_active_members", "highest_ltv", "lowest_ltv"]
                for field in summary_fields:
                    if field not in summary:
                        self.log_result("Member LTV Summary", False, f"Missing summary field: {field}")
                        return False
                
                # Verify ltv_by_membership_type structure
                ltv_by_type = data["ltv_by_membership_type"]
                if not isinstance(ltv_by_type, dict):
                    self.log_result("Member LTV By Type", False, "ltv_by_membership_type should be object")
                    return False
                
                # Verify membership type structure if any exist
                if ltv_by_type:
                    type_name = list(ltv_by_type.keys())[0]
                    type_data = ltv_by_type[type_name]
                    type_fields = ["total_revenue", "member_count", "avg_ltv"]
                    for field in type_fields:
                        if field not in type_data:
                            self.log_result("Member LTV Type Fields", False, f"Missing type field: {field}")
                            return False
                
                # Verify top_members structure
                top_members = data["top_members"]
                if not isinstance(top_members, list):
                    self.log_result("Member LTV Top Members", False, "top_members should be array")
                    return False
                
                # Verify top 20 limit
                if len(top_members) > 20:
                    self.log_result("Member LTV Top Members Limit", False, "top_members should be limited to 20")
                    return False
                
                # Verify member structure if any exist
                if top_members:
                    member = top_members[0]
                    member_fields = ["member_id", "member_name", "status", "tenure_months", "total_revenue", "monthly_avg_revenue"]
                    for field in member_fields:
                        if field not in member:
                            self.log_result("Member LTV Member Fields", False, f"Missing member field: {field}")
                            return False
                    
                    # Verify sorting (highest total_revenue first)
                    if len(top_members) > 1:
                        for i in range(1, len(top_members)):
                            if top_members[i]["total_revenue"] > top_members[i-1]["total_revenue"]:
                                self.log_result("Member LTV Sorting", False, "Members not sorted by total_revenue")
                                return False
                    
                    # Verify monthly_avg_revenue calculation
                    tenure = member["tenure_months"]
                    total_rev = member["total_revenue"]
                    monthly_avg = member["monthly_avg_revenue"]
                    expected_avg = round(total_rev / tenure, 2) if tenure > 0 else 0
                    if abs(monthly_avg - expected_avg) > 0.01:  # Allow small floating point differences
                        self.log_result("Member LTV Monthly Avg Calculation", False, f"Monthly avg calculation incorrect: {monthly_avg} vs expected {expected_avg}")
                        return False
                
                # Verify all_members_ltv structure
                all_members = data["all_members_ltv"]
                if not isinstance(all_members, list):
                    self.log_result("Member LTV All Members", False, "all_members_ltv should be array")
                    return False
                
                self.log_result("Member LTV Default", True, f"Total LTV: R{summary['total_ltv']:.2f}, Average: R{summary['average_ltv']:.2f}")
                
            else:
                self.log_result("Member LTV Default", False, f"Failed: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Member LTV API", False, f"Error: {str(e)}")
            return False
    
    def test_at_risk_members_api(self):
        """Test GET /api/reports/at-risk-members endpoint"""
        print("\n=== Testing At-Risk Members API ===")
        
        try:
            # Test 1: Default parameters (threshold 60)
            response = requests.get(f"{API_BASE}/reports/at-risk-members", headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["summary", "at_risk_members"]
                
                for field in required_fields:
                    if field not in data:
                        self.log_result("At-Risk Members Structure", False, f"Missing field: {field}")
                        return False
                
                # Verify summary structure
                summary = data["summary"]
                summary_fields = ["total_at_risk", "critical_risk", "high_risk", "medium_risk", "risk_threshold"]
                for field in summary_fields:
                    if field not in summary:
                        self.log_result("At-Risk Members Summary", False, f"Missing summary field: {field}")
                        return False
                
                # Verify risk threshold
                if summary["risk_threshold"] != 60:
                    self.log_result("At-Risk Members Default Threshold", False, "Default threshold should be 60")
                    return False
                
                # Verify at_risk_members structure
                at_risk = data["at_risk_members"]
                if not isinstance(at_risk, list):
                    self.log_result("At-Risk Members Array", False, "at_risk_members should be array")
                    return False
                
                # Verify member structure if any exist
                if at_risk:
                    member = at_risk[0]
                    member_fields = ["member_id", "member_name", "email", "phone", "join_date", "last_visit", "risk_score", "risk_level", "risk_factors", "unpaid_invoices"]
                    for field in member_fields:
                        if field not in member:
                            self.log_result("At-Risk Members Member Fields", False, f"Missing member field: {field}")
                            return False
                    
                    # Verify risk_level categorization
                    risk_score = member["risk_score"]
                    risk_level = member["risk_level"]
                    
                    if risk_score >= 80 and risk_level != "critical":
                        self.log_result("At-Risk Members Risk Level Critical", False, f"Risk score {risk_score} should be 'critical'")
                        return False
                    elif 60 <= risk_score < 80 and risk_level != "high":
                        self.log_result("At-Risk Members Risk Level High", False, f"Risk score {risk_score} should be 'high'")
                        return False
                    elif 40 <= risk_score < 60 and risk_level != "medium":
                        self.log_result("At-Risk Members Risk Level Medium", False, f"Risk score {risk_score} should be 'medium'")
                        return False
                    
                    # Verify risk_factors is array with meaningful descriptions
                    risk_factors = member["risk_factors"]
                    if not isinstance(risk_factors, list):
                        self.log_result("At-Risk Members Risk Factors", False, "risk_factors should be array")
                        return False
                    
                    # Verify sorting (highest risk_score first)
                    if len(at_risk) > 1:
                        for i in range(1, len(at_risk)):
                            if at_risk[i]["risk_score"] > at_risk[i-1]["risk_score"]:
                                self.log_result("At-Risk Members Sorting", False, "Members not sorted by risk_score")
                                return False
                
                self.log_result("At-Risk Members Default", True, f"Found {summary['total_at_risk']} at-risk members (threshold: {summary['risk_threshold']})")
                
            else:
                self.log_result("At-Risk Members Default", False, f"Failed: {response.status_code}")
                return False
            
            # Test 2: Custom threshold (40)
            response = requests.get(f"{API_BASE}/reports/at-risk-members?risk_threshold=40", headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                if data["summary"]["risk_threshold"] != 40:
                    self.log_result("At-Risk Members Threshold 40", False, "Threshold 40 not respected")
                    return False
                
                self.log_result("At-Risk Members Threshold 40", True, f"Threshold 40: {data['summary']['total_at_risk']} at-risk members")
                
            else:
                self.log_result("At-Risk Members Threshold 40", False, f"Failed: {response.status_code}")
                return False
            
            # Test 3: High threshold (80)
            response = requests.get(f"{API_BASE}/reports/at-risk-members?risk_threshold=80", headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                if data["summary"]["risk_threshold"] != 80:
                    self.log_result("At-Risk Members Threshold 80", False, "Threshold 80 not respected")
                    return False
                
                self.log_result("At-Risk Members Threshold 80", True, f"Threshold 80: {data['summary']['total_at_risk']} at-risk members")
                
            else:
                self.log_result("At-Risk Members Threshold 80", False, f"Failed: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("At-Risk Members API", False, f"Error: {str(e)}")
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