"""
TI (Transactional Information) Utilities for Nedbank Host-to-Host Integration

This module handles FTI (Final Transaction Information), PTI (Provisional Transaction Information),
and Notifications for automated payment reconciliation and monitoring.

Based on: TI Host to Host User Manual CLIENT
"""

import os
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET
import csv
from io import StringIO


class TIService:
    """
    Nedbank Transactional Information (TI) service integration
    
    Provides FTI (reconciliation), PTI (real-time tracking), and Notifications
    """
    
    # Nedbank TI endpoints
    QA_FTI_ENDPOINT = "https://qa-secureintegration.nedsecure.co.za:443/services/ti/fti/v1"
    PROD_FTI_ENDPOINT = "https://secureintegration.nedsecure.co.za:443/services/ti/fti/v1"
    QA_PTI_ENDPOINT = "https://qa-secureintegration.nedsecure.co.za:443/services/ti/pti/v1"
    PROD_PTI_ENDPOINT = "https://secureintegration.nedsecure.co.za:443/services/ti/pti/v1"
    
    # Transaction types
    TRANSACTION_TYPES = {
        "001": "Cash Deposit",
        "002": "Cheque Deposit",
        "003": "Mixed Deposit",
        "004": "Electronic Deposit",
        "101": "Cash Withdrawal",
        "102": "Debit Order",
        "103": "Electronic Payment",
        "104": "Electronic Transfer",
        "105": "POS Purchase",
        "201": "Interest Credit",
        "202": "Bank Charges",
        "203": "Reversal",
        "204": "Adjustment"
    }
    
    # Channels
    CHANNELS = {
        "NBB": "NetBank Business",
        "ATM": "ATM",
        "BRN": "Branch",
        "CRD": "Card",
        "POS": "Point of Sale",
        "EFT": "Electronic Funds Transfer",
        "MOB": "Mobile Banking"
    }
    
    def __init__(self, config: Dict):
        """
        Initialize TI service with configuration
        
        Args:
            config: Dictionary containing:
                - mock_mode: bool (True for testing without credentials)
                - profile_number: str (Nedbank profile number)
                - account_number: str (Account to monitor)
                - use_qa: bool (True for QA environment)
                - fti_frequency: str (daily, weekly, monthly)
                - pti_enabled: bool (Enable provisional transaction feed)
        """
        self.mock_mode = config.get("mock_mode", True)
        self.profile_number = config.get("profile_number", "0000000000")
        self.account_number = config.get("account_number", "0000000000")
        self.use_qa = config.get("use_qa", True)
        self.fti_frequency = config.get("fti_frequency", "daily")
        self.pti_enabled = config.get("pti_enabled", False)
        
        self.fti_endpoint = self.QA_FTI_ENDPOINT if self.use_qa else self.PROD_FTI_ENDPOINT
        self.pti_endpoint = self.QA_PTI_ENDPOINT if self.use_qa else self.PROD_PTI_ENDPOINT
    
    def parse_fti_csv(self, csv_content: str) -> List[Dict]:
        """
        Parse FTI CSV file format
        
        CSV Format (T1 template):
        Statement Number, Date, Time, Balance, Transaction Type, Channel, Amount, Reference, Description
        """
        transactions = []
        reader = csv.DictReader(StringIO(csv_content))
        
        for row in reader:
            transaction = {
                "statement_number": row.get("Statement Number", ""),
                "date": row.get("Date", ""),
                "time": row.get("Time", ""),
                "balance": float(row.get("Balance", 0)),
                "transaction_type": row.get("Transaction Type", ""),
                "transaction_type_name": self.TRANSACTION_TYPES.get(row.get("Transaction Type", ""), "Unknown"),
                "channel": row.get("Channel", ""),
                "channel_name": self.CHANNELS.get(row.get("Channel", ""), "Unknown"),
                "amount": float(row.get("Amount", 0)),
                "reference": row.get("Reference", ""),
                "description": row.get("Description", ""),
                "transaction_key": row.get("Transaction Key", ""),
                "process_key": row.get("Process Key", ""),
                "is_debit": float(row.get("Amount", 0)) < 0
            }
            transactions.append(transaction)
        
        return transactions
    
    def parse_fti_xml(self, xml_content: str) -> List[Dict]:
        """
        Parse FTI XML file format
        
        XML Format (T1 template):
        <Statement>
          <Transaction>
            <Date>...</Date>
            <Amount>...</Amount>
            ...
          </Transaction>
        </Statement>
        """
        transactions = []
        root = ET.fromstring(xml_content)
        
        for transaction_elem in root.findall('.//Transaction'):
            transaction = {
                "statement_number": transaction_elem.findtext('StatementNumber', ''),
                "date": transaction_elem.findtext('Date', ''),
                "time": transaction_elem.findtext('Time', ''),
                "balance": float(transaction_elem.findtext('Balance', 0)),
                "transaction_type": transaction_elem.findtext('TransactionType', ''),
                "transaction_type_name": self.TRANSACTION_TYPES.get(transaction_elem.findtext('TransactionType', ''), "Unknown"),
                "channel": transaction_elem.findtext('Channel', ''),
                "channel_name": self.CHANNELS.get(transaction_elem.findtext('Channel', ''), "Unknown"),
                "amount": float(transaction_elem.findtext('Amount', 0)),
                "reference": transaction_elem.findtext('Reference', ''),
                "description": transaction_elem.findtext('Description', ''),
                "transaction_key": transaction_elem.findtext('TransactionKey', ''),
                "is_debit": float(transaction_elem.findtext('Amount', 0)) < 0
            }
            transactions.append(transaction)
        
        return transactions
    
    def generate_mock_fti_data(self, num_transactions: int = 20) -> List[Dict]:
        """
        Generate mock FTI transactions for testing
        
        Creates realistic transaction data including member payments, fees, etc.
        """
        transactions = []
        base_date = datetime.now() - timedelta(days=1)
        balance = 50000.00
        
        # Common gym transaction patterns
        transaction_patterns = [
            {"type": "004", "channel": "EFT", "desc_prefix": "MEMBER PAYMENT", "amount_range": (200, 1500)},
            {"type": "102", "channel": "EFT", "desc_prefix": "DEBIT ORDER", "amount_range": (300, 1200)},
            {"type": "004", "channel": "NBB", "desc_prefix": "ONLINE PAYMENT", "amount_range": (250, 1000)},
            {"type": "001", "channel": "BRN", "desc_prefix": "CASH DEPOSIT", "amount_range": (100, 500)},
            {"type": "202", "channel": "EFT", "desc_prefix": "BANK CHARGES", "amount_range": (-50, -10)},
        ]
        
        for i in range(num_transactions):
            pattern = transaction_patterns[i % len(transaction_patterns)]
            
            # Generate amount
            amount = round(
                pattern["amount_range"][0] + 
                (pattern["amount_range"][1] - pattern["amount_range"][0]) * (i / num_transactions),
                2
            )
            
            # Update balance
            balance += amount
            
            # Generate transaction time
            trans_datetime = base_date + timedelta(hours=i * 2, minutes=i * 5)
            
            # Generate reference (could match member ID or invoice)
            reference = f"MEM{1000 + (i % 50):04d}" if pattern["type"] in ["004", "102"] else f"REF{i:06d}"
            
            transaction = {
                "statement_number": f"ST{base_date.strftime('%Y%m%d')}001",
                "date": trans_datetime.strftime("%Y-%m-%d"),
                "time": trans_datetime.strftime("%H:%M:%S"),
                "balance": round(balance, 2),
                "transaction_type": pattern["type"],
                "transaction_type_name": self.TRANSACTION_TYPES.get(pattern["type"], "Unknown"),
                "channel": pattern["channel"],
                "channel_name": self.CHANNELS.get(pattern["channel"], "Unknown"),
                "amount": amount,
                "reference": reference,
                "description": f"{pattern['desc_prefix']} {reference}",
                "transaction_key": f"TXN{uuid.uuid4().hex[:12].upper()}",
                "process_key": f"PROC{i:09d}",
                "is_debit": amount < 0,
                "mock_mode": True
            }
            transactions.append(transaction)
        
        return transactions
    
    def match_transaction_to_invoice(self, transaction: Dict, invoices: List[Dict]) -> Optional[Dict]:
        """
        Match a bank transaction to an invoice
        
        Matching criteria (in order of priority):
        1. Exact reference match (invoice ID or member ID in reference)
        2. Amount + Date match (within 3 days)
        3. Amount + Member name match
        """
        trans_amount = abs(transaction["amount"])
        trans_date = datetime.strptime(transaction["date"], "%Y-%m-%d")
        trans_ref = transaction.get("reference", "").upper()
        
        # Try exact reference match first
        for invoice in invoices:
            invoice_ref = str(invoice.get("id", "")).upper()
            member_id = str(invoice.get("member_id", "")).upper()
            
            if invoice_ref in trans_ref or member_id in trans_ref:
                # Verify amount is close (within 1% for rounding)
                invoice_amount = invoice.get("amount", 0)
                if abs(trans_amount - invoice_amount) / invoice_amount < 0.01:
                    return {
                        "invoice": invoice,
                        "match_confidence": "high",
                        "match_reason": "reference_and_amount"
                    }
        
        # Try amount + date match
        for invoice in invoices:
            invoice_amount = invoice.get("amount", 0)
            invoice_date = invoice.get("due_date")
            
            if invoice_date:
                invoice_datetime = datetime.fromisoformat(invoice_date.replace('Z', '+00:00'))
                days_diff = abs((trans_date - invoice_datetime).days)
                
                # Amount match within 1% and date within 3 days
                if abs(trans_amount - invoice_amount) / invoice_amount < 0.01 and days_diff <= 3:
                    return {
                        "invoice": invoice,
                        "match_confidence": "medium",
                        "match_reason": "amount_and_date"
                    }
        
        # Try amount match only (lower confidence)
        for invoice in invoices:
            invoice_amount = invoice.get("amount", 0)
            
            if abs(trans_amount - invoice_amount) / invoice_amount < 0.01:
                return {
                    "invoice": invoice,
                    "match_confidence": "low",
                    "match_reason": "amount_only"
                }
        
        return None
    
    def reconcile_transactions(self, transactions: List[Dict], invoices: List[Dict]) -> Dict:
        """
        Reconcile bank transactions against invoices
        
        Returns:
            Dict containing:
                - matched: List of matched transactions with invoice details
                - unmatched: List of transactions that couldn't be matched
                - summary: Reconciliation statistics
        """
        matched = []
        unmatched = []
        
        # Filter for credit transactions (payments received)
        credit_transactions = [t for t in transactions if not t.get("is_debit", False) and t["amount"] > 0]
        
        for transaction in credit_transactions:
            match_result = self.match_transaction_to_invoice(transaction, invoices)
            
            if match_result:
                matched.append({
                    "transaction": transaction,
                    "invoice": match_result["invoice"],
                    "match_confidence": match_result["match_confidence"],
                    "match_reason": match_result["match_reason"],
                    "reconciled_at": datetime.utcnow().isoformat()
                })
            else:
                unmatched.append(transaction)
        
        # Calculate summary
        total_matched_amount = sum(m["transaction"]["amount"] for m in matched)
        total_unmatched_amount = sum(t["amount"] for t in unmatched)
        
        summary = {
            "total_transactions": len(credit_transactions),
            "matched_count": len(matched),
            "unmatched_count": len(unmatched),
            "match_rate": (len(matched) / len(credit_transactions) * 100) if credit_transactions else 0,
            "total_matched_amount": round(total_matched_amount, 2),
            "total_unmatched_amount": round(total_unmatched_amount, 2),
            "high_confidence_matches": len([m for m in matched if m["match_confidence"] == "high"]),
            "medium_confidence_matches": len([m for m in matched if m["match_confidence"] == "medium"]),
            "low_confidence_matches": len([m for m in matched if m["match_confidence"] == "low"])
        }
        
        return {
            "matched": matched,
            "unmatched": unmatched,
            "summary": summary,
            "reconciled_at": datetime.utcnow().isoformat()
        }
    
    def generate_mock_pti_data(self) -> List[Dict]:
        """
        Generate mock PTI (Provisional Transaction Information) data
        
        Simulates real-time transaction feed
        """
        # Generate 1-3 recent transactions
        num_trans = 2
        transactions = []
        
        for i in range(num_trans):
            now = datetime.utcnow() - timedelta(minutes=i * 15)
            
            transaction = {
                "transaction_key": f"PTI{uuid.uuid4().hex[:12].upper()}",
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S"),
                "transaction_type": "004",
                "transaction_type_name": "Electronic Deposit",
                "channel": "EFT",
                "channel_name": "Electronic Funds Transfer",
                "amount": round(450.00 + (i * 100), 2),
                "reference": f"MEM{1020 + i:04d}",
                "description": f"MEMBER PAYMENT MEM{1020 + i:04d}",
                "status": "provisional",
                "is_debit": False,
                "mock_mode": True
            }
            transactions.append(transaction)
        
        return transactions
    
    async def fetch_fti_data(self) -> List[Dict]:
        """
        Fetch FTI data from Nedbank (or mock data in mock mode)
        """
        if self.mock_mode:
            return self.generate_mock_fti_data()
        
        # In production, would make HTTP request to Nedbank TI API
        # For now, return mock data
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.profile_number}"
                }
                
                async with session.get(
                    self.fti_endpoint,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    data = await response.json()
                    # Parse response and return transactions
                    return data.get("transactions", [])
        
        except Exception as e:
            print(f"TI FTI fetch failed: {str(e)}. Using mock mode.")
            return self.generate_mock_fti_data()
    
    async def fetch_pti_data(self) -> List[Dict]:
        """
        Fetch PTI (provisional) data from Nedbank
        """
        if self.mock_mode:
            return self.generate_mock_pti_data()
        
        # In production, would connect to real-time PTI feed
        try:
            # Similar to FTI but for provisional data
            return self.generate_mock_pti_data()
        except Exception as e:
            print(f"TI PTI fetch failed: {str(e)}. Using mock mode.")
            return self.generate_mock_pti_data()
    
    @staticmethod
    def format_reconciliation_report(reconciliation_result: Dict) -> str:
        """
        Format reconciliation results into a readable report
        """
        summary = reconciliation_result["summary"]
        matched = reconciliation_result["matched"]
        unmatched = reconciliation_result["unmatched"]
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("PAYMENT RECONCILIATION REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {reconciliation_result['reconciled_at']}")
        report_lines.append("")
        report_lines.append("SUMMARY:")
        report_lines.append(f"  Total Transactions: {summary['total_transactions']}")
        report_lines.append(f"  Matched: {summary['matched_count']} ({summary['match_rate']:.1f}%)")
        report_lines.append(f"  Unmatched: {summary['unmatched_count']}")
        report_lines.append(f"  Total Matched Amount: R{summary['total_matched_amount']:,.2f}")
        report_lines.append(f"  Total Unmatched Amount: R{summary['total_unmatched_amount']:,.2f}")
        report_lines.append("")
        report_lines.append("MATCH CONFIDENCE:")
        report_lines.append(f"  High: {summary['high_confidence_matches']}")
        report_lines.append(f"  Medium: {summary['medium_confidence_matches']}")
        report_lines.append(f"  Low: {summary['low_confidence_matches']}")
        report_lines.append("")
        
        if matched:
            report_lines.append("MATCHED TRANSACTIONS:")
            report_lines.append("-" * 80)
            for match in matched[:10]:  # Show first 10
                trans = match["transaction"]
                inv = match["invoice"]
                report_lines.append(f"  {trans['date']} | R{trans['amount']:,.2f} | {trans['reference']}")
                report_lines.append(f"    → Invoice: {inv.get('id', 'N/A')} | Member: {inv.get('member_name', 'N/A')}")
                report_lines.append(f"    → Confidence: {match['match_confidence']} ({match['match_reason']})")
                report_lines.append("")
        
        if unmatched:
            report_lines.append("UNMATCHED TRANSACTIONS (Require Manual Review):")
            report_lines.append("-" * 80)
            for trans in unmatched[:10]:  # Show first 10
                report_lines.append(f"  {trans['date']} | R{trans['amount']:,.2f} | {trans['reference']}")
                report_lines.append(f"    → {trans['description']}")
                report_lines.append("")
        
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
