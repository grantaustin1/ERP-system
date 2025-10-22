"""
EFT SDV (Same Day Value) File Format Utilities
Implements Nedbank CPS format for debit orders and payment reconciliation
"""

from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
import os


class EFTFileGenerator:
    """Generate EFT files in Nedbank CPS format"""
    
    def __init__(self, client_profile_number: str, nominated_account: str, charges_account: str):
        """
        Initialize EFT file generator
        
        Args:
            client_profile_number: 10-digit Nedbank client number
            nominated_account: 16-digit Nedbank account number for credits
            charges_account: 16-digit Nedbank account for fees/charges
        """
        self.client_profile_number = client_profile_number.zfill(10)
        self.nominated_account = nominated_account.zfill(16)
        self.charges_account = charges_account.zfill(16)
    
    def generate_file_sequence_number(self) -> str:
        """
        Generate unique file sequence number
        Format: {ClientProfileNumber (10)}{YYYYMMDD (8)}{Sequential (6)}
        """
        today = datetime.now().strftime('%Y%m%d')
        # In production, this should increment based on files generated today
        # For now, use timestamp-based sequence
        sequence = datetime.now().strftime('%H%M%S')
        return f"{self.client_profile_number}{today}{sequence}"
    
    def format_header_record(self, file_sequence: str, file_type: str = "01", 
                            statement_narrative: str = "DEBIT ORDER") -> str:
        """
        Format EFT file header record (Record Type 01)
        
        Args:
            file_sequence: 24-digit unique file sequence number
            file_type: 01=transaction instructions, 02=disallow instructions
            statement_narrative: Text to appear on statement (max 30 chars)
        
        Returns:
            320-character header record string
        """
        record = []
        record.append("01")  # Record identifier (2)
        record.append(self.client_profile_number)  # Client profile number (10)
        record.append(file_sequence.zfill(24))  # File sequence number (24)
        record.append(file_type.zfill(2))  # File type (2)
        record.append(self.nominated_account)  # Nominated account (16)
        record.append(self.charges_account)  # Charges account (16)
        record.append(statement_narrative.ljust(30)[:30])  # Statement narrative (30)
        record.append(" " * 220)  # Filler (220)
        
        return "".join(record) + "\n"
    
    def format_transaction_record(self, payment_ref: str, dest_branch: str, 
                                 dest_account: str, amount: float, action_date: date,
                                 reference: str, transaction_number: int) -> str:
        """
        Format EFT transaction record (Record Type 02)
        
        Args:
            payment_ref: 34-digit unique payment reference
            dest_branch: 6-digit destination branch code
            dest_account: 16-digit destination account number
            amount: Transaction amount (cents format, e.g., 100.00 = 10000)
            action_date: Date to process transaction
            reference: 30-char reference for statement
            transaction_number: Sequential transaction number
        
        Returns:
            320-character transaction record string
        """
        record = []
        record.append("02")  # Record identifier (2)
        record.append(" " * 16)  # Nominated account override (blank) (16)
        record.append(payment_ref.zfill(34))  # Payment reference (34)
        record.append(dest_branch.zfill(6))  # Destination branch (6)
        record.append(dest_account.zfill(16))  # Destination account (16)
        
        # Amount in cents (12 digits, last 2 are cents)
        amount_cents = int(amount * 100)
        record.append(str(amount_cents).zfill(12))  # Amount (12)
        
        # Action date YYYYMMDD (8)
        record.append(action_date.strftime('%Y%m%d'))
        
        # Reference (30 chars)
        # Format: User reference (10) + Contract reference (14) + Cycle date YYMMDD (6)
        cycle_date = action_date.strftime('%y%m%d')
        user_ref = "GYMDEBIT".ljust(10)[:10]
        contract_ref = str(transaction_number).zfill(14)
        full_reference = user_ref + contract_ref + cycle_date
        record.append(full_reference[:30].ljust(30))
        
        record.append(" " * 196)  # Filler (196)
        
        return "".join(record) + "\n"
    
    def format_trailer_record(self, total_transactions: int, total_value: float) -> str:
        """
        Format EFT file trailer record (Record Type 03)
        
        Args:
            total_transactions: Total number of transaction records
            total_value: Total value of all transactions
        
        Returns:
            320-character trailer record string
        """
        record = []
        record.append("03")  # Record identifier (2)
        record.append(str(total_transactions).zfill(10))  # Total transactions (10)
        
        # Total value in cents (14 digits, last 2 are cents)
        total_cents = int(total_value * 100)
        record.append(str(total_cents).zfill(14))  # Total value (14)
        
        record.append(" " * 294)  # Filler (294)
        
        return "".join(record) + "\n"
    
    def format_security_record(self, hash_total: str = "") -> str:
        """
        Format EFT file security record (Record Type 04)
        
        Args:
            hash_total: Optional hash total for security verification
        
        Returns:
            320-character security record string
        """
        record = []
        record.append("04")  # Record identifier (2)
        record.append(hash_total.ljust(50)[:50])  # Hash total (50)
        record.append(" " * 268)  # Filler (268)
        
        return "".join(record) + "\n"
    
    def generate_debit_order_file(self, transactions: List[Dict]) -> Tuple[str, str]:
        """
        Generate complete EFT debit order file
        
        Args:
            transactions: List of transaction dicts with keys:
                - member_name: Member full name
                - member_account: Bank account number
                - member_branch: Branch code
                - amount: Amount to debit
                - invoice_id: Invoice ID for reference
                - action_date: Date to process (optional, defaults to today)
        
        Returns:
            Tuple of (filename, file_content)
        """
        if not transactions:
            raise ValueError("No transactions provided")
        
        file_sequence = self.generate_file_sequence_number()
        filename = f"EFT_DEBIT_{file_sequence}.txt"
        
        lines = []
        
        # Header record
        lines.append(self.format_header_record(file_sequence, "01", "GYM MEMBERSHIP"))
        
        # Transaction records
        total_value = 0.0
        for idx, txn in enumerate(transactions, 1):
            action_date = txn.get('action_date', date.today())
            if isinstance(action_date, str):
                action_date = datetime.strptime(action_date, '%Y-%m-%d').date()
            
            amount = float(txn['amount'])
            total_value += amount
            
            # Generate payment reference: file_sequence + sequential
            payment_ref = f"{file_sequence}{str(idx).zfill(10)}"
            
            lines.append(self.format_transaction_record(
                payment_ref=payment_ref,
                dest_branch=str(txn.get('member_branch', '000000')),
                dest_account=str(txn.get('member_account', '')),
                amount=amount,
                action_date=action_date,
                reference=txn.get('invoice_id', ''),
                transaction_number=idx
            ))
        
        # Trailer record
        lines.append(self.format_trailer_record(len(transactions), total_value))
        
        # Security record
        lines.append(self.format_security_record())
        
        file_content = "".join(lines)
        
        return filename, file_content


class EFTFileParser:
    """Parse incoming EFT response files from bank"""
    
    @staticmethod
    def parse_response_file(file_content: str) -> Dict:
        """
        Parse EFT response file (ACK, NACK, or Unpaid)
        
        Args:
            file_content: Raw file content string
        
        Returns:
            Dict with parsed response data
        """
        lines = file_content.strip().split('\n')
        
        if not lines:
            raise ValueError("Empty file content")
        
        # Parse header
        header = EFTFileParser.parse_header_record(lines[0])
        
        # Parse transaction responses
        transactions = []
        for line in lines[1:]:
            if not line.strip():
                continue
            
            record_type = line[0:2]
            
            if record_type == "02":  # Transaction record
                txn = EFTFileParser.parse_transaction_response(line)
                transactions.append(txn)
            elif record_type == "03":  # Trailer
                _ = EFTFileParser.parse_trailer_record(line)  # Parse but don't need to use
            elif record_type == "04":  # Security
                pass  # Skip security record
        
        return {
            "header": header,
            "transactions": transactions,
            "total_count": len(transactions)
        }
    
    @staticmethod
    def parse_header_record(line: str) -> Dict:
        """Parse header record"""
        if len(line) < 100:
            raise ValueError("Invalid header record length")
        
        return {
            "record_type": line[0:2],
            "client_profile": line[2:12].strip(),
            "file_sequence": line[12:36].strip(),
            "file_type": line[36:38].strip(),
            "nominated_account": line[38:54].strip(),
            "charges_account": line[54:70].strip(),
            "statement_narrative": line[70:100].strip()
        }
    
    @staticmethod
    def parse_transaction_response(line: str) -> Dict:
        """Parse transaction response record"""
        if len(line) < 120:
            raise ValueError("Invalid transaction record length")
        
        # Parse payment reference to extract original invoice/member info
        payment_ref = line[18:52].strip()
        
        # Parse amount (12 digits, last 2 are cents)
        amount_str = line[74:86].strip()
        amount = float(amount_str) / 100.0 if amount_str else 0.0
        
        # Parse action date YYYYMMDD
        action_date_str = line[86:94].strip()
        action_date = None
        if action_date_str and len(action_date_str) == 8:
            action_date = datetime.strptime(action_date_str, '%Y%m%d').date()
        
        return {
            "record_type": line[0:2],
            "payment_reference": payment_ref,
            "dest_branch": line[52:58].strip(),
            "dest_account": line[58:74].strip(),
            "amount": amount,
            "action_date": action_date,
            "reference": line[94:124].strip() if len(line) >= 124 else "",
            "status": "processed"  # Default status, override based on file type
        }
    
    @staticmethod
    def parse_trailer_record(line: str) -> Dict:
        """Parse trailer record"""
        if len(line) < 26:
            raise ValueError("Invalid trailer record length")
        
        total_txn = line[2:12].strip()
        total_value_str = line[12:26].strip()
        
        return {
            "total_transactions": int(total_txn) if total_txn else 0,
            "total_value": float(total_value_str) / 100.0 if total_value_str else 0.0
        }


def save_eft_file(filename: str, content: str, folder: str = "/app/eft_files") -> str:
    """
    Save EFT file to specified folder
    
    Args:
        filename: Name of the file
        content: File content
        folder: Folder path to save file
    
    Returns:
        Full path to saved file
    """
    os.makedirs(folder, exist_ok=True)
    
    # Create subfolders for organization
    outgoing_folder = os.path.join(folder, "outgoing")
    os.makedirs(outgoing_folder, exist_ok=True)
    
    filepath = os.path.join(outgoing_folder, filename)
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    return filepath


def setup_eft_folders(base_folder: str = "/app/eft_files") -> Dict[str, str]:
    """
    Setup EFT folder structure
    
    Returns:
        Dict with folder paths
    """
    folders = {
        "base": base_folder,
        "outgoing": os.path.join(base_folder, "outgoing"),
        "incoming": os.path.join(base_folder, "incoming"),
        "processed": os.path.join(base_folder, "processed"),
        "failed": os.path.join(base_folder, "failed")
    }
    
    for folder in folders.values():
        os.makedirs(folder, exist_ok=True)
    
    return folders
