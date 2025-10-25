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
    
    def test_member_demographics_api(self):
        """Test GET /api/reports/member-demographics endpoint"""
        print("\n=== Testing Member Demographics API ===")
        
        try:
            # Test 1: Default parameters
            response = requests.get(f"{API_BASE}/reports/member-demographics", headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["summary", "gender_distribution", "age_distribution", "membership_type_distribution", "location_distribution", "status_distribution"]
                
                for field in required_fields:
                    if field not in data:
                        self.log_result("Member Demographics Structure", False, f"Missing field: {field}")
                        return False
                
                # Verify summary structure
                summary = data["summary"]
                summary_fields = ["total_members", "active_members", "active_percentage"]
                for field in summary_fields:
                    if field not in summary:
                        self.log_result("Member Demographics Summary", False, f"Missing summary field: {field}")
                        return False
                
                # Verify active_percentage calculation
                total = summary["total_members"]
                active = summary["active_members"]
                active_pct = summary["active_percentage"]
                expected_pct = round((active / total) * 100, 2) if total > 0 else 0
                if abs(active_pct - expected_pct) > 0.01:
                    self.log_result("Member Demographics Active Percentage", False, f"Active percentage calculation incorrect: {active_pct} vs expected {expected_pct}")
                    return False
                
                # Verify gender_distribution is object
                gender_dist = data["gender_distribution"]
                if not isinstance(gender_dist, dict):
                    self.log_result("Member Demographics Gender", False, "gender_distribution should be object")
                    return False
                
                # Verify age_distribution structure
                age_dist = data["age_distribution"]
                expected_age_groups = ["Under 18", "18-25", "26-35", "36-45", "46-55", "56-65", "Over 65", "Unknown"]
                for group in expected_age_groups:
                    if group not in age_dist:
                        self.log_result("Member Demographics Age Groups", False, f"Missing age group: {group}")
                        return False
                
                # Verify age groups sum to total_members
                age_sum = sum(age_dist.values())
                if age_sum != total:
                    self.log_result("Member Demographics Age Sum", False, f"Age groups sum ({age_sum}) doesn't match total members ({total})")
                    return False
                
                # Verify membership_type_distribution is object
                type_dist = data["membership_type_distribution"]
                if not isinstance(type_dist, dict):
                    self.log_result("Member Demographics Membership Types", False, "membership_type_distribution should be object")
                    return False
                
                # Verify location_distribution is object (top 10)
                location_dist = data["location_distribution"]
                if not isinstance(location_dist, dict):
                    self.log_result("Member Demographics Locations", False, "location_distribution should be object")
                    return False
                
                # Verify top 10 locations limit
                if len(location_dist) > 10:
                    self.log_result("Member Demographics Location Limit", False, "location_distribution should be limited to top 10")
                    return False
                
                # Verify status_distribution is object
                status_dist = data["status_distribution"]
                if not isinstance(status_dist, dict):
                    self.log_result("Member Demographics Status", False, "status_distribution should be object")
                    return False
                
                self.log_result("Member Demographics Default", True, f"Total: {total} members, Active: {active_pct}%")
                
            else:
                self.log_result("Member Demographics Default", False, f"Failed: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Member Demographics API", False, f"Error: {str(e)}")
            return False
    
    def test_acquisition_cost_api(self):
        """Test GET /api/reports/acquisition-cost endpoint"""
        print("\n=== Testing Acquisition Cost API ===")
        
        try:
            # Test 1: Default parameters (last 90 days)
            response = requests.get(f"{API_BASE}/reports/acquisition-cost", headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["period", "summary", "by_source", "best_performing_source", "worst_performing_source"]
                
                for field in required_fields:
                    if field not in data:
                        self.log_result("Acquisition Cost Structure", False, f"Missing field: {field}")
                        return False
                
                # Verify period structure
                period = data["period"]
                period_fields = ["start_date", "end_date"]
                for field in period_fields:
                    if field not in period:
                        self.log_result("Acquisition Cost Period", False, f"Missing period field: {field}")
                        return False
                
                # Verify summary structure
                summary = data["summary"]
                summary_fields = ["total_leads", "total_converted", "overall_conversion_rate", "total_estimated_cost", "average_cost_per_lead", "average_cost_per_acquisition"]
                for field in summary_fields:
                    if field not in summary:
                        self.log_result("Acquisition Cost Summary", False, f"Missing summary field: {field}")
                        return False
                
                # Verify conversion rate calculation
                total_leads = summary["total_leads"]
                total_converted = summary["total_converted"]
                conversion_rate = summary["overall_conversion_rate"]
                expected_rate = round((total_converted / total_leads) * 100, 2) if total_leads > 0 else 0
                if abs(conversion_rate - expected_rate) > 0.01:
                    self.log_result("Acquisition Cost Conversion Rate", False, f"Conversion rate calculation incorrect: {conversion_rate} vs expected {expected_rate}")
                    return False
                
                # Verify by_source structure
                by_source = data["by_source"]
                if not isinstance(by_source, list):
                    self.log_result("Acquisition Cost By Source", False, "by_source should be array")
                    return False
                
                # Verify source structure if any exist
                if by_source:
                    source = by_source[0]
                    source_fields = ["source", "total_leads", "converted_leads", "conversion_rate", "estimated_cost", "cost_per_lead", "cost_per_acquisition", "roi", "revenue_generated"]
                    for field in source_fields:
                        if field not in source:
                            self.log_result("Acquisition Cost Source Fields", False, f"Missing source field: {field}")
                            return False
                    
                    # Verify sorting (highest conversion_rate first)
                    if len(by_source) > 1:
                        for i in range(1, len(by_source)):
                            if by_source[i]["conversion_rate"] > by_source[i-1]["conversion_rate"]:
                                self.log_result("Acquisition Cost Sorting", False, "Sources not sorted by conversion_rate")
                                return False
                    
                    # Verify cost calculations
                    total_cost = source["estimated_cost"]
                    converted = source["converted_leads"]
                    cost_per_acq = source["cost_per_acquisition"]
                    expected_cost_per_acq = round(total_cost / converted, 2) if converted > 0 else 0
                    if abs(cost_per_acq - expected_cost_per_acq) > 0.01:
                        self.log_result("Acquisition Cost Per Acquisition", False, f"Cost per acquisition calculation incorrect: {cost_per_acq} vs expected {expected_cost_per_acq}")
                        return False
                
                # Verify best/worst performing sources
                best_source = data["best_performing_source"]
                worst_source = data["worst_performing_source"]
                
                if by_source:
                    if best_source and best_source != by_source[0]:
                        self.log_result("Acquisition Cost Best Source", False, "Best performing source should be first in sorted list")
                        return False
                    
                    if worst_source and worst_source != by_source[-1]:
                        self.log_result("Acquisition Cost Worst Source", False, "Worst performing source should be last in sorted list")
                        return False
                
                self.log_result("Acquisition Cost Default", True, f"Total leads: {total_leads}, Conversion rate: {conversion_rate}%")
                
            else:
                self.log_result("Acquisition Cost Default", False, f"Failed: {response.status_code}")
                return False
            
            # Test 2: Custom date range
            end_date = "2024-12-31T23:59:59Z"
            start_date = "2024-01-01T00:00:00Z"
            
            response = requests.get(
                f"{API_BASE}/reports/acquisition-cost",
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
                    self.log_result("Acquisition Cost Custom Dates", False, "Date range not respected")
                    return False
                
                self.log_result("Acquisition Cost Custom Dates", True, f"Custom range: {data['summary']['total_leads']} leads")
                
            else:
                self.log_result("Acquisition Cost Custom Dates", False, f"Failed: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Acquisition Cost API", False, f"Error: {str(e)}")
            return False
    
    def test_response_times(self):
        """Test API response times are reasonable (< 2 seconds)"""
        print("\n=== Testing API Response Times ===")
        
        try:
            endpoints = [
                "/reports/retention-dashboard",
                "/reports/member-ltv", 
                "/reports/at-risk-members",
                "/reports/member-demographics",
                "/reports/acquisition-cost"
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
            # Test invalid date format for acquisition cost
            response = requests.get(
                f"{API_BASE}/reports/acquisition-cost",
                params={"start_date": "invalid-date"},
                headers=self.admin_headers
            )
            
            # Should handle gracefully (either 400, 422, 500 or fallback to defaults)
            if response.status_code in [200, 400, 422, 500]:
                self.log_result("Error Handling Invalid Date", True, f"Handled gracefully: {response.status_code}")
            else:
                self.log_result("Error Handling Invalid Date", False, f"Unexpected status: {response.status_code}")
                return False
            
            # Test invalid risk threshold parameter
            response = requests.get(
                f"{API_BASE}/reports/at-risk-members",
                params={"risk_threshold": "invalid_threshold"},
                headers=self.admin_headers
            )
            
            # Should handle gracefully
            if response.status_code in [200, 400, 422, 500]:
                self.log_result("Error Handling Invalid Threshold", True, f"Handled gracefully: {response.status_code}")
            else:
                self.log_result("Error Handling Invalid Threshold", False, f"Unexpected status: {response.status_code}")
                return False
            
            # Test invalid period_months parameter
            response = requests.get(
                f"{API_BASE}/reports/retention-dashboard",
                params={"period_months": "invalid_period"},
                headers=self.admin_headers
            )
            
            # Should handle gracefully
            if response.status_code in [200, 400, 422, 500]:
                self.log_result("Error Handling Invalid Period", True, f"Handled gracefully: {response.status_code}")
            else:
                self.log_result("Error Handling Invalid Period", False, f"Unexpected status: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Error Handling", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all member analytics & retention API tests"""
        print("🚀 Starting Member Analytics & Retention API Tests...")
        print(f"📍 Testing against: {BASE_URL}")
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return False
        
        # Run all tests
        tests = [
            self.test_retention_dashboard_api,
            self.test_member_ltv_api,
            self.test_at_risk_members_api,
            self.test_member_demographics_api,
            self.test_acquisition_cost_api,
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
    runner = MemberAnalyticsTestRunner()
    success = runner.run_all_tests()
    
    if success:
        print("\n🎉 All Member Analytics & Retention API tests passed!")
        exit(0)
    else:
        print("\n💥 Some tests failed!")
        exit(1)


if __name__ == "__main__":
    main()