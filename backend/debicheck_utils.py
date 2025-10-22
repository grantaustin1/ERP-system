"""
DebiCheck Mandate and Collection Management Utilities
Implements Nedbank CPS DebiCheck format for authenticated debit orders
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
import uuid
import os


class DebiCheckMandateGenerator:
    """Generate DebiCheck mandate requests in Nedbank CPS format"""
    
    # Mandate types
    MANDATE_TYPE_FIXED = "F"
    MANDATE_TYPE_VARIABLE = "V"
    MANDATE_TYPE_USAGE_BASED = "U"
    
    # Transaction types
    TT_REAL_TIME = "TT1"
    TT_BATCH = "TT2"
    TT_CARD_PIN = "TT3"
    
    # Adjustment categories
    ADJ_NEVER = "0"
    ADJ_QUARTERLY = "1"
    ADJ_BIANNUALLY = "2"
    ADJ_ANNUALLY = "3"
    ADJ_REPO_RATE = "4"
    
    # Frequency codes
    FREQ_WEEKLY = "W"
    FREQ_FORTNIGHTLY = "F"
    FREQ_MONTHLY = "M"
    FREQ_QUARTERLY = "Q"
    FREQ_BIANNUALLY = "H"
    FREQ_ANNUALLY = "Y"
    
    def __init__(self, client_profile_number: str, creditor_name: str, creditor_abbr: str):
        """
        Initialize DebiCheck mandate generator
        
        Args:
            client_profile_number: 10-digit Nedbank client number
            creditor_name: Full creditor/payee name (max 30 chars)
            creditor_abbr: Abbreviated name for statements (max 10 chars)
        """
        self.client_profile_number = client_profile_number.zfill(10)
        self.creditor_name = creditor_name[:30].ljust(30)
        self.creditor_abbr = creditor_abbr[:10].ljust(10)
    
    def generate_mandate_reference_number(self, member_id: str) -> str:
        """
        Generate unique Mandate Reference Number (MRN)
        Format: {BankNumber(4)}{CreationDate(8)}{FreeFormat(13)}
        Must be unique industry-wide for mandate lifetime
        """
        bank_number = "1058"  # Nedbank universal branch code
        creation_date = datetime.now().strftime('%Y%m%d')
        free_format = f"{member_id[:7]}{str(uuid.uuid4())[:6]}"
        return f"{bank_number}{creation_date}{free_format[:13].zfill(13)}"
    
    def format_mandate_header(self, file_sequence: str) -> str:
        """
        Format DebiCheck mandate file header record
        
        Args:
            file_sequence: 24-digit unique file sequence number
        
        Returns:
            320-character header record string
        """
        record = []
        record.append("01")  # Record identifier (2)
        record.append(self.client_profile_number)  # Client profile number (10)
        record.append(file_sequence.zfill(24))  # File sequence number (24)
        record.append("03")  # File type: 03=Mandate Request (2)
        record.append(" " * 16)  # Nominated account (not used for mandates) (16)
        record.append(" " * 16)  # Charges account (not used for mandates) (16)
        record.append(self.creditor_name)  # Statement narrative (30)
        record.append(" " * 222)  # Filler (222)
        
        return "".join(record) + "\n"
    
    def format_mandate_request(self, mandate_data: Dict, transaction_number: int) -> str:
        """
        Format DebiCheck mandate request record
        
        Args:
            mandate_data: Dict containing mandate details:
                - mandate_type: "F" (Fixed), "V" (Variable), "U" (Usage-based)
                - transaction_type: "TT1", "TT2", "TT3"
                - contract_reference: 14-char contract/policy number
                - debtor_name: Payer full name
                - debtor_id_number: SA ID or passport
                - debtor_bank_account: 16-digit account number
                - debtor_branch_code: 6-digit branch code
                - first_collection_date: Date for first collection
                - collection_day: Day of month (1-31)
                - frequency: "M", "Q", "Y", etc.
                - installment_amount: Regular collection amount
                - maximum_amount: Maximum allowed (1.5x installment for variable)
                - adjustment_category: "0"-"4"
                - adjustment_rate: Percentage if applicable
            transaction_number: Sequential transaction number
        
        Returns:
            320-character mandate request record string
        """
        record = []
        
        # Record identifier
        record.append("02")  # (2)
        
        # Action indicator: A=Add, C=Cancel, U=Update
        record.append(mandate_data.get('action', 'A'))  # (1)
        
        # Mandate reference number (MRN) - unique identifier
        mrn = mandate_data.get('mandate_reference_number', '')
        record.append(mrn.ljust(25)[:25])  # (25)
        
        # Creditor abbreviation (appears on statement)
        record.append(self.creditor_abbr)  # (10)
        
        # Contract reference
        contract_ref = mandate_data.get('contract_reference', '')
        record.append(contract_ref.ljust(14)[:14])  # (14)
        
        # Debtor account number
        debtor_account = mandate_data.get('debtor_bank_account', '').zfill(16)
        record.append(debtor_account[:16])  # (16)
        
        # Debtor branch code
        debtor_branch = mandate_data.get('debtor_branch_code', '').zfill(6)
        record.append(debtor_branch[:6])  # (6)
        
        # Debtor account type: 1=Current, 2=Savings, 3=Transmission
        account_type = mandate_data.get('account_type', '1')
        record.append(account_type)  # (1)
        
        # Mandate type: F=Fixed, V=Variable, U=Usage-based
        mandate_type = mandate_data.get('mandate_type', 'F')
        record.append(mandate_type)  # (1)
        
        # Debtor ID number (13 digits for SA ID)
        debtor_id = mandate_data.get('debtor_id_number', '').zfill(13)
        record.append(debtor_id[:13])  # (13)
        
        # Debtor full name
        debtor_name = mandate_data.get('debtor_name', '')
        record.append(debtor_name.ljust(30)[:30])  # (30)
        
        # First collection date YYYYMMDD
        first_date = mandate_data.get('first_collection_date', date.today())
        if isinstance(first_date, str):
            first_date = datetime.strptime(first_date, '%Y-%m-%d').date()
        record.append(first_date.strftime('%Y%m%d'))  # (8)
        
        # Collection day (1-31)
        collection_day = str(mandate_data.get('collection_day', first_date.day)).zfill(2)
        record.append(collection_day)  # (2)
        
        # Collection frequency
        frequency = mandate_data.get('frequency', 'M')
        record.append(frequency)  # (1)
        
        # Installment amount in cents (12 digits)
        installment = int(float(mandate_data.get('installment_amount', 0)) * 100)
        record.append(str(installment).zfill(12))  # (12)
        
        # Maximum amount in cents (12 digits)
        maximum = int(float(mandate_data.get('maximum_amount', installment * 1.5)) * 100)
        record.append(str(maximum).zfill(12))  # (12)
        
        # Adjustment category: 0=Never, 1=Quarterly, 2=Biannually, 3=Annually, 4=Repo
        adjustment_cat = mandate_data.get('adjustment_category', '0')
        record.append(adjustment_cat)  # (1)
        
        # Adjustment rate (5.2 format: 3 digits + 2 decimals)
        adjustment_rate = mandate_data.get('adjustment_rate', 0)
        adj_rate_cents = int(float(adjustment_rate) * 100)
        record.append(str(adj_rate_cents).zfill(5))  # (5)
        
        # Transaction type: TT1=Real-time, TT2=Batch, TT3=Card&Pin
        transaction_type = mandate_data.get('transaction_type', 'TT2')
        record.append(transaction_type.ljust(3)[:3])  # (3)
        
        # Tracking indicator: T=Cancel in tracking, F=Don't cancel
        tracking = mandate_data.get('tracking_indicator', 'F')
        record.append(tracking)  # (1)
        
        # Filler
        record.append(" " * 142)  # (142)
        
        return "".join(record) + "\n"
    
    def format_trailer_record(self, total_transactions: int) -> str:
        """
        Format DebiCheck mandate file trailer record
        
        Args:
            total_transactions: Total number of mandate records
        
        Returns:
            320-character trailer record string
        """
        record = []
        record.append("03")  # Record identifier (2)
        record.append(str(total_transactions).zfill(10))  # Total transactions (10)
        record.append(" " * 14)  # Total value not used for mandates (14)
        record.append(" " * 294)  # Filler (294)
        
        return "".join(record) + "\n"
    
    def format_security_record(self) -> str:
        """Format security record"""
        record = []
        record.append("04")  # Record identifier (2)
        record.append(" " * 50)  # Hash total (50)
        record.append(" " * 268)  # Filler (268)
        
        return "".join(record) + "\n"
    
    def generate_mandate_file(self, mandates: List[Dict]) -> Tuple[str, str]:
        """
        Generate complete DebiCheck mandate request file
        
        Args:
            mandates: List of mandate data dictionaries
        
        Returns:
            Tuple of (filename, file_content)
        """
        if not mandates:
            raise ValueError("No mandates provided")
        
        # Generate file sequence
        today = datetime.now().strftime('%Y%m%d')
        sequence = datetime.now().strftime('%H%M%S')
        file_sequence = f"{self.client_profile_number}{today}{sequence}"
        
        filename = f"DEBICHECK_MANDATE_{file_sequence}.txt"
        
        lines = []
        
        # Header record
        lines.append(self.format_mandate_header(file_sequence))
        
        # Mandate records
        for idx, mandate in enumerate(mandates, 1):
            # Generate MRN if not provided
            if 'mandate_reference_number' not in mandate:
                mandate['mandate_reference_number'] = self.generate_mandate_reference_number(
                    mandate.get('member_id', str(idx))
                )
            
            lines.append(self.format_mandate_request(mandate, idx))
        
        # Trailer record
        lines.append(self.format_trailer_record(len(mandates)))
        
        # Security record
        lines.append(self.format_security_record())
        
        file_content = "".join(lines)
        
        return filename, file_content


class DebiCheckCollectionGenerator:
    """Generate DebiCheck collection request files"""
    
    def __init__(self, client_profile_number: str, creditor_abbr: str):
        self.client_profile_number = client_profile_number.zfill(10)
        self.creditor_abbr = creditor_abbr[:10].ljust(10)
    
    def format_collection_header(self, file_sequence: str, nominated_account: str, 
                                 charges_account: str) -> str:
        """Format collection request header"""
        record = []
        record.append("01")  # Record identifier (2)
        record.append(self.client_profile_number)  # Client profile (10)
        record.append(file_sequence.zfill(24))  # File sequence (24)
        record.append("04")  # File type: 04=DebiCheck Collection (2)
        record.append(nominated_account.zfill(16))  # Nominated account (16)
        record.append(charges_account.zfill(16))  # Charges account (16)
        record.append("DEBICHECK COLL".ljust(30))  # Statement narrative (30)
        record.append(" " * 222)  # Filler (222)
        
        return "".join(record) + "\n"
    
    def format_collection_request(self, collection_data: Dict, transaction_number: int) -> str:
        """
        Format DebiCheck collection request record
        
        Args:
            collection_data: Dict with collection details:
                - mandate_reference_number: MRN from original mandate
                - contract_reference: Contract number
                - collection_amount: Amount to collect
                - action_date: Date for collection
                - collection_type: "R"=Recurring, "F"=Final, "O"=Once-off
        """
        record = []
        
        record.append("02")  # Record identifier (2)
        
        # Mandate reference number (must match existing mandate)
        mrn = collection_data.get('mandate_reference_number', '')
        record.append(mrn.ljust(25)[:25])  # (25)
        
        # Contract reference
        contract_ref = collection_data.get('contract_reference', '')
        record.append(contract_ref.ljust(14)[:14])  # (14)
        
        # Collection amount in cents
        amount = int(float(collection_data.get('collection_amount', 0)) * 100)
        record.append(str(amount).zfill(12))  # (12)
        
        # Action date YYYYMMDD
        action_date = collection_data.get('action_date', date.today())
        if isinstance(action_date, str):
            action_date = datetime.strptime(action_date, '%Y-%m-%d').date()
        record.append(action_date.strftime('%Y%m%d'))  # (8)
        
        # Collection type: R=Recurring, F=Final, O=Once-off
        collection_type = collection_data.get('collection_type', 'R')
        record.append(collection_type)  # (1)
        
        # User reference (creditor abbreviation)
        record.append(self.creditor_abbr)  # (10)
        
        # Filler
        record.append(" " * 248)  # (248)
        
        return "".join(record) + "\n"
    
    def generate_collection_file(self, collections: List[Dict], nominated_account: str,
                                charges_account: str) -> Tuple[str, str]:
        """Generate complete DebiCheck collection request file"""
        if not collections:
            raise ValueError("No collections provided")
        
        # Generate file sequence
        today = datetime.now().strftime('%Y%m%d')
        sequence = datetime.now().strftime('%H%M%S')
        file_sequence = f"{self.client_profile_number}{today}{sequence}"
        
        filename = f"DEBICHECK_COLLECTION_{file_sequence}.txt"
        
        lines = []
        
        # Header
        lines.append(self.format_collection_header(file_sequence, nominated_account, charges_account))
        
        # Collection records
        total_amount = 0
        for idx, collection in enumerate(collections, 1):
            lines.append(self.format_collection_request(collection, idx))
            total_amount += float(collection.get('collection_amount', 0))
        
        # Trailer
        record = []
        record.append("03")
        record.append(str(len(collections)).zfill(10))
        record.append(str(int(total_amount * 100)).zfill(14))
        record.append(" " * 294)
        lines.append("".join(record) + "\n")
        
        # Security
        lines.append("04" + " " * 318 + "\n")
        
        return filename, "".join(lines)


class DebiCheckResponseParser:
    """Parse DebiCheck mandate and collection response files"""
    
    @staticmethod
    def parse_mandate_response(file_content: str) -> Dict:
        """Parse mandate response file (approved/rejected mandates)"""
        lines = file_content.strip().split('\n')
        
        responses = []
        for line in lines[1:]:  # Skip header
            if not line.strip() or line[0:2] not in ['02']:
                continue
            
            # Parse mandate response record
            mandate_ref = line[3:28].strip()
            status = line[28:29]  # A=Approved, R=Rejected, P=Pending
            reason_code = line[29:33].strip() if len(line) > 33 else ""
            
            responses.append({
                'mandate_reference_number': mandate_ref,
                'status': status,
                'reason_code': reason_code,
                'status_description': DebiCheckResponseParser.get_status_description(status),
                'reason_description': DebiCheckResponseParser.get_reason_description(reason_code)
            })
        
        return {
            'responses': responses,
            'total_count': len(responses)
        }
    
    @staticmethod
    def get_status_description(status: str) -> str:
        """Get status description"""
        statuses = {
            'A': 'Approved',
            'R': 'Rejected',
            'P': 'Pending',
            'C': 'Cancelled',
            'S': 'Suspended'
        }
        return statuses.get(status, 'Unknown')
    
    @staticmethod
    def get_reason_description(reason_code: str) -> str:
        """Get reason code description"""
        reasons = {
            '0001': 'Account closed',
            '0002': 'Account does not exist',
            '0003': 'Insufficient funds',
            '0004': 'Disputed by account holder',
            '0005': 'No response from account holder',
            '0006': 'Rejected by account holder',
            '0007': 'Duplicate mandate',
            '0008': 'Invalid account details',
            '0009': 'Mandate expired',
            '0010': 'Exceeded maximum amount'
        }
        return reasons.get(reason_code, 'Unknown reason')


def save_debicheck_file(filename: str, content: str, file_type: str = "mandate") -> str:
    """
    Save DebiCheck file to appropriate folder
    
    Args:
        filename: Name of file
        content: File content
        file_type: "mandate" or "collection"
    
    Returns:
        Full path to saved file
    """
    base_folder = "/app/debicheck_files"
    os.makedirs(base_folder, exist_ok=True)
    
    # Create subfolders
    outgoing_folder = os.path.join(base_folder, "outgoing", file_type)
    os.makedirs(outgoing_folder, exist_ok=True)
    
    filepath = os.path.join(outgoing_folder, filename)
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    return filepath
