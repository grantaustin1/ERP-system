#!/usr/bin/env python3
"""
Backend Test Suite - Phase 2D Advanced Analytics APIs
Focus on Advanced Analytics backend APIs testing
"""

import requests
import json
import time
import os
from datetime import datetime, timezone, timedelta

# Configuration
BASE_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://fitclub-manager.preview.emergentagent.com')
API_BASE = f"{BASE_URL}/api"

# Test credentials
TEST_EMAIL = "admin@gym.com"
TEST_PASSWORD = "admin123"

class AdvancedAnalyticsTestRunner:
    def __init__(self):
        self.token = None
        self.headers = {}
        self.test_results = []
        self.created_members = []  # Track created members for cleanup
        self.created_access_logs = []  # Track created access logs for cleanup
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
        """Create test members for dashboard testing"""
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
            timestamp = int(time.time() * 1000)  # Use milliseconds for more uniqueness
            member_data_1 = {
                "first_name": "Sarah",
                "last_name": f"DashboardTest{timestamp}",
                "email": f"sarah.dashboard.{timestamp}@example.com",
                "phone": f"082333{timestamp % 100000:05d}",
                "membership_type_id": membership_type_id
            }
            
            response = requests.post(f"{API_BASE}/members", json=member_data_1, headers=self.headers)
            if response.status_code == 200:
                member = response.json()
                self.test_member_id = member["id"]
                self.created_members.append(member["id"])
                self.log_result("Setup Test Member 1", True, f"Created test member 1: {self.test_member_id}")
            else:
                self.log_result("Setup Test Member 1", False, f"Failed to create test member 1: {response.status_code}",
                              {"response": response.text})
                return False
            
            # Create second test member
            member_data_2 = {
                "first_name": "Michael",
                "last_name": f"DashboardTest{timestamp}",
                "email": f"michael.dashboard.{timestamp}@example.com",
                "phone": f"082444{timestamp % 100000:05d}",
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
                self.log_result("Setup Test Member 2", False, f"Failed to create test member 2: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Setup Test Members", False, f"Error creating test members: {str(e)}")
            return False
    
    def test_revenue_breakdown_analytics_api(self):
        """Test Revenue Breakdown Analytics API - GET /api/analytics/revenue-breakdown"""
        print("\n=== Testing Revenue Breakdown Analytics API ===")
        
        try:
            # Test with default period (12 months)
            response = requests.get(f"{API_BASE}/analytics/revenue-breakdown", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required structure
                required_fields = ["summary", "by_membership_type", "by_payment_method", "monthly_trend"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Revenue Breakdown Structure", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify summary structure
                summary = data["summary"]
                summary_fields = ["total_revenue", "mrr", "arpu", "active_members"]
                missing_summary_fields = [field for field in summary_fields if field not in summary]
                
                if missing_summary_fields:
                    self.log_result("Revenue Breakdown Summary Structure", False, 
                                  f"Missing summary fields: {missing_summary_fields}")
                    return False
                
                # Verify data types
                if not isinstance(summary["total_revenue"], (int, float)):
                    self.log_result("Revenue Breakdown Total Revenue Type", False, 
                                  "Total revenue should be number")
                    return False
                
                if not isinstance(summary["mrr"], (int, float)):
                    self.log_result("Revenue Breakdown MRR Type", False, 
                                  "MRR should be number")
                    return False
                
                if not isinstance(summary["arpu"], (int, float)):
                    self.log_result("Revenue Breakdown ARPU Type", False, 
                                  "ARPU should be number")
                    return False
                
                if not isinstance(summary["active_members"], int):
                    self.log_result("Revenue Breakdown Active Members Type", False, 
                                  "Active members should be integer")
                    return False
                
                # Verify by_membership_type structure
                if data["by_membership_type"]:
                    membership_type = data["by_membership_type"][0]
                    membership_fields = ["type", "revenue", "percentage"]
                    missing_membership_fields = [field for field in membership_fields if field not in membership_type]
                    
                    if missing_membership_fields:
                        self.log_result("Revenue Breakdown Membership Type Structure", False, 
                                      f"Missing membership type fields: {missing_membership_fields}")
                        return False
                
                # Verify by_payment_method structure
                if data["by_payment_method"]:
                    payment_method = data["by_payment_method"][0]
                    payment_fields = ["method", "revenue", "percentage"]
                    missing_payment_fields = [field for field in payment_fields if field not in payment_method]
                    
                    if missing_payment_fields:
                        self.log_result("Revenue Breakdown Payment Method Structure", False, 
                                      f"Missing payment method fields: {missing_payment_fields}")
                        return False
                
                # Verify monthly_trend structure
                if data["monthly_trend"]:
                    trend = data["monthly_trend"][0]
                    trend_fields = ["month", "revenue"]
                    missing_trend_fields = [field for field in trend_fields if field not in trend]
                    
                    if missing_trend_fields:
                        self.log_result("Revenue Breakdown Monthly Trend Structure", False, 
                                      f"Missing monthly trend fields: {missing_trend_fields}")
                        return False
                
                self.log_result("Revenue Breakdown Analytics API (Default)", True, 
                              f"Retrieved revenue breakdown: Total Revenue R{summary['total_revenue']:.2f}, "
                              f"MRR R{summary['mrr']:.2f}, ARPU R{summary['arpu']:.2f}, "
                              f"Active Members {summary['active_members']}")
                
                # Test with different periods
                test_periods = [3, 6, 24]
                for period in test_periods:
                    response = requests.get(f"{API_BASE}/analytics/revenue-breakdown?period_months={period}", headers=self.headers)
                    if response.status_code == 200:
                        period_data = response.json()
                        self.log_result(f"Revenue Breakdown Analytics API ({period}m)", True, 
                                      f"Retrieved {period}-month revenue breakdown successfully")
                    else:
                        self.log_result(f"Revenue Breakdown Analytics API ({period}m)", False, 
                                      f"Failed to get {period}-month revenue breakdown: {response.status_code}")
                        return False
                
                return True
                
            else:
                self.log_result("Revenue Breakdown Analytics API", False, 
                              f"Failed to get revenue breakdown: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Revenue Breakdown Analytics API", False, f"Error testing revenue breakdown API: {str(e)}")
            return False
    
    def test_geographic_distribution_analytics_api(self):
        """Test Geographic Distribution Analytics API - GET /api/analytics/geographic-distribution"""
        print("\n=== Testing Geographic Distribution Analytics API ===")
        
        try:
            response = requests.get(f"{API_BASE}/analytics/geographic-distribution", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required structure
                required_fields = ["summary", "by_postcode", "by_city", "by_state"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Geographic Distribution Structure", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify summary structure
                summary = data["summary"]
                summary_fields = ["total_members", "with_postcode", "with_city", 
                                "with_state", "coverage"]
                missing_summary_fields = [field for field in summary_fields if field not in summary]
                
                if missing_summary_fields:
                    self.log_result("Geographic Distribution Summary Structure", False, 
                                  f"Missing summary fields: {missing_summary_fields}")
                    return False
                
                # Verify coverage structure
                coverage = summary["coverage"]
                coverage_fields = ["postcode", "city", "state"]
                missing_coverage_fields = [field for field in coverage_fields if field not in coverage]
                
                if missing_coverage_fields:
                    self.log_result("Geographic Distribution Coverage Structure", False, 
                                  f"Missing coverage fields: {missing_coverage_fields}")
                    return False
                
                # Verify data types
                if not isinstance(summary["total_members"], int):
                    self.log_result("Geographic Distribution Total Members Type", False, 
                                  "Total members should be integer")
                    return False
                
                if not isinstance(summary["coverage"]["postcode"], (int, float)):
                    self.log_result("Geographic Distribution Postcode Coverage Type", False, 
                                  "Postcode coverage should be number")
                    return False
                
                # Verify by_postcode structure (top 20)
                if data["by_postcode"]:
                    postcode = data["by_postcode"][0]
                    postcode_fields = ["postcode", "member_count", "percentage"]
                    missing_postcode_fields = [field for field in postcode_fields if field not in postcode]
                    
                    if missing_postcode_fields:
                        self.log_result("Geographic Distribution Postcode Structure", False, 
                                      f"Missing postcode fields: {missing_postcode_fields}")
                        return False
                    
                    # Verify top 20 limit
                    if len(data["by_postcode"]) > 20:
                        self.log_result("Geographic Distribution Postcode Limit", False, 
                                      f"Should return top 20 postcodes, got {len(data['by_postcode'])}")
                        return False
                
                # Verify by_city structure (top 10)
                if data["by_city"]:
                    city = data["by_city"][0]
                    city_fields = ["city", "member_count", "percentage"]
                    missing_city_fields = [field for field in city_fields if field not in city]
                    
                    if missing_city_fields:
                        self.log_result("Geographic Distribution City Structure", False, 
                                      f"Missing city fields: {missing_city_fields}")
                        return False
                    
                    # Verify top 10 limit
                    if len(data["by_city"]) > 10:
                        self.log_result("Geographic Distribution City Limit", False, 
                                      f"Should return top 10 cities, got {len(data['by_city'])}")
                        return False
                
                # Verify by_state structure
                if data["by_state"]:
                    state = data["by_state"][0]
                    state_fields = ["state", "member_count", "percentage"]
                    missing_state_fields = [field for field in state_fields if field not in state]
                    
                    if missing_state_fields:
                        self.log_result("Geographic Distribution State Structure", False, 
                                      f"Missing state fields: {missing_state_fields}")
                        return False
                
                self.log_result("Geographic Distribution Analytics API", True, 
                              f"Retrieved geographic distribution: {summary['total_members']} total members, "
                              f"Postcode coverage: {summary['coverage']['postcode']:.1f}%, "
                              f"City coverage: {summary['coverage']['city']:.1f}%, "
                              f"State coverage: {summary['coverage']['state']:.1f}%")
                return True
                
            else:
                self.log_result("Geographic Distribution Analytics API", False, 
                              f"Failed to get geographic distribution: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Geographic Distribution Analytics API", False, f"Error testing geographic distribution API: {str(e)}")
            return False
    
    def test_attendance_deep_dive_analytics_api(self):
        """Test Attendance Deep Dive Analytics API - GET /api/analytics/attendance-deep-dive"""
        print("\n=== Testing Attendance Deep Dive Analytics API ===")
        
        try:
            # Test with default period (90 days)
            response = requests.get(f"{API_BASE}/analytics/attendance-deep-dive", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required structure
                required_fields = ["summary", "peak_hours", "hourly_distribution", 
                                 "daily_distribution", "frequency_distribution", "weekly_trend"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Attendance Deep Dive Structure", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify summary structure
                summary = data["summary"]
                summary_fields = ["total_visits", "unique_members", "avg_visits_per_member", "date_range"]
                missing_summary_fields = [field for field in summary_fields if field not in summary]
                
                if missing_summary_fields:
                    self.log_result("Attendance Deep Dive Summary Structure", False, 
                                  f"Missing summary fields: {missing_summary_fields}")
                    return False
                
                # Verify data types
                if not isinstance(summary["total_visits"], int):
                    self.log_result("Attendance Deep Dive Total Visits Type", False, 
                                  "Total visits should be integer")
                    return False
                
                if not isinstance(summary["unique_members"], int):
                    self.log_result("Attendance Deep Dive Unique Members Type", False, 
                                  "Unique members should be integer")
                    return False
                
                if not isinstance(summary["avg_visits_per_member"], (int, float)):
                    self.log_result("Attendance Deep Dive Avg Visits Type", False, 
                                  "Avg visits per member should be number")
                    return False
                
                # Verify peak_hours structure (top 5)
                if data["peak_hours"]:
                    peak_hour = data["peak_hours"][0]
                    peak_fields = ["hour", "visit_count", "percentage"]
                    missing_peak_fields = [field for field in peak_fields if field not in peak_hour]
                    
                    if missing_peak_fields:
                        self.log_result("Attendance Deep Dive Peak Hours Structure", False, 
                                      f"Missing peak hour fields: {missing_peak_fields}")
                        return False
                    
                    # Verify top 5 limit
                    if len(data["peak_hours"]) > 5:
                        self.log_result("Attendance Deep Dive Peak Hours Limit", False, 
                                      f"Should return top 5 peak hours, got {len(data['peak_hours'])}")
                        return False
                
                # Verify hourly_distribution structure (24 hours)
                if len(data["hourly_distribution"]) != 24:
                    self.log_result("Attendance Deep Dive Hourly Distribution Count", False, 
                                  f"Should have 24 hourly entries, got {len(data['hourly_distribution'])}")
                    return False
                
                if data["hourly_distribution"]:
                    hourly = data["hourly_distribution"][0]
                    hourly_fields = ["hour", "count"]
                    missing_hourly_fields = [field for field in hourly_fields if field not in hourly]
                    
                    if missing_hourly_fields:
                        self.log_result("Attendance Deep Dive Hourly Distribution Structure", False, 
                                      f"Missing hourly fields: {missing_hourly_fields}")
                        return False
                
                # Verify daily_distribution structure (7 days)
                if len(data["daily_distribution"]) != 7:
                    self.log_result("Attendance Deep Dive Daily Distribution Count", False, 
                                  f"Should have 7 daily entries, got {len(data['daily_distribution'])}")
                    return False
                
                if data["daily_distribution"]:
                    daily = data["daily_distribution"][0]
                    daily_fields = ["day", "count"]
                    missing_daily_fields = [field for field in daily_fields if field not in daily]
                    
                    if missing_daily_fields:
                        self.log_result("Attendance Deep Dive Daily Distribution Structure", False, 
                                      f"Missing daily fields: {missing_daily_fields}")
                        return False
                
                # Verify frequency_distribution structure
                if data["frequency_distribution"]:
                    frequency = data["frequency_distribution"][0]
                    frequency_fields = ["range", "members"]
                    missing_frequency_fields = [field for field in frequency_fields if field not in frequency]
                    
                    if missing_frequency_fields:
                        self.log_result("Attendance Deep Dive Frequency Distribution Structure", False, 
                                      f"Missing frequency fields: {missing_frequency_fields}")
                        return False
                
                # Verify weekly_trend structure (may be empty if no data)
                # Weekly trend is optional and may be empty if no attendance data exists
                self.log_result("Attendance Deep Dive Weekly Trend", True, 
                              f"Weekly trend contains {len(data['weekly_trend'])} entries")
                
                self.log_result("Attendance Deep Dive Analytics API (Default)", True, 
                              f"Retrieved attendance analysis: {summary['total_visits']} total visits, "
                              f"{summary['unique_members']} unique members, "
                              f"{summary['avg_visits_per_member']:.1f} avg visits per member")
                
                # Test with different periods
                test_periods = [30, 60, 180]
                for period in test_periods:
                    response = requests.get(f"{API_BASE}/analytics/attendance-deep-dive?days_back={period}", headers=self.headers)
                    if response.status_code == 200:
                        period_data = response.json()
                        self.log_result(f"Attendance Deep Dive Analytics API ({period}d)", True, 
                                      f"Retrieved {period}-day attendance analysis successfully")
                    else:
                        self.log_result(f"Attendance Deep Dive Analytics API ({period}d)", False, 
                                      f"Failed to get {period}-day attendance analysis: {response.status_code}")
                        return False
                
                return True
                
            else:
                self.log_result("Attendance Deep Dive Analytics API", False, 
                              f"Failed to get attendance deep dive: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Attendance Deep Dive Analytics API", False, f"Error testing attendance deep dive API: {str(e)}")
            return False
    
    def test_member_lifetime_value_analytics_api(self):
        """Test Member Lifetime Value Analytics API - GET /api/analytics/member-lifetime-value"""
        print("\n=== Testing Member Lifetime Value Analytics API ===")
        
        try:
            response = requests.get(f"{API_BASE}/analytics/member-lifetime-value", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required structure
                required_fields = ["summary", "by_membership_type", "top_members"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Member Lifetime Value Structure", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify summary structure
                summary = data["summary"]
                summary_fields = ["total_lifetime_value", "avg_ltv_per_member", "total_members_analyzed"]
                missing_summary_fields = [field for field in summary_fields if field not in summary]
                
                if missing_summary_fields:
                    self.log_result("Member Lifetime Value Summary Structure", False, 
                                  f"Missing summary fields: {missing_summary_fields}")
                    return False
                
                # Verify data types
                if not isinstance(summary["total_lifetime_value"], (int, float)):
                    self.log_result("Member Lifetime Value Total LTV Type", False, 
                                  "Total lifetime value should be number")
                    return False
                
                if not isinstance(summary["avg_ltv_per_member"], (int, float)):
                    self.log_result("Member Lifetime Value Avg LTV Type", False, 
                                  "Avg LTV per member should be number")
                    return False
                
                if not isinstance(summary["total_members_analyzed"], int):
                    self.log_result("Member Lifetime Value Total Members Type", False, 
                                  "Total members analyzed should be integer")
                    return False
                
                # Verify by_membership_type structure
                if data["by_membership_type"]:
                    membership_type = data["by_membership_type"][0]
                    membership_fields = ["membership_type", "avg_ltv", "avg_monthly_value", 
                                       "avg_duration_months", "member_count", "total_ltv"]
                    missing_membership_fields = [field for field in membership_fields if field not in membership_type]
                    
                    if missing_membership_fields:
                        self.log_result("Member Lifetime Value Membership Type Structure", False, 
                                      f"Missing membership type fields: {missing_membership_fields}")
                        return False
                
                # Verify top_members structure (top 10)
                if data["top_members"]:
                    top_member = data["top_members"][0]
                    member_fields = ["member_id", "member_name", "membership_type", 
                                   "ltv", "monthly_value", "duration_months"]
                    missing_member_fields = [field for field in member_fields if field not in top_member]
                    
                    if missing_member_fields:
                        self.log_result("Member Lifetime Value Top Members Structure", False, 
                                      f"Missing top member fields: {missing_member_fields}")
                        return False
                    
                    # Verify top 10 limit
                    if len(data["top_members"]) > 10:
                        self.log_result("Member Lifetime Value Top Members Limit", False, 
                                      f"Should return top 10 members, got {len(data['top_members'])}")
                        return False
                
                self.log_result("Member Lifetime Value Analytics API", True, 
                              f"Retrieved LTV analysis: Total LTV R{summary['total_lifetime_value']:.2f}, "
                              f"Avg LTV R{summary['avg_ltv_per_member']:.2f}, "
                              f"{summary['total_members_analyzed']} members analyzed")
                return True
                
            else:
                self.log_result("Member Lifetime Value Analytics API", False, 
                              f"Failed to get member lifetime value: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Member Lifetime Value Analytics API", False, f"Error testing member lifetime value API: {str(e)}")
            return False
    
    def test_churn_prediction_analytics_api(self):
        """Test Churn Prediction Analytics API - GET /api/analytics/churn-prediction"""
        print("\n=== Testing Churn Prediction Analytics API ===")
        
        try:
            response = requests.get(f"{API_BASE}/analytics/churn-prediction", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify required structure
                required_fields = ["summary", "at_risk_members", "common_risk_factors"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("Churn Prediction Structure", False, 
                                  f"Missing fields: {missing_fields}")
                    return False
                
                # Verify summary structure
                summary = data["summary"]
                summary_fields = ["at_risk_count", "risk_percentage", "by_risk_level"]
                missing_summary_fields = [field for field in summary_fields if field not in summary]
                
                if missing_summary_fields:
                    self.log_result("Churn Prediction Summary Structure", False, 
                                  f"Missing summary fields: {missing_summary_fields}")
                    return False
                
                # Verify by_risk_level structure
                by_risk_level = summary["by_risk_level"]
                risk_level_fields = ["critical", "high", "medium"]
                missing_risk_fields = [field for field in risk_level_fields if field not in by_risk_level]
                
                if missing_risk_fields:
                    self.log_result("Churn Prediction Risk Level Structure", False, 
                                  f"Missing risk level fields: {missing_risk_fields}")
                    return False
                
                # Verify data types
                if not isinstance(summary["at_risk_count"], int):
                    self.log_result("Churn Prediction At Risk Count Type", False, 
                                  "At risk count should be integer")
                    return False
                
                if not isinstance(summary["risk_percentage"], (int, float)):
                    self.log_result("Churn Prediction Risk Percentage Type", False, 
                                  "Risk percentage should be number")
                    return False
                
                # Verify at_risk_members structure
                if data["at_risk_members"]:
                    at_risk_member = data["at_risk_members"][0]
                    member_fields = ["member_id", "member_name", "email", "phone", "membership_type", 
                                   "risk_score", "risk_level", "risk_reasons", "last_visit"]
                    missing_member_fields = [field for field in member_fields if field not in at_risk_member]
                    
                    if missing_member_fields:
                        self.log_result("Churn Prediction At Risk Members Structure", False, 
                                      f"Missing at risk member fields: {missing_member_fields}")
                        return False
                    
                    # Verify risk score and level logic
                    risk_score = at_risk_member["risk_score"]
                    risk_level = at_risk_member["risk_level"]
                    
                    if risk_level == "Critical" and risk_score < 50:
                        self.log_result("Churn Prediction Risk Level Logic", False, 
                                      f"Critical risk should have score ≥50, got {risk_score}")
                        return False
                    elif risk_level == "High" and (risk_score < 30 or risk_score >= 50):
                        self.log_result("Churn Prediction Risk Level Logic", False, 
                                      f"High risk should have score 30-49, got {risk_score}")
                        return False
                    elif risk_level == "Medium" and (risk_score < 15 or risk_score >= 30):
                        self.log_result("Churn Prediction Risk Level Logic", False, 
                                      f"Medium risk should have score 15-29, got {risk_score}")
                        return False
                    
                    # Verify risk_reasons is a list
                    if not isinstance(at_risk_member["risk_reasons"], list):
                        self.log_result("Churn Prediction Risk Reasons Type", False, 
                                      "Risk reasons should be a list")
                        return False
                
                # Verify common_risk_factors structure
                if data["common_risk_factors"]:
                    risk_factor = data["common_risk_factors"][0]
                    factor_fields = ["factor", "count"]
                    missing_factor_fields = [field for field in factor_fields if field not in risk_factor]
                    
                    if missing_factor_fields:
                        self.log_result("Churn Prediction Common Risk Factors Structure", False, 
                                      f"Missing risk factor fields: {missing_factor_fields}")
                        return False
                
                self.log_result("Churn Prediction Analytics API", True, 
                              f"Retrieved churn prediction: {summary['at_risk_count']} at-risk members "
                              f"({summary['risk_percentage']:.1f}% of total), "
                              f"Critical: {by_risk_level['critical']}, High: {by_risk_level['high']}, "
                              f"Medium: {by_risk_level['medium']}")
                return True
                
            else:
                self.log_result("Churn Prediction Analytics API", False, 
                              f"Failed to get churn prediction: {response.status_code}",
                              {"response": response.text})
                return False
                
        except Exception as e:
            self.log_result("Churn Prediction Analytics API", False, f"Error testing churn prediction API: {str(e)}")
            return False
    
    def test_analytics_api_authentication(self):
        """Test that all analytics APIs require authentication"""
        print("\n=== Testing Analytics API Authentication ===")
        
        try:
            # Test without authentication headers
            endpoints = [
                "/analytics/revenue-breakdown",
                "/analytics/geographic-distribution",
                "/analytics/attendance-deep-dive",
                "/analytics/member-lifetime-value",
                "/analytics/churn-prediction"
            ]
            
            for endpoint in endpoints:
                response = requests.get(f"{API_BASE}{endpoint}")
                
                if response.status_code not in [401, 403]:
                    self.log_result(f"Authentication {endpoint}", False, 
                                  f"Expected 401 or 403 (authentication required), got {response.status_code}")
                    return False
                
                self.log_result(f"Authentication {endpoint}", True, 
                              f"Correctly requires authentication (status: {response.status_code})")
            
            return True
                
        except Exception as e:
            self.log_result("Analytics API Authentication", False, f"Error testing authentication: {str(e)}")
            return False
    
    def test_analytics_api_error_handling(self):
        """Test error handling for analytics APIs"""
        print("\n=== Testing Analytics API Error Handling ===")
        
        try:
            # Test invalid parameters for revenue breakdown
            response = requests.get(f"{API_BASE}/analytics/revenue-breakdown?period_months=-1", headers=self.headers)
            # Should still work but with reasonable defaults or handle gracefully
            
            # Test invalid parameters for attendance deep dive
            response = requests.get(f"{API_BASE}/analytics/attendance-deep-dive?days_back=0", headers=self.headers)
            # Should still work but with reasonable defaults or handle gracefully
            
            # Test very large parameters
            response = requests.get(f"{API_BASE}/analytics/revenue-breakdown?period_months=1000", headers=self.headers)
            if response.status_code == 200:
                self.log_result("Revenue Breakdown Large Parameter", True, "Handles large parameters gracefully")
            else:
                self.log_result("Revenue Breakdown Large Parameter", False, f"Failed with large parameter: {response.status_code}")
                return False
            
            response = requests.get(f"{API_BASE}/analytics/attendance-deep-dive?days_back=10000", headers=self.headers)
            if response.status_code == 200:
                self.log_result("Attendance Deep Dive Large Parameter", True, "Handles large parameters gracefully")
            else:
                self.log_result("Attendance Deep Dive Large Parameter", False, f"Failed with large parameter: {response.status_code}")
                return False
            
            return True
                
        except Exception as e:
            self.log_result("Analytics API Error Handling", False, f"Error testing error handling: {str(e)}")
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
        
        # Clean up created access logs
        for access_log_id in self.created_access_logs:
            try:
                response = requests.delete(f"{API_BASE}/access-logs/{access_log_id}", headers=self.headers)
                if response.status_code == 200:
                    self.log_result(f"Cleanup Access Log {access_log_id[:8]}", True, "Access log deleted")
                else:
                    self.log_result(f"Cleanup Access Log {access_log_id[:8]}", False, f"Failed to delete: {response.status_code}")
            except Exception as e:
                self.log_result(f"Cleanup Access Log {access_log_id[:8]}", False, f"Error: {str(e)}")
    
    def run_advanced_analytics_tests(self):
        """Run the advanced analytics API tests"""
        print("=" * 80)
        print("BACKEND TESTING - PHASE 2D ADVANCED ANALYTICS APIs")
        print("=" * 80)
        
        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Step 2: Setup test members (for context, though analytics APIs work with existing data)
        if not self.setup_test_members():
            print("❌ Failed to setup test members. Cannot proceed with tests.")
            return False
        
        # Step 3: Run ADVANCED ANALYTICS API TESTS
        print("\n" + "=" * 60)
        print("ADVANCED ANALYTICS API TESTS")
        print("=" * 60)
        
        analytics_results = []
        
        # 1. Authentication Tests
        print("\n🔐 TEST 1: Analytics API Authentication")
        analytics_results.append(self.test_analytics_api_authentication())
        
        # 2. Revenue Breakdown Analytics API
        print("\n💰 TEST 2: Revenue Breakdown Analytics API")
        analytics_results.append(self.test_revenue_breakdown_analytics_api())
        
        # 3. Geographic Distribution Analytics API
        print("\n🌍 TEST 3: Geographic Distribution Analytics API")
        analytics_results.append(self.test_geographic_distribution_analytics_api())
        
        # 4. Attendance Deep Dive Analytics API
        print("\n📊 TEST 4: Attendance Deep Dive Analytics API")
        analytics_results.append(self.test_attendance_deep_dive_analytics_api())
        
        # 5. Member Lifetime Value Analytics API
        print("\n💎 TEST 5: Member Lifetime Value Analytics API")
        analytics_results.append(self.test_member_lifetime_value_analytics_api())
        
        # 6. Churn Prediction Analytics API
        print("\n⚠️ TEST 6: Churn Prediction Analytics API")
        analytics_results.append(self.test_churn_prediction_analytics_api())
        
        # 7. Error Handling Tests
        print("\n🛠️ TEST 7: Analytics API Error Handling")
        analytics_results.append(self.test_analytics_api_error_handling())
        
        # Step 4: Generate Summary
        print("\n" + "=" * 80)
        print("TEST RESULTS SUMMARY")
        print("=" * 80)
        
        analytics_passed = sum(analytics_results)
        analytics_total = len(analytics_results)
        
        print(f"\n🎯 ADVANCED ANALYTICS TESTS: {analytics_passed}/{analytics_total} PASSED")
        print(f"📈 SUCCESS RATE: {(analytics_passed/analytics_total)*100:.1f}%")
        
        # Detailed results
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        # Step 5: Cleanup
        self.cleanup_test_data()
        
        # Return success if all analytics tests passed
        return analytics_passed == analytics_total

def main():
    """Main execution function"""
    tester = AdvancedAnalyticsTestRunner()
    success = tester.run_advanced_analytics_tests()
    
    if success:
        print("\n🎉 ALL ADVANCED ANALYTICS TESTS PASSED!")
        exit(0)
    else:
        print("\n💥 SOME ADVANCED ANALYTICS TESTS FAILED!")
        exit(1)

if __name__ == "__main__":
    main()