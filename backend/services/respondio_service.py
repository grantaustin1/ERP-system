"""
Respond.io WhatsApp Integration Service
Handles WhatsApp messaging through respond.io platform
"""
import os
import aiohttp
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class RespondIOService:
    """Service for interacting with respond.io WhatsApp API"""
    
    def __init__(self):
        self.api_key = os.getenv("RESPOND_IO_API_KEY")
        self.base_url = os.getenv("RESPOND_IO_BASE_URL", "https://api.respond.io/v2")
        self.channel_id = os.getenv("WHATSAPP_CHANNEL_ID")
        
        if not self.api_key:
            logger.warning("RESPOND_IO_API_KEY not set - WhatsApp integration will be mocked")
            self.is_mocked = True
        else:
            self.is_mocked = False
        
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        } if self.api_key else {}
    
    def format_phone_number(self, phone: str) -> str:
        """
        Format phone number to E.164 standard for South African numbers
        
        Examples:
            "0821234567" -> "+27821234567"
            "27821234567" -> "+27821234567"
            "+27821234567" -> "+27821234567"
            "082 123 4567" -> "+27821234567"
        """
        # Remove all non-digit characters
        clean_number = ''.join(filter(str.isdigit, phone))
        
        # Handle leading zero (South African format)
        if clean_number.startswith('0'):
            clean_number = '27' + clean_number[1:]
        
        # Ensure country code is present
        if not clean_number.startswith('27'):
            clean_number = '27' + clean_number
        
        # Add + prefix
        formatted = f"+{clean_number}"
        
        # Validate length (SA numbers are 11 digits including country code)
        if len(clean_number) != 11:
            logger.warning(f"Phone number {phone} may be invalid (formatted: {formatted})")
        
        return formatted
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None
    ) -> Dict:
        """Make async HTTP request to respond.io API with retry logic"""
        if self.is_mocked:
            logger.info(f"[MOCK] Would send {method} to {endpoint} with data: {data}")
            return {"status": "mocked", "messageId": "mock-msg-id-123"}
        
        url = f"{self.base_url}/{endpoint}"
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method=method,
                        url=url,
                        headers=self.headers,
                        json=data,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        response.raise_for_status()
                        return await response.json()
            except aiohttp.ClientError as e:
                if attempt == max_retries - 1:
                    logger.error(f"API request failed after {max_retries} attempts: {str(e)}")
                    raise
                
                import asyncio
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{max_retries}), "
                    f"retrying in {wait_time}s: {str(e)}"
                )
                await asyncio.sleep(wait_time)
            except Exception as e:
                logger.error(f"Unexpected error during API request: {str(e)}")
                raise
    
    async def create_or_update_contact(
        self,
        phone: str,
        first_name: str,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        custom_fields: Optional[Dict] = None
    ) -> Dict:
        """Create or update a contact in respond.io"""
        formatted_phone = self.format_phone_number(phone)
        
        payload = {
            "phone": formatted_phone,
            "firstName": first_name,
        }
        
        if last_name:
            payload["lastName"] = last_name
        if email:
            payload["email"] = email
        if custom_fields:
            payload["customFields"] = custom_fields
        
        # Use phone as identifier for create/update
        identifier = f"phone:{formatted_phone}"
        
        try:
            result = await self._make_request(
                "POST",
                f"contact/{identifier}",
                payload
            )
            logger.info(f"Contact created/updated: {identifier}")
            return result
        except Exception as e:
            logger.error(f"Failed to create/update contact {identifier}: {str(e)}")
            raise
    
    async def send_whatsapp_message(
        self,
        contact_phone: str,
        template_name: str,
        template_params: List[str],
        template_language: str = "en",
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None
    ) -> Dict:
        """
        Send a WhatsApp message using an approved template
        
        Args:
            contact_phone: Recipient phone number (will be formatted to E.164)
            template_name: Name of the approved template
            template_params: List of parameter values for template variables
            template_language: Template language code (default: en)
            first_name: Contact first name (for contact creation)
            last_name: Contact last name (optional)
            email: Contact email (optional)
            
        Returns:
            API response containing message ID and status
        """
        formatted_phone = self.format_phone_number(contact_phone)
        contact_identifier = f"phone:{formatted_phone}"
        
        # Ensure contact exists first
        if first_name:
            try:
                await self.create_or_update_contact(
                    phone=formatted_phone,
                    first_name=first_name,
                    last_name=last_name,
                    email=email
                )
            except Exception as e:
                logger.warning(f"Failed to create contact, proceeding with message: {str(e)}")
        
        payload = {
            "contactId": contact_identifier,
            "channelId": self.channel_id,
            "message": {
                "type": "whatsapp_template",
                "template": {
                    "name": template_name,
                    "language": template_language,
                    "parameters": template_params
                }
            }
        }
        
        try:
            result = await self._make_request(
                "POST",
                "message/send",
                payload
            )
            
            message_id = result.get('messageId', 'unknown')
            logger.info(
                f"WhatsApp message sent to {formatted_phone} "
                f"using template {template_name}, message ID: {message_id}"
            )
            return result
        except Exception as e:
            logger.error(
                f"Failed to send WhatsApp message to {formatted_phone}: {str(e)}"
            )
            raise
    
    async def list_message_templates(self, channel_id: Optional[str] = None) -> List[Dict]:
        """List all approved message templates for a channel"""
        if self.is_mocked:
            logger.info("[MOCK] Would list message templates")
            return [
                {"name": "payment_failed_alert", "status": "APPROVED"},
                {"name": "member_welcome", "status": "APPROVED"},
                {"name": "membership_renewal_reminder", "status": "APPROVED"}
            ]
        
        channel = channel_id or self.channel_id
        
        try:
            response = await self._make_request(
                "GET",
                f"space/channel/{channel}/template"
            )
            
            # Filter for approved templates only
            approved_templates = [
                t for t in response.get('data', [])
                if t.get('status') == 'APPROVED'
            ]
            
            logger.info(f"Retrieved {len(approved_templates)} approved templates")
            return approved_templates
        except Exception as e:
            logger.error(f"Failed to list message templates: {str(e)}")
            raise
