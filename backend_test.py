#!/usr/bin/env python3
"""
Backend Test Suite - Sales Performance & Forecasting APIs Testing
Focus on testing the Sales Performance & Forecasting APIs with comprehensive validation
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

class SalesPerformanceTestRunner:
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
    
    # ===================== SALES PERFORMANCE & FORECASTING API TESTS =====================
    
    def test_sales_funnel_api(self):
        """Test GET /api/reports/sales-funnel endpoint"""
        print("\n=== Testing Sales Funnel API ===")
        
        try:
            # Test 1: Default parameters (last 90 days)
            response = requests.get(f"{API_BASE}/reports/sales-funnel", headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["period", "funnel_stages", "summary"]
                
                for field in required_fields:
                    if field not in data:
                        self.log_result("Sales Funnel Structure", False, f"Missing field: {field}")
                        return False
                
                # Verify period structure
                period = data["period"]
                period_fields = ["start_date", "end_date"]
                for field in period_fields:
                    if field not in period:
                        self.log_result("Sales Funnel Period", False, f"Missing period field: {field}")
                        return False
                
                # Verify funnel_stages structure
                stages = data["funnel_stages"]
                if not isinstance(stages, list):
                    self.log_result("Sales Funnel Stages", False, "funnel_stages should be array")
                    return False
                
                # Verify stages are in correct order
                expected_stages = ["lead", "qualified", "proposal", "negotiation", "closed_won"]
                if len(stages) >= len(expected_stages):
                    for i, expected_stage in enumerate(expected_stages):
                        if i < len(stages) and stages[i]["stage"] != expected_stage:
                            self.log_result("Sales Funnel Stage Order", False, f"Stage {i} should be '{expected_stage}', got '{stages[i]['stage']}'")
                            return False
                
                # Verify stage structure
                if stages:
                    stage = stages[0]
                    stage_fields = ["stage", "label", "count", "conversion_rate", "drop_off", "drop_off_rate"]
                    for field in stage_fields:
                        if field not in stage:
                            self.log_result("Sales Funnel Stage Fields", False, f"Missing stage field: {field}")
                            return False
                    
                    # Verify first stage has 100% conversion rate
                    if stage["conversion_rate"] != 100.0:
                        self.log_result("Sales Funnel First Stage Conversion", False, f"First stage should have 100% conversion rate, got {stage['conversion_rate']}")
                        return False
                
                # Verify summary structure
                summary = data["summary"]
                summary_fields = ["total_leads", "total_won", "overall_conversion_rate", "biggest_drop_off_stage"]
                for field in summary_fields:
                    if field not in summary:
                        self.log_result("Sales Funnel Summary", False, f"Missing summary field: {field}")
                        return False
                
                # Verify conversion rates are calculated correctly
                for stage in stages:
                    conversion_rate = stage["conversion_rate"]
                    if not (0 <= conversion_rate <= 100):
                        self.log_result("Sales Funnel Conversion Rate Range", False, f"Conversion rate should be 0-100%, got {conversion_rate}")
                        return False
                
                self.log_result("Sales Funnel Default", True, f"Total leads: {summary['total_leads']}, Overall conversion: {summary['overall_conversion_rate']}%")
                
            else:
                self.log_result("Sales Funnel Default", False, f"Failed: {response.status_code}")
                return False
            
            # Test 2: Custom date range
            end_date = "2024-12-31T23:59:59Z"
            start_date = "2024-01-01T00:00:00Z"
            
            response = requests.get(
                f"{API_BASE}/reports/sales-funnel",
                params={"start_date": start_date, "end_date": end_date},
                headers=self.admin_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                period = data["period"]
                
                # Verify date range is respected
                start_check = "2024-01-01" in period["start_date"]
                end_check = "2024-12-31" in period["end_date"]
                if not start_check or not end_check:
                    self.log_result("Sales Funnel Custom Dates", False, "Date range not respected")
                    return False
                
                self.log_result("Sales Funnel Custom Dates", True, f"Custom range: {data['summary']['total_leads']} leads")
                
            else:
                self.log_result("Sales Funnel Custom Dates", False, f"Failed: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Sales Funnel API", False, f"Error: {str(e)}")
            return False
    
    def test_pipeline_forecast_api(self):
        """Test GET /api/reports/pipeline-forecast endpoint"""
        print("\n=== Testing Pipeline Forecast API ===")
        
        try:
            # Test 1: Default parameters
            response = requests.get(f"{API_BASE}/reports/pipeline-forecast", headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["summary", "pipeline_by_stage", "stage_probabilities"]
                
                for field in required_fields:
                    if field not in data:
                        self.log_result("Pipeline Forecast Structure", False, f"Missing field: {field}")
                        return False
                
                # Verify summary structure
                summary = data["summary"]
                summary_fields = ["total_opportunities", "total_pipeline_value", "weighted_pipeline_value", "predicted_revenue", "closing_this_month", "closing_this_month_value", "closing_this_month_weighted", "avg_days_to_close"]
                for field in summary_fields:
                    if field not in summary:
                        self.log_result("Pipeline Forecast Summary", False, f"Missing summary field: {field}")
                        return False
                
                # Verify pipeline_by_stage structure
                pipeline_stages = data["pipeline_by_stage"]
                if not isinstance(pipeline_stages, list):
                    self.log_result("Pipeline Forecast Stages", False, "pipeline_by_stage should be array")
                    return False
                
                # Verify stage structure if any exist
                if pipeline_stages:
                    stage = pipeline_stages[0]
                    stage_fields = ["stage", "count", "total_value", "weighted_value", "probability"]
                    for field in stage_fields:
                        if field not in stage:
                            self.log_result("Pipeline Forecast Stage Fields", False, f"Missing stage field: {field}")
                            return False
                
                # Verify stage_probabilities structure
                probabilities = data["stage_probabilities"]
                expected_probs = {
                    "lead": 0.10,
                    "qualified": 0.25,
                    "proposal": 0.50,
                    "negotiation": 0.75,
                    "closed_won": 1.00
                }
                
                for stage, expected_prob in expected_probs.items():
                    if stage not in probabilities:
                        self.log_result("Pipeline Forecast Probabilities", False, f"Missing probability for stage: {stage}")
                        return False
                    
                    if probabilities[stage] != expected_prob:
                        self.log_result("Pipeline Forecast Probability Values", False, f"Stage {stage} should have probability {expected_prob}, got {probabilities[stage]}")
                        return False
                
                # Verify weighted calculations use correct probabilities
                for stage in pipeline_stages:
                    stage_name = stage["stage"]
                    if stage_name in probabilities:
                        expected_weighted = round(stage["total_value"] * probabilities[stage_name], 2)
                        actual_weighted = stage["weighted_value"]
                        if abs(actual_weighted - expected_weighted) > 0.01:
                            self.log_result("Pipeline Forecast Weighted Calculation", False, f"Stage {stage_name} weighted value incorrect: {actual_weighted} vs expected {expected_weighted}")
                            return False
                
                # Verify all currency values are rounded to 2 decimals
                currency_fields = ["total_pipeline_value", "weighted_pipeline_value", "predicted_revenue", "closing_this_month_value", "closing_this_month_weighted"]
                for field in currency_fields:
                    value = summary[field]
                    if isinstance(value, float) and round(value, 2) != value:
                        self.log_result("Pipeline Forecast Currency Rounding", False, f"Currency field {field} not rounded to 2 decimals: {value}")
                        return False
                
                self.log_result("Pipeline Forecast Default", True, f"Total opportunities: {summary['total_opportunities']}, Pipeline value: R{summary['total_pipeline_value']:.2f}")
                
            else:
                self.log_result("Pipeline Forecast Default", False, f"Failed: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Pipeline Forecast API", False, f"Error: {str(e)}")
            return False
    
    def test_lead_source_roi_api(self):
        """Test GET /api/reports/lead-source-roi endpoint"""
        print("\n=== Testing Lead Source ROI API ===")
        
        try:
            # Test 1: Default parameters (last 90 days)
            response = requests.get(f"{API_BASE}/reports/lead-source-roi", headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["period", "sources", "best_roi_source", "worst_roi_source"]
                
                for field in required_fields:
                    if field not in data:
                        self.log_result("Lead Source ROI Structure", False, f"Missing field: {field}")
                        return False
                
                # Verify period structure
                period = data["period"]
                period_fields = ["start_date", "end_date"]
                for field in period_fields:
                    if field not in period:
                        self.log_result("Lead Source ROI Period", False, f"Missing period field: {field}")
                        return False
                
                # Verify sources structure
                sources = data["sources"]
                if not isinstance(sources, list):
                    self.log_result("Lead Source ROI Sources", False, "sources should be array")
                    return False
                
                # Verify source structure if any exist
                if sources:
                    source = sources[0]
                    source_fields = ["source", "total_leads", "qualified_leads", "converted_leads", "lost_leads", "revenue_generated", "avg_deal_size", "conversion_rate", "qualification_rate", "estimated_cost", "cost_per_lead", "cost_per_acquisition", "roi"]
                    for field in source_fields:
                        if field not in source:
                            self.log_result("Lead Source ROI Source Fields", False, f"Missing source field: {field}")
                            return False
                    
                    # Verify all rates are percentages between 0-100
                    rates = ["conversion_rate", "qualification_rate"]
                    for rate_field in rates:
                        rate_value = source[rate_field]
                        if not (0 <= rate_value <= 100):
                            self.log_result("Lead Source ROI Rate Range", False, f"{rate_field} should be 0-100%, got {rate_value}")
                            return False
                    
                    # Verify sources are sorted by ROI (highest first)
                    if len(sources) > 1:
                        for i in range(1, len(sources)):
                            if sources[i]["roi"] > sources[i-1]["roi"]:
                                self.log_result("Lead Source ROI Sorting", False, "Sources not sorted by ROI (highest first)")
                                return False
                
                # Verify best/worst ROI sources
                best_roi = data["best_roi_source"]
                worst_roi = data["worst_roi_source"]
                
                if sources:
                    if best_roi and best_roi != sources[0]:
                        self.log_result("Lead Source ROI Best Source", False, "Best ROI source should be first in sorted list")
                        return False
                    
                    if worst_roi and worst_roi != sources[-1]:
                        self.log_result("Lead Source ROI Worst Source", False, "Worst ROI source should be last in sorted list")
                        return False
                
                self.log_result("Lead Source ROI Default", True, f"Found {len(sources)} sources")
                
            else:
                self.log_result("Lead Source ROI Default", False, f"Failed: {response.status_code}")
                return False
            
            # Test 2: Custom date range
            end_date = "2024-12-31T23:59:59Z"
            start_date = "2024-01-01T00:00:00Z"
            
            response = requests.get(
                f"{API_BASE}/reports/lead-source-roi",
                params={"start_date": start_date, "end_date": end_date},
                headers=self.admin_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                period = data["period"]
                
                # Verify date range is respected
                start_check = "2024-01-01" in period["start_date"]
                end_check = "2024-12-31" in period["end_date"]
                if not start_check or not end_check:
                    self.log_result("Lead Source ROI Custom Dates", False, "Date range not respected")
                    return False
                
                self.log_result("Lead Source ROI Custom Dates", True, f"Custom range: {len(data['sources'])} sources")
                
            else:
                self.log_result("Lead Source ROI Custom Dates", False, f"Failed: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Lead Source ROI API", False, f"Error: {str(e)}")
            return False
    
    def test_win_loss_analysis_api(self):
        """Test GET /api/reports/win-loss-analysis endpoint"""
        print("\n=== Testing Win-Loss Analysis API ===")
        
        try:
            # Test 1: Default parameters (last 90 days)
            response = requests.get(f"{API_BASE}/reports/win-loss-analysis", headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["period", "summary", "loss_reasons", "top_loss_reason", "salesperson_performance"]
                
                for field in required_fields:
                    if field not in data:
                        self.log_result("Win-Loss Analysis Structure", False, f"Missing field: {field}")
                        return False
                
                # Verify period structure
                period = data["period"]
                period_fields = ["start_date", "end_date"]
                for field in period_fields:
                    if field not in period:
                        self.log_result("Win-Loss Analysis Period", False, f"Missing period field: {field}")
                        return False
                
                # Verify summary structure
                summary = data["summary"]
                summary_fields = ["total_won", "total_lost", "total_closed", "win_rate", "won_revenue", "lost_revenue", "avg_won_deal_size", "avg_lost_deal_size"]
                for field in summary_fields:
                    if field not in summary:
                        self.log_result("Win-Loss Analysis Summary", False, f"Missing summary field: {field}")
                        return False
                
                # Verify win_rate calculation
                total_won = summary["total_won"]
                total_closed = summary["total_closed"]
                win_rate = summary["win_rate"]
                expected_win_rate = round((total_won / total_closed) * 100, 2) if total_closed > 0 else 0
                if abs(win_rate - expected_win_rate) > 0.01:
                    self.log_result("Win-Loss Analysis Win Rate", False, f"Win rate calculation incorrect: {win_rate} vs expected {expected_win_rate}")
                    return False
                
                # Verify loss_reasons structure
                loss_reasons = data["loss_reasons"]
                if not isinstance(loss_reasons, list):
                    self.log_result("Win-Loss Analysis Loss Reasons", False, "loss_reasons should be array")
                    return False
                
                # Verify loss reason structure if any exist
                if loss_reasons:
                    reason = loss_reasons[0]
                    reason_fields = ["reason", "count", "percentage"]
                    for field in reason_fields:
                        if field not in reason:
                            self.log_result("Win-Loss Analysis Reason Fields", False, f"Missing reason field: {field}")
                            return False
                    
                    # Verify loss_reasons are sorted by count (highest first)
                    if len(loss_reasons) > 1:
                        for i in range(1, len(loss_reasons)):
                            if loss_reasons[i]["count"] > loss_reasons[i-1]["count"]:
                                self.log_result("Win-Loss Analysis Reason Sorting", False, "Loss reasons not sorted by count (highest first)")
                                return False
                
                # Verify top_loss_reason
                top_loss_reason = data["top_loss_reason"]
                if loss_reasons and top_loss_reason and top_loss_reason != loss_reasons[0]:
                    self.log_result("Win-Loss Analysis Top Loss Reason", False, "Top loss reason should be first in sorted list")
                    return False
                
                # Verify salesperson_performance structure
                salesperson_perf = data["salesperson_performance"]
                if not isinstance(salesperson_perf, list):
                    self.log_result("Win-Loss Analysis Salesperson Performance", False, "salesperson_performance should be array")
                    return False
                
                # Verify salesperson structure if any exist
                if salesperson_perf:
                    salesperson = salesperson_perf[0]
                    salesperson_fields = ["salesperson_id", "salesperson_name", "won", "lost", "win_rate", "total_closed"]
                    for field in salesperson_fields:
                        if field not in salesperson:
                            self.log_result("Win-Loss Analysis Salesperson Fields", False, f"Missing salesperson field: {field}")
                            return False
                    
                    # Verify salesperson_performance is sorted by win_rate (highest first)
                    if len(salesperson_perf) > 1:
                        for i in range(1, len(salesperson_perf)):
                            if salesperson_perf[i]["win_rate"] > salesperson_perf[i-1]["win_rate"]:
                                self.log_result("Win-Loss Analysis Salesperson Sorting", False, "Salesperson performance not sorted by win_rate (highest first)")
                                return False
                
                self.log_result("Win-Loss Analysis Default", True, f"Total closed: {total_closed}, Win rate: {win_rate}%")
                
            else:
                self.log_result("Win-Loss Analysis Default", False, f"Failed: {response.status_code}")
                return False
            
            # Test 2: Custom date range
            end_date = "2024-12-31T23:59:59Z"
            start_date = "2024-01-01T00:00:00Z"
            
            response = requests.get(
                f"{API_BASE}/reports/win-loss-analysis",
                params={"start_date": start_date, "end_date": end_date},
                headers=self.admin_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                period = data["period"]
                
                # Verify date range is respected
                start_check = "2024-01-01" in period["start_date"]
                end_check = "2024-12-31" in period["end_date"]
                if not start_check or not end_check:
                    self.log_result("Win-Loss Analysis Custom Dates", False, "Date range not respected")
                    return False
                
                self.log_result("Win-Loss Analysis Custom Dates", True, f"Custom range: {data['summary']['total_closed']} closed deals")
                
            else:
                self.log_result("Win-Loss Analysis Custom Dates", False, f"Failed: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Win-Loss Analysis API", False, f"Error: {str(e)}")
            return False
    
    def test_salesperson_performance_api(self):
        """Test GET /api/reports/salesperson-performance endpoint"""
        print("\n=== Testing Salesperson Performance API ===")
        
        try:
            # Test 1: Default parameters (last 30 days, all salespeople)
            response = requests.get(f"{API_BASE}/reports/salesperson-performance", headers=self.admin_headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["period", "team_summary", "salesperson_performance", "top_performer"]
                
                for field in required_fields:
                    if field not in data:
                        self.log_result("Salesperson Performance Structure", False, f"Missing field: {field}")
                        return False
                
                # Verify period structure
                period = data["period"]
                period_fields = ["start_date", "end_date"]
                for field in period_fields:
                    if field not in period:
                        self.log_result("Salesperson Performance Period", False, f"Missing period field: {field}")
                        return False
                
                # Verify team_summary structure
                team_summary = data["team_summary"]
                team_fields = ["total_leads", "total_opportunities", "total_won", "total_revenue", "total_pipeline_value"]
                for field in team_fields:
                    if field not in team_summary:
                        self.log_result("Salesperson Performance Team Summary", False, f"Missing team summary field: {field}")
                        return False
                
                # Verify salesperson_performance structure
                salesperson_perf = data["salesperson_performance"]
                if not isinstance(salesperson_perf, list):
                    self.log_result("Salesperson Performance Array", False, "salesperson_performance should be array")
                    return False
                
                # Verify salesperson structure if any exist
                if salesperson_perf:
                    salesperson = salesperson_perf[0]
                    salesperson_fields = ["salesperson_id", "salesperson_name", "email", "role", "total_leads", "qualified_leads", "converted_leads", "lead_conversion_rate", "total_opportunities", "won_opportunities", "lost_opportunities", "opp_win_rate", "open_opportunities", "pipeline_value", "won_revenue", "avg_deal_size"]
                    for field in salesperson_fields:
                        if field not in salesperson:
                            self.log_result("Salesperson Performance Fields", False, f"Missing salesperson field: {field}")
                            return False
                    
                    # Verify conversion rates are calculated correctly
                    total_leads = salesperson["total_leads"]
                    converted_leads = salesperson["converted_leads"]
                    lead_conversion_rate = salesperson["lead_conversion_rate"]
                    expected_lead_rate = round((converted_leads / total_leads) * 100, 2) if total_leads > 0 else 0
                    if abs(lead_conversion_rate - expected_lead_rate) > 0.01:
                        self.log_result("Salesperson Performance Lead Conversion", False, f"Lead conversion rate incorrect: {lead_conversion_rate} vs expected {expected_lead_rate}")
                        return False
                    
                    # Verify salesperson_performance is sorted by won_revenue (highest first)
                    if len(salesperson_perf) > 1:
                        for i in range(1, len(salesperson_perf)):
                            if salesperson_perf[i]["won_revenue"] > salesperson_perf[i-1]["won_revenue"]:
                                self.log_result("Salesperson Performance Sorting", False, "Salesperson performance not sorted by won_revenue (highest first)")
                                return False
                
                # Verify top_performer
                top_performer = data["top_performer"]
                if salesperson_perf and top_performer and top_performer != salesperson_perf[0]:
                    self.log_result("Salesperson Performance Top Performer", False, "Top performer should be first in sorted list")
                    return False
                
                self.log_result("Salesperson Performance Default", True, f"Team revenue: R{team_summary['total_revenue']:.2f}, {len(salesperson_perf)} salespeople")
                
            else:
                self.log_result("Salesperson Performance Default", False, f"Failed: {response.status_code}")
                return False
            
            # Test 2: Custom date range
            end_date = "2024-12-31T23:59:59Z"
            start_date = "2024-01-01T00:00:00Z"
            
            response = requests.get(
                f"{API_BASE}/reports/salesperson-performance",
                params={"start_date": start_date, "end_date": end_date},
                headers=self.admin_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                period = data["period"]
                
                # Verify date range is respected
                start_check = "2024-01-01" in period["start_date"]
                end_check = "2024-12-31" in period["end_date"]
                if not start_check or not end_check:
                    self.log_result("Salesperson Performance Custom Dates", False, "Date range not respected")
                    return False
                
                self.log_result("Salesperson Performance Custom Dates", True, f"Custom range: R{data['team_summary']['total_revenue']:.2f} revenue")
                
            else:
                self.log_result("Salesperson Performance Custom Dates", False, f"Failed: {response.status_code}")
                return False
            
            # Test 3: Specific salesperson (if we have any)
            if salesperson_perf:
                salesperson_id = salesperson_perf[0]["salesperson_id"]
                response = requests.get(
                    f"{API_BASE}/reports/salesperson-performance",
                    params={"salesperson_id": salesperson_id},
                    headers=self.admin_headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Should only return data for the specific salesperson
                    if len(data["salesperson_performance"]) > 1:
                        # Check if all returned salespeople have the same ID
                        all_same_id = all(sp["salesperson_id"] == salesperson_id for sp in data["salesperson_performance"])
                        if not all_same_id:
                            self.log_result("Salesperson Performance Specific ID", False, "Should only return data for specified salesperson")
                            return False
                    
                    self.log_result("Salesperson Performance Specific ID", True, f"Specific salesperson: {data['salesperson_performance'][0]['salesperson_name']}")
                    
                else:
                    self.log_result("Salesperson Performance Specific ID", False, f"Failed: {response.status_code}")
                    return False
            
            return True
            
        except Exception as e:
            self.log_result("Salesperson Performance API", False, f"Error: {str(e)}")
            return False
    
    def test_response_times(self):
        """Test API response times are reasonable (< 2 seconds)"""
        print("\n=== Testing API Response Times ===")
        
        try:
            endpoints = [
                "/reports/sales-funnel",
                "/reports/pipeline-forecast", 
                "/reports/lead-source-roi",
                "/reports/win-loss-analysis",
                "/reports/salesperson-performance"
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
            # Test invalid date format for sales funnel
            response = requests.get(
                f"{API_BASE}/reports/sales-funnel",
                params={"start_date": "invalid-date"},
                headers=self.admin_headers
            )
            
            # Should handle gracefully (either 400, 422, 500 or fallback to defaults)
            if response.status_code in [200, 400, 422, 500]:
                self.log_result("Error Handling Invalid Date", True, f"Handled gracefully: {response.status_code}")
            else:
                self.log_result("Error Handling Invalid Date", False, f"Unexpected status: {response.status_code}")
                return False
            
            # Test invalid salesperson_id parameter
            response = requests.get(
                f"{API_BASE}/reports/salesperson-performance",
                params={"salesperson_id": "invalid_id"},
                headers=self.admin_headers
            )
            
            # Should handle gracefully
            if response.status_code in [200, 400, 422, 500]:
                self.log_result("Error Handling Invalid Salesperson ID", True, f"Handled gracefully: {response.status_code}")
            else:
                self.log_result("Error Handling Invalid Salesperson ID", False, f"Unexpected status: {response.status_code}")
                return False
            
            # Test invalid date range (end before start)
            response = requests.get(
                f"{API_BASE}/reports/lead-source-roi",
                params={"start_date": "2024-12-31T23:59:59Z", "end_date": "2024-01-01T00:00:00Z"},
                headers=self.admin_headers
            )
            
            # Should handle gracefully
            if response.status_code in [200, 400, 422, 500]:
                self.log_result("Error Handling Invalid Date Range", True, f"Handled gracefully: {response.status_code}")
            else:
                self.log_result("Error Handling Invalid Date Range", False, f"Unexpected status: {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_result("Error Handling", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all sales performance & forecasting API tests"""
        print("🚀 Starting Sales Performance & Forecasting API Tests...")
        print(f"📍 Testing against: {BASE_URL}")
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return False
        
        # Run all tests
        tests = [
            self.test_sales_funnel_api,
            self.test_pipeline_forecast_api,
            self.test_lead_source_roi_api,
            self.test_win_loss_analysis_api,
            self.test_salesperson_performance_api,
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
    runner = SalesPerformanceTestRunner()
    success = runner.run_all_tests()
    
    if success:
        print("\n🎉 All Sales Performance & Forecasting API tests passed!")
        exit(0)
    else:
        print("\n💥 Some tests failed!")
        exit(1)


if __name__ == "__main__":
    main()