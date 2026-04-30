"""
Supplier Communicator Agent

Sends purchase orders (POs) to suppliers via email (SMTP) or mock API.
Tracks confirmation status and delivery updates.
"""

from typing import Dict, Optional
import re
import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

logger = logging.getLogger(__name__)

# Security: Validate PO ID to prevent path traversal
_PO_ID_PATTERN = re.compile(r'^[A-Z0-9_-]+$')
POS_DIR = Path(__file__).parent.parent / "data" / "pos"
POS_DIR.mkdir(exist_ok=True, parents=True)

def _validate_po_id(po_id: str) -> bool:
    """
    Validate PO ID to prevent path traversal attacks.
    
    Args:
        po_id: Purchase order ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    return bool(_PO_ID_PATTERN.match(po_id))

def _safe_po_path(po_id: str) -> Path:
    """
    Get safe file path for PO, ensuring no path traversal.
    
    Args:
        po_id: Validated PO ID
        
    Returns:
        Safe Path object within POS_DIR
        
    Raises:
        ValueError: If PO ID is invalid or path traversal detected
    """
    if not _validate_po_id(po_id):
        raise ValueError(f"Invalid PO ID format: {po_id}")
    
    po_file = (POS_DIR / po_id).with_suffix('.json')
    
    # Ensure the resolved path is within POS_DIR
    try:
        po_file.resolve().relative_to(POS_DIR.resolve())
    except ValueError:
        raise ValueError(f"Path traversal attempt detected in PO ID: {po_id}")
    
    return po_file


def send_po_email(po: Dict) -> bool:
    """
    Sends a purchase order to a supplier via email.

    Args:
        po: Purchase order dictionary containing supplier, items, totals, etc.

    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Load SMTP settings from environment variables
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT", 587))
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")
        smtp_from = os.getenv("SMTP_FROM", smtp_username)

        # If SMTP not configured, log and return mock success for demo
        if not all([smtp_server, smtp_username, smtp_password]):
            logger.warning("SMTP settings not configured. Mock email send successful.")
            return True

        # Determine recipient email based on supplier
        supplier_email_map = {
            "Metcash": "orders@metcash.com",
            "PFD Food Services": "orders@pfdfood.com.au",
            "Toll Group": "logistics@tollgroup.com",
            "CEVA Logistics": "operations@cevalogistics.com"
        }
        recipient = supplier_email_map.get(po["supplier"], f"orders@{po['supplier'].lower().replace(' ', '_')}.com")

        # Create email message
        msg = MIMEMultipart()
        msg["From"] = smtp_from
        msg["To"] = recipient
        msg["Subject"] = f"Purchase Order {po['po_id']} - {po['supplier']}"

        # Build email body
        body = f"""
       Dear {po['supplier']} Team,

       Please find the attached purchase order for our store(s).

        Purchase Order Details:
        PO ID: {po['po_id']}
        Stores: {', '.join(po['store_ids'])}
        Delivery Date: {po['delivery_date']}

        Items:
        """
        for item in po["items"]:
            body += f"\n  - {item['name']} ({item['sku_id']}): {item['quantity']} units @ ${item['unit_cost']:.2f} = ${item['total']:.2f}"
            if item.get("discount", 0) > 0:
                body += f" (discount: {item['discount']*100:.0f}%)"

        body += f"\n\nTotal Quantity: {po.get('total_quantity', sum(i['quantity'] for i in po['items']))}"
        body += f"\nTotal Cost: ${po['total_cost']:.2f}"
        if po.get("bulk_discount_applied", 0) > 0:
            body += f"\nBulk Discount Applied: {po['bulk_discount_applied'] * 100:.0f}%"
        body += f"\n\nPlease confirm receipt and estimated delivery.\n\nBest regards,\nInventory Management System"

        msg.attach(MIMEText(body, "plain"))

        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)

        logger.info(
            "PO sent via email",
            extra={
                "po_id": po["po_id"],
                "supplier": po["supplier"],
                "recipient": recipient,
                "sensitive": False,
            },
        )
        return True

    except Exception as e:
        logger.error(
            "Failed to send PO via email",
            extra={
                "po_id": po.get("po_id", "N/A"),
                "error": str(e),
                "sensitive": False,
            },
            exc_info=True,
        )
        return False


def send_po_api(po: Dict, api_url: str = None, api_key: str = None) -> bool:
    """
    Sends a purchase order to a supplier via mock API.

    Args:
        po: Purchase order dictionary
        api_url: Optional API endpoint URL
        api_key: Optional API key for authentication

    Returns:
        True if API call succeeded, False otherwise
    """
    try:
        import requests

        # Determine API endpoint based on supplier
        if not api_url:
            supplier_endpoints = {
                "Metcash": "http://localhost:8001/metcash/order/",
                "PFD Food Services": "http://localhost:8001/pfd/order/",
            }
            api_url = supplier_endpoints.get(po["supplier"], "http://localhost:8001/order/")

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        # Prepare payload
        payload = {
            "po_id": po["po_id"],
            "store_ids": po["store_ids"],
            "supplier": po["supplier"],
            "items": po["items"],
            "total_cost": po["total_cost"],
            "delivery_date": po["delivery_date"],
        }

        response = requests.post(api_url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()

        logger.info(
            "PO sent via API",
            extra={
                "po_id": po["po_id"],
                "supplier": po["supplier"],
                "status_code": response.status_code,
                "sensitive": False,
            },
        )
        return True

    except ImportError:
        logger.warning("requests library not available. Mock API call successful.")
        return True
    except Exception as e:
        logger.error(
            "Failed to send PO via API",
            extra={
                "po_id": po.get("po_id", "N/A"),
                "error": str(e),
                "sensitive": False,
            },
        )
        return False


def send_po(po: Dict, method: str = "email", **kwargs) -> bool:
    """
    Sends a PO using the specified method.

    Args:
        po: Purchase order dictionary
        method: "email" or "api"
        **kwargs: Additional arguments passed to the specific sender

    Returns:
        True if successful, False otherwise
    """
    if method.lower() == "email":
        return send_po_email(po)
    elif method.lower() == "api":
        return send_po_api(po, **kwargs)
    else:
        logger.error("Unsupported PO sending method: %s", method)
        return False


def track_po_status(po_id: str) -> Dict:
    """
    Tracks the status of a sent PO (mock implementation).

    In production, this would query supplier systems or email for confirmations.

    Args:
        po_id: Purchase order ID

    Returns:
        Dict with status information

    Raises:
        ValueError: If PO ID format is invalid
    """
    if not _validate_po_id(po_id):
        raise ValueError(f"Invalid PO ID format: {po_id}")

    try:
        # In a real system, we'd check a database of sent POs and responses
        # For demo, return a mock status
        import random

        return {
            "po_id": po_id,
            "status": "confirmed",
            "delivery_date": "2026-05-03",
            "tracking_number": f"TRK{random.randint(100000, 999999)}",
            "carrier": "Australia Post",
        }
    except Exception as e:
        logger.error(
            "Failed to track PO",
            extra={
                "po_id": po_id,
                "error": str(e),
                "sensitive": False,
            },
            exc_info=True,
        )
        return {"po_id": po_id, "status": "unknown", "error": str(e)}
