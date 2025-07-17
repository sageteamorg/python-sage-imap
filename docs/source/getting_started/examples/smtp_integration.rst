.. _smtp_integration:

SMTP Integration
================

This example demonstrates how to send emails properly using SMTP with all production requirements including **Message-ID**, proper headers, and standards compliance.

**⚠️ IMPORTANT: This example follows RFC standards for production email sending!**

Overview
--------

You'll learn how to:

- Send emails with proper RFC-compliant headers
- Generate unique Message-IDs correctly
- Handle attachments and multipart messages
- Implement proper authentication and security
- Handle bounces and delivery status
- Integrate with IMAP for sent message handling
- Use templates for consistent messaging
- Implement bulk email sending safely

Prerequisites
-------------

- Python 3.7 or higher
- Python Sage IMAP installed
- Valid SMTP server credentials
- Understanding of email standards (RFC 5322)

Complete Example
----------------

.. code-block:: python

   #!/usr/bin/env python3
   """
   SMTP Integration Example
   
   This example demonstrates proper email sending using SMTP with
   RFC-compliant headers, Message-ID generation, and production standards.
   """
   
   import smtplib
   import logging
   import time
   import uuid
   from datetime import datetime
   from email.mime.multipart import MIMEMultipart
   from email.mime.text import MIMEText
   from email.mime.base import MIMEBase
   from email.mime.image import MIMEImage
   from email import encoders
   from email.utils import formatdate, make_msgid, formataddr
   from typing import List, Dict, Optional, Union, BinaryIO
   from pathlib import Path
   import socket
   import ssl
   
   # IMAP integration
   from sage_imap.services.client import IMAPClient
   from sage_imap.services import IMAPMailboxUIDService
   from sage_imap.helpers.search import IMAPSearchCriteria
   from sage_imap.models.message import MessageSet
   
   # Configure logging
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   
   logger = logging.getLogger(__name__)
   
   
   class ProductionEmailSender:
       """
       Production-ready email sender with RFC compliance and proper headers.
       """
       
       def __init__(self, smtp_config: Dict, imap_config: Dict = None):
           """
           Initialize the email sender with SMTP and optional IMAP configuration.
           
           Args:
               smtp_config: SMTP server configuration
               imap_config: Optional IMAP configuration for sent message handling
           """
           self.smtp_config = smtp_config
           self.imap_config = imap_config
           
           # Email tracking
           self.sent_messages = []
           self.failed_messages = []
           
           # Default headers
           self.default_headers = {
               'X-Mailer': 'Python Sage IMAP Email Sender v1.0',
               'X-Priority': '3',  # Normal priority
               'Importance': 'Normal'
           }
           
       def demonstrate_smtp_operations(self):
           """
           Demonstrate comprehensive SMTP operations with proper standards.
           """
           logger.info("=== SMTP Integration Example ===")
           
           try:
               # Basic email sending
               self.demonstrate_basic_email_sending()
               
               # HTML emails with attachments
               self.demonstrate_html_emails_with_attachments()
               
               # Bulk email sending
               self.demonstrate_bulk_email_sending()
               
               # Email templates
               self.demonstrate_email_templates()
               
               # Advanced headers and tracking
               self.demonstrate_advanced_headers()
               
               # Bounce handling
               self.demonstrate_bounce_handling()
               
               # IMAP integration
               self.demonstrate_imap_integration()
               
               # Production patterns
               self.demonstrate_production_patterns()
               
               logger.info("✓ SMTP integration operations completed successfully")
               
           except Exception as e:
               logger.error(f"❌ SMTP integration operations failed: {e}")
               raise
   
       def demonstrate_basic_email_sending(self):
           """
           Demonstrate basic email sending with proper headers.
           """
           logger.info("--- Basic Email Sending ---")
           
           try:
               # Simple text email
               self.send_simple_text_email()
               
               # Text email with proper headers
               self.send_text_email_with_headers()
               
               # HTML email
               self.send_html_email()
               
               logger.info("  ✓ Basic email sending completed")
               
           except Exception as e:
               logger.error(f"Failed basic email sending: {e}")
   
       def send_simple_text_email(self):
           """
           Send a simple text email with minimal headers.
           """
           logger.info("--- Simple Text Email ---")
           
           try:
               # Create message
               msg = MIMEText("This is a simple text email sent using Python Sage IMAP.")
               
               # Basic headers
               msg['Subject'] = 'Simple Text Email'
               msg['From'] = formataddr(('Sender Name', self.smtp_config['username']))
               msg['To'] = 'recipient@example.com'
               msg['Date'] = formatdate(localtime=True)
               
               # Generate proper Message-ID
               msg['Message-ID'] = make_msgid(domain=self.get_domain_from_email(self.smtp_config['username']))
               
               # Send email
               result = self.send_email(msg)
               
               if result.success:
                   logger.info("  ✓ Simple text email sent successfully")
                   logger.info(f"    Message-ID: {msg['Message-ID']}")
               else:
                   logger.error(f"  ❌ Failed to send simple text email: {result.error_message}")
               
           except Exception as e:
               logger.error(f"Failed to send simple text email: {e}")
   
       def send_text_email_with_headers(self):
           """
           Send a text email with comprehensive headers.
           """
           logger.info("--- Text Email with Proper Headers ---")
           
           try:
               # Create message
               msg = MIMEText("This is a text email with comprehensive RFC-compliant headers.")
               
               # Required headers
               msg['Subject'] = 'Text Email with Proper Headers'
               msg['From'] = formataddr(('Production Sender', self.smtp_config['username']))
               msg['To'] = formataddr(('Recipient Name', 'recipient@example.com'))
               msg['Date'] = formatdate(localtime=True)
               
               # Generate unique Message-ID
               msg['Message-ID'] = make_msgid(domain=self.get_domain_from_email(self.smtp_config['username']))
               
               # Optional but recommended headers
               msg['Reply-To'] = formataddr(('Support Team', 'support@example.com'))
               msg['Return-Path'] = self.smtp_config['username']
               msg['Sender'] = self.smtp_config['username']
               
               # Add custom headers
               msg['X-Mailer'] = self.default_headers['X-Mailer']
               msg['X-Priority'] = self.default_headers['X-Priority']
               msg['Importance'] = self.default_headers['Importance']
               
               # Tracking headers
               msg['X-Email-ID'] = str(uuid.uuid4())
               msg['X-Campaign'] = 'example_campaign'
               
               # MIME version
               msg['MIME-Version'] = '1.0'
               
               # Send email
               result = self.send_email(msg)
               
               if result.success:
                   logger.info("  ✓ Text email with headers sent successfully")
                   logger.info(f"    Message-ID: {msg['Message-ID']}")
                   logger.info(f"    Email-ID: {msg['X-Email-ID']}")
               else:
                   logger.error(f"  ❌ Failed to send text email with headers: {result.error_message}")
               
           except Exception as e:
               logger.error(f"Failed to send text email with headers: {e}")
   
       def send_html_email(self):
           """
           Send an HTML email with proper structure.
           """
           logger.info("--- HTML Email ---")
           
           try:
               # Create HTML content
               html_content = """
               <html>
                 <head>
                   <title>HTML Email Example</title>
                   <style>
                     body { font-family: Arial, sans-serif; }
                     .header { background-color: #f0f0f0; padding: 20px; }
                     .content { padding: 20px; }
                     .footer { background-color: #e0e0e0; padding: 10px; font-size: 12px; }
                   </style>
                 </head>
                 <body>
                   <div class="header">
                     <h1>HTML Email Example</h1>
                   </div>
                   <div class="content">
                     <p>This is an <strong>HTML email</strong> sent using Python Sage IMAP.</p>
                     <p>It includes:</p>
                     <ul>
                       <li>Proper HTML structure</li>
                       <li>CSS styling</li>
                       <li>RFC-compliant headers</li>
                       <li>Unique Message-ID</li>
                     </ul>
                   </div>
                   <div class="footer">
                     <p>Sent by Python Sage IMAP Email Sender</p>
                   </div>
                 </body>
               </html>
               """
               
               # Create message
               msg = MIMEText(html_content, 'html')
               
               # Headers
               msg['Subject'] = 'HTML Email Example'
               msg['From'] = formataddr(('HTML Sender', self.smtp_config['username']))
               msg['To'] = 'recipient@example.com'
               msg['Date'] = formatdate(localtime=True)
               msg['Message-ID'] = make_msgid(domain=self.get_domain_from_email(self.smtp_config['username']))
               
               # Additional headers
               msg['Content-Type'] = 'text/html; charset=utf-8'
               msg['X-Mailer'] = self.default_headers['X-Mailer']
               
               # Send email
               result = self.send_email(msg)
               
               if result.success:
                   logger.info("  ✓ HTML email sent successfully")
                   logger.info(f"    Message-ID: {msg['Message-ID']}")
               else:
                   logger.error(f"  ❌ Failed to send HTML email: {result.error_message}")
               
           except Exception as e:
               logger.error(f"Failed to send HTML email: {e}")
   
       def demonstrate_html_emails_with_attachments(self):
           """
           Demonstrate HTML emails with attachments.
           """
           logger.info("--- HTML Emails with Attachments ---")
           
           try:
               # Multipart email with HTML and attachments
               self.send_multipart_email_with_attachments()
               
               # Email with inline images
               self.send_email_with_inline_images()
               
               # Email with various attachment types
               self.send_email_with_multiple_attachments()
               
               logger.info("  ✓ HTML emails with attachments completed")
               
           except Exception as e:
               logger.error(f"Failed HTML emails with attachments: {e}")
   
       def send_multipart_email_with_attachments(self):
           """
           Send a multipart email with HTML content and attachments.
           """
           logger.info("--- Multipart Email with Attachments ---")
           
           try:
               # Create multipart message
               msg = MIMEMultipart('mixed')
               
               # Headers
               msg['Subject'] = 'Multipart Email with Attachments'
               msg['From'] = formataddr(('Attachment Sender', self.smtp_config['username']))
               msg['To'] = 'recipient@example.com'
               msg['Date'] = formatdate(localtime=True)
               msg['Message-ID'] = make_msgid(domain=self.get_domain_from_email(self.smtp_config['username']))
               
               # Create HTML content
               html_content = """
               <html>
                 <body>
                   <h2>Email with Attachments</h2>
                   <p>This email contains attachments as demonstrated below:</p>
                   <ul>
                     <li>Text file attachment</li>
                     <li>CSV data file</li>
                     <li>PDF document</li>
                   </ul>
                   <p>Please find the attached files.</p>
                 </body>
               </html>
               """
               
               # Attach HTML content
               html_part = MIMEText(html_content, 'html')
               msg.attach(html_part)
               
               # Add text file attachment
               self.add_text_attachment(msg, "Sample text file content for demonstration.", "sample.txt")
               
               # Add CSV attachment
               csv_content = "Name,Email,Department\nJohn Doe,john@example.com,IT\nJane Smith,jane@example.com,HR"
               self.add_text_attachment(msg, csv_content, "data.csv", "text/csv")
               
               # Add binary attachment (simulated PDF)
               pdf_content = b"PDF content placeholder - this would be actual PDF bytes"
               self.add_binary_attachment(msg, pdf_content, "document.pdf", "application/pdf")
               
               # Send email
               result = self.send_email(msg)
               
               if result.success:
                   logger.info("  ✓ Multipart email with attachments sent successfully")
                   logger.info(f"    Message-ID: {msg['Message-ID']}")
               else:
                   logger.error(f"  ❌ Failed to send multipart email: {result.error_message}")
               
           except Exception as e:
               logger.error(f"Failed to send multipart email with attachments: {e}")
   
       def send_email_with_inline_images(self):
           """
           Send an email with inline images.
           """
           logger.info("--- Email with Inline Images ---")
           
           try:
               # Create multipart message
               msg = MIMEMultipart('related')
               
               # Headers
               msg['Subject'] = 'Email with Inline Images'
               msg['From'] = formataddr(('Image Sender', self.smtp_config['username']))
               msg['To'] = 'recipient@example.com'
               msg['Date'] = formatdate(localtime=True)
               msg['Message-ID'] = make_msgid(domain=self.get_domain_from_email(self.smtp_config['username']))
               
               # HTML content with inline image reference
               html_content = """
               <html>
                 <body>
                   <h2>Email with Inline Images</h2>
                   <p>This email contains an inline image:</p>
                   <img src="cid:inline_image" alt="Inline Image" style="max-width: 300px;">
                   <p>The image is embedded directly in the email.</p>
                 </body>
               </html>
               """
               
               # Attach HTML content
               html_part = MIMEText(html_content, 'html')
               msg.attach(html_part)
               
               # Add inline image (simulated)
               # In practice, you would read actual image data
               image_data = b"PNG image data placeholder - this would be actual PNG bytes"
               image_part = MIMEImage(image_data)
               image_part.add_header('Content-ID', '<inline_image>')
               image_part.add_header('Content-Disposition', 'inline', filename='inline_image.png')
               msg.attach(image_part)
               
               # Send email
               result = self.send_email(msg)
               
               if result.success:
                   logger.info("  ✓ Email with inline images sent successfully")
                   logger.info(f"    Message-ID: {msg['Message-ID']}")
               else:
                   logger.error(f"  ❌ Failed to send email with inline images: {result.error_message}")
               
           except Exception as e:
               logger.error(f"Failed to send email with inline images: {e}")
   
       def send_email_with_multiple_attachments(self):
           """
           Send an email with multiple different types of attachments.
           """
           logger.info("--- Email with Multiple Attachments ---")
           
           try:
               # Create multipart message
               msg = MIMEMultipart('mixed')
               
               # Headers
               msg['Subject'] = 'Email with Multiple Attachment Types'
               msg['From'] = formataddr(('Multi-Attachment Sender', self.smtp_config['username']))
               msg['To'] = 'recipient@example.com'
               msg['Date'] = formatdate(localtime=True)
               msg['Message-ID'] = make_msgid(domain=self.get_domain_from_email(self.smtp_config['username']))
               
               # HTML content
               html_content = """
               <html>
                 <body>
                   <h2>Multiple Attachment Types</h2>
                   <p>This email demonstrates various attachment types:</p>
                   <ul>
                     <li><strong>Text files:</strong> .txt, .log</li>
                     <li><strong>Data files:</strong> .csv, .json</li>
                     <li><strong>Documents:</strong> .pdf, .docx</li>
                     <li><strong>Images:</strong> .png, .jpg</li>
                   </ul>
                 </body>
               </html>
               """
               
               html_part = MIMEText(html_content, 'html')
               msg.attach(html_part)
               
               # Add various attachment types
               attachments = [
                   ("log.txt", "Application log file content...", "text/plain"),
                   ("config.json", '{"setting": "value", "enabled": true}', "application/json"),
                   ("report.csv", "Date,Users,Revenue\n2024-01-01,100,5000", "text/csv"),
                   ("image.png", b"PNG image data...", "image/png"),
                   ("document.pdf", b"PDF document data...", "application/pdf")
               ]
               
               for filename, content, content_type in attachments:
                   if isinstance(content, str):
                       self.add_text_attachment(msg, content, filename, content_type)
                   else:
                       self.add_binary_attachment(msg, content, filename, content_type)
               
               # Send email
               result = self.send_email(msg)
               
               if result.success:
                   logger.info("  ✓ Email with multiple attachments sent successfully")
                   logger.info(f"    Message-ID: {msg['Message-ID']}")
                   logger.info(f"    Attachments: {len(attachments)}")
               else:
                   logger.error(f"  ❌ Failed to send email with multiple attachments: {result.error_message}")
               
           except Exception as e:
               logger.error(f"Failed to send email with multiple attachments: {e}")
   
       def add_text_attachment(self, msg: MIMEMultipart, content: str, filename: str, content_type: str = "text/plain"):
           """
           Add a text attachment to the message.
           """
           try:
               attachment = MIMEText(content)
               attachment.add_header('Content-Disposition', 'attachment', filename=filename)
               attachment.add_header('Content-Type', content_type)
               msg.attach(attachment)
           except Exception as e:
               logger.error(f"Failed to add text attachment {filename}: {e}")
   
       def add_binary_attachment(self, msg: MIMEMultipart, content: bytes, filename: str, content_type: str):
           """
           Add a binary attachment to the message.
           """
           try:
               attachment = MIMEBase(*content_type.split('/'))
               attachment.set_payload(content)
               encoders.encode_base64(attachment)
               attachment.add_header('Content-Disposition', 'attachment', filename=filename)
               msg.attach(attachment)
           except Exception as e:
               logger.error(f"Failed to add binary attachment {filename}: {e}")
   
       def demonstrate_bulk_email_sending(self):
           """
           Demonstrate safe bulk email sending with proper throttling.
           """
           logger.info("--- Bulk Email Sending ---")
           
           try:
               # Bulk sending with throttling
               self.send_bulk_emails_with_throttling()
               
               # Personalized bulk emails
               self.send_personalized_bulk_emails()
               
               # Bulk sending with error handling
               self.send_bulk_emails_with_error_handling()
               
               logger.info("  ✓ Bulk email sending completed")
               
           except Exception as e:
               logger.error(f"Failed bulk email sending: {e}")
   
       def send_bulk_emails_with_throttling(self):
           """
           Send bulk emails with proper throttling to avoid server limits.
           """
           logger.info("--- Bulk Emails with Throttling ---")
           
           try:
               # Recipients list
               recipients = [
                   {'email': 'user1@example.com', 'name': 'User One'},
                   {'email': 'user2@example.com', 'name': 'User Two'},
                   {'email': 'user3@example.com', 'name': 'User Three'},
                   {'email': 'user4@example.com', 'name': 'User Four'},
                   {'email': 'user5@example.com', 'name': 'User Five'}
               ]
               
               # Bulk sending configuration
               batch_size = 2  # Send 2 emails per batch
               delay_between_batches = 1.0  # 1 second delay between batches
               
               logger.info(f"  📧 Sending to {len(recipients)} recipients in batches of {batch_size}")
               
               successful_sends = 0
               failed_sends = 0
               
               # Process in batches
               for i in range(0, len(recipients), batch_size):
                   batch = recipients[i:i + batch_size]
                   
                   logger.info(f"    Processing batch {i//batch_size + 1}: {len(batch)} recipients")
                   
                   # Send to each recipient in the batch
                   for recipient in batch:
                       try:
                           # Create personalized message
                           msg = MIMEText(f"Hello {recipient['name']},\n\nThis is a bulk email sent to you.")
                           
                           # Headers
                           msg['Subject'] = 'Bulk Email Notification'
                           msg['From'] = formataddr(('Bulk Sender', self.smtp_config['username']))
                           msg['To'] = formataddr((recipient['name'], recipient['email']))
                           msg['Date'] = formatdate(localtime=True)
                           msg['Message-ID'] = make_msgid(domain=self.get_domain_from_email(self.smtp_config['username']))
                           
                           # Bulk email headers
                           msg['X-Bulk-Email'] = 'true'
                           msg['X-Batch-ID'] = str(uuid.uuid4())
                           msg['List-Unsubscribe'] = '<mailto:unsubscribe@example.com>'
                           
                           # Send email
                           result = self.send_email(msg)
                           
                           if result.success:
                               successful_sends += 1
                               logger.info(f"      ✓ Sent to {recipient['email']}")
                           else:
                               failed_sends += 1
                               logger.error(f"      ❌ Failed to send to {recipient['email']}: {result.error_message}")
                       
                       except Exception as e:
                           failed_sends += 1
                           logger.error(f"      ❌ Error sending to {recipient['email']}: {e}")
                   
                   # Delay between batches
                   if i + batch_size < len(recipients):
                       logger.info(f"    Waiting {delay_between_batches}s before next batch...")
                       time.sleep(delay_between_batches)
               
               logger.info(f"  📊 Bulk sending complete: {successful_sends} successful, {failed_sends} failed")
               
           except Exception as e:
               logger.error(f"Failed bulk emails with throttling: {e}")
   
       def send_personalized_bulk_emails(self):
           """
           Send personalized bulk emails using templates.
           """
           logger.info("--- Personalized Bulk Emails ---")
           
           try:
               # Recipients with personalization data
               recipients = [
                   {
                       'email': 'john@example.com',
                       'name': 'John Doe',
                       'department': 'Engineering',
                       'project': 'Mobile App'
                   },
                   {
                       'email': 'jane@example.com',
                       'name': 'Jane Smith',
                       'department': 'Marketing',
                       'project': 'Website Redesign'
                   },
                   {
                       'email': 'bob@example.com',
                       'name': 'Bob Johnson',
                       'department': 'Sales',
                       'project': 'CRM Integration'
                   }
               ]
               
               # Email template
               template = """
               <html>
                 <body>
                   <h2>Project Update for {name}</h2>
                   <p>Dear {name} from the {department} department,</p>
                   <p>This is a personalized update regarding the <strong>{project}</strong> project.</p>
                   <p>Please review the attached materials and provide your feedback.</p>
                   <p>Best regards,<br>Project Management Team</p>
                 </body>
               </html>
               """
               
               successful_sends = 0
               
               for recipient in recipients:
                   try:
                       # Personalize template
                       personalized_content = template.format(
                           name=recipient['name'],
                           department=recipient['department'],
                           project=recipient['project']
                       )
                       
                       # Create message
                       msg = MIMEText(personalized_content, 'html')
                       
                       # Headers
                       msg['Subject'] = f"Project Update: {recipient['project']}"
                       msg['From'] = formataddr(('Project Manager', self.smtp_config['username']))
                       msg['To'] = formataddr((recipient['name'], recipient['email']))
                       msg['Date'] = formatdate(localtime=True)
                       msg['Message-ID'] = make_msgid(domain=self.get_domain_from_email(self.smtp_config['username']))
                       
                       # Personalization headers
                       msg['X-Personalized'] = 'true'
                       msg['X-Department'] = recipient['department']
                       msg['X-Project'] = recipient['project']
                       
                       # Send email
                       result = self.send_email(msg)
                       
                       if result.success:
                           successful_sends += 1
                           logger.info(f"    ✓ Sent personalized email to {recipient['name']}")
                       else:
                           logger.error(f"    ❌ Failed to send to {recipient['name']}: {result.error_message}")
                   
                   except Exception as e:
                       logger.error(f"    ❌ Error sending personalized email to {recipient['name']}: {e}")
               
               logger.info(f"  📊 Personalized bulk sending: {successful_sends}/{len(recipients)} successful")
               
           except Exception as e:
               logger.error(f"Failed personalized bulk emails: {e}")
   
       def send_bulk_emails_with_error_handling(self):
           """
           Send bulk emails with comprehensive error handling.
           """
           logger.info("--- Bulk Emails with Error Handling ---")
           
           try:
               # Recipients with some invalid emails for testing
               recipients = [
                   'valid1@example.com',
                   'valid2@example.com',
                   'invalid-email',  # Invalid format
                   'valid3@example.com',
                   'nonexistent@invalid-domain-xyz.com'  # Non-existent domain
               ]
               
               results = {
                   'successful': [],
                   'failed': [],
                   'invalid_format': [],
                   'server_errors': []
               }
               
               for recipient in recipients:
                   try:
                       # Validate email format
                       if not self.validate_email_format(recipient):
                           results['invalid_format'].append(recipient)
                           logger.warning(f"    ⚠ Invalid email format: {recipient}")
                           continue
                       
                       # Create message
                       msg = MIMEText(f"This is a test email to {recipient}")
                       
                       # Headers
                       msg['Subject'] = 'Test Email with Error Handling'
                       msg['From'] = formataddr(('Error Handler', self.smtp_config['username']))
                       msg['To'] = recipient
                       msg['Date'] = formatdate(localtime=True)
                       msg['Message-ID'] = make_msgid(domain=self.get_domain_from_email(self.smtp_config['username']))
                       
                       # Send email
                       result = self.send_email(msg)
                       
                       if result.success:
                           results['successful'].append(recipient)
                           logger.info(f"    ✓ Sent to {recipient}")
                       else:
                           if 'server' in result.error_message.lower():
                               results['server_errors'].append(recipient)
                           else:
                               results['failed'].append(recipient)
                           logger.error(f"    ❌ Failed to send to {recipient}: {result.error_message}")
                   
                   except Exception as e:
                       results['failed'].append(recipient)
                       logger.error(f"    ❌ Error sending to {recipient}: {e}")
               
               # Summary
               logger.info(f"  📊 Bulk email results:")
               logger.info(f"    • Successful: {len(results['successful'])}")
               logger.info(f"    • Failed: {len(results['failed'])}")
               logger.info(f"    • Invalid format: {len(results['invalid_format'])}")
               logger.info(f"    • Server errors: {len(results['server_errors'])}")
               
           except Exception as e:
               logger.error(f"Failed bulk emails with error handling: {e}")
   
       def validate_email_format(self, email: str) -> bool:
           """
           Validate email format using simple regex.
           """
           import re
           pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
           return re.match(pattern, email) is not None
   
       def demonstrate_email_templates(self):
           """
           Demonstrate email template system.
           """
           logger.info("--- Email Templates ---")
           
           try:
               # Template-based emails
               self.send_welcome_email_template()
               self.send_notification_email_template()
               self.send_invoice_email_template()
               
               logger.info("  ✓ Email templates completed")
               
           except Exception as e:
               logger.error(f"Failed email templates: {e}")
   
       def send_welcome_email_template(self):
           """
           Send welcome email using template.
           """
           logger.info("--- Welcome Email Template ---")
           
           try:
               # Welcome email template
               template_data = {
                   'user_name': 'John Doe',
                   'company_name': 'Example Corp',
                   'activation_link': 'https://example.com/activate/abc123',
                   'support_email': 'support@example.com'
               }
               
               html_template = """
               <html>
                 <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                   <div style="background-color: #f8f9fa; padding: 20px; text-align: center;">
                     <h1 style="color: #007bff;">Welcome to {company_name}!</h1>
                   </div>
                   <div style="padding: 20px;">
                     <p>Dear {user_name},</p>
                     <p>Welcome to {company_name}! We're excited to have you join our community.</p>
                     <p>To get started, please activate your account by clicking the button below:</p>
                     <div style="text-align: center; margin: 30px 0;">
                       <a href="{activation_link}" style="background-color: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px;">Activate Account</a>
                     </div>
                     <p>If you have any questions, please don't hesitate to contact us at <a href="mailto:{support_email}">{support_email}</a>.</p>
                     <p>Best regards,<br>The {company_name} Team</p>
                   </div>
                   <div style="background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666;">
                     <p>This is an automated message. Please do not reply to this email.</p>
                   </div>
                 </body>
               </html>
               """
               
               # Format template
               html_content = html_template.format(**template_data)
               
               # Create message
               msg = MIMEText(html_content, 'html')
               
               # Headers
               msg['Subject'] = f"Welcome to {template_data['company_name']}!"
               msg['From'] = formataddr((template_data['company_name'], self.smtp_config['username']))
               msg['To'] = 'newuser@example.com'
               msg['Date'] = formatdate(localtime=True)
               msg['Message-ID'] = make_msgid(domain=self.get_domain_from_email(self.smtp_config['username']))
               
               # Template headers
               msg['X-Email-Template'] = 'welcome'
               msg['X-Email-Type'] = 'transactional'
               
               # Send email
               result = self.send_email(msg)
               
               if result.success:
                   logger.info(f"    ✓ Welcome email sent to {template_data['user_name']}")
               else:
                   logger.error(f"    ❌ Failed to send welcome email: {result.error_message}")
               
           except Exception as e:
               logger.error(f"Failed welcome email template: {e}")
   
       def send_notification_email_template(self):
           """
           Send notification email using template.
           """
           logger.info("--- Notification Email Template ---")
           
           try:
               # Notification data
               notification_data = {
                   'user_name': 'Jane Smith',
                   'notification_type': 'Security Alert',
                   'notification_message': 'A new login was detected from an unrecognized device.',
                   'action_required': 'Please review your recent activity and secure your account if necessary.',
                   'dashboard_link': 'https://example.com/dashboard',
                   'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
               }
               
               html_template = """
               <html>
                 <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                   <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 5px;">
                     <h2 style="color: #856404; margin-top: 0;">⚠️ {notification_type}</h2>
                     <p>Hello {user_name},</p>
                     <p><strong>Alert:</strong> {notification_message}</p>
                     <p><strong>Action Required:</strong> {action_required}</p>
                     <p><strong>Time:</strong> {timestamp}</p>
                     <div style="margin: 20px 0;">
                       <a href="{dashboard_link}" style="background-color: #ffc107; color: #212529; padding: 10px 20px; text-decoration: none; border-radius: 3px;">Review Activity</a>
                     </div>
                     <p style="font-size: 14px; color: #666;">If you did not perform this action, please contact our support team immediately.</p>
                   </div>
                 </body>
               </html>
               """
               
               # Format template
               html_content = html_template.format(**notification_data)
               
               # Create message
               msg = MIMEText(html_content, 'html')
               
               # Headers
               msg['Subject'] = f"{notification_data['notification_type']} - Action Required"
               msg['From'] = formataddr(('Security Team', self.smtp_config['username']))
               msg['To'] = 'user@example.com'
               msg['Date'] = formatdate(localtime=True)
               msg['Message-ID'] = make_msgid(domain=self.get_domain_from_email(self.smtp_config['username']))
               
               # Notification headers
               msg['X-Email-Template'] = 'notification'
               msg['X-Email-Type'] = 'alert'
               msg['X-Priority'] = '2'  # High priority
               msg['Importance'] = 'High'
               
               # Send email
               result = self.send_email(msg)
               
               if result.success:
                   logger.info(f"    ✓ Notification email sent for {notification_data['notification_type']}")
               else:
                   logger.error(f"    ❌ Failed to send notification email: {result.error_message}")
               
           except Exception as e:
               logger.error(f"Failed notification email template: {e}")
   
       def send_invoice_email_template(self):
           """
           Send invoice email using template.
           """
           logger.info("--- Invoice Email Template ---")
           
           try:
               # Invoice data
               invoice_data = {
                   'customer_name': 'ABC Company',
                   'invoice_number': 'INV-2024-001',
                   'invoice_date': '2024-01-15',
                   'due_date': '2024-02-15',
                   'amount': '$1,250.00',
                   'items': [
                       {'description': 'Web Development Services', 'quantity': 20, 'rate': '$50.00', 'amount': '$1,000.00'},
                       {'description': 'Domain Registration', 'quantity': 1, 'rate': '$15.00', 'amount': '$15.00'},
                       {'description': 'SSL Certificate', 'quantity': 1, 'rate': '$25.00', 'amount': '$25.00'}
                   ],
                   'payment_link': 'https://example.com/pay/inv-2024-001'
               }
               
               # Generate items HTML
               items_html = ""
               for item in invoice_data['items']:
                   items_html += f"""
                   <tr>
                     <td style="padding: 8px; border-bottom: 1px solid #ddd;">{item['description']}</td>
                     <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: center;">{item['quantity']}</td>
                     <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">{item['rate']}</td>
                     <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">{item['amount']}</td>
                   </tr>
                   """
               
               html_template = f"""
               <html>
                 <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                   <div style="background-color: #f8f9fa; padding: 20px; text-align: center;">
                     <h1 style="color: #007bff;">Invoice {invoice_data['invoice_number']}</h1>
                   </div>
                   <div style="padding: 20px;">
                     <p>Dear {invoice_data['customer_name']},</p>
                     <p>Please find your invoice details below:</p>
                     
                     <table style="width: 100%; margin: 20px 0;">
                       <tr>
                         <td><strong>Invoice Number:</strong></td>
                         <td>{invoice_data['invoice_number']}</td>
                       </tr>
                       <tr>
                         <td><strong>Invoice Date:</strong></td>
                         <td>{invoice_data['invoice_date']}</td>
                       </tr>
                       <tr>
                         <td><strong>Due Date:</strong></td>
                         <td>{invoice_data['due_date']}</td>
                       </tr>
                     </table>
                     
                     <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                       <thead>
                         <tr style="background-color: #f8f9fa;">
                           <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Description</th>
                           <th style="padding: 10px; border: 1px solid #ddd; text-align: center;">Qty</th>
                           <th style="padding: 10px; border: 1px solid #ddd; text-align: right;">Rate</th>
                           <th style="padding: 10px; border: 1px solid #ddd; text-align: right;">Amount</th>
                         </tr>
                       </thead>
                       <tbody>
                         {items_html}
                       </tbody>
                     </table>
                     
                     <div style="text-align: right; margin: 20px 0;">
                       <p style="font-size: 18px;"><strong>Total Amount: {invoice_data['amount']}</strong></p>
                     </div>
                     
                     <div style="text-align: center; margin: 30px 0;">
                       <a href="{invoice_data['payment_link']}" style="background-color: #28a745; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px;">Pay Now</a>
                     </div>
                     
                     <p>Thank you for your business!</p>
                   </div>
                 </body>
               </html>
               """
               
               # Create message
               msg = MIMEText(html_template, 'html')
               
               # Headers
               msg['Subject'] = f"Invoice {invoice_data['invoice_number']} - {invoice_data['amount']}"
               msg['From'] = formataddr(('Billing Department', self.smtp_config['username']))
               msg['To'] = 'customer@example.com'
               msg['Date'] = formatdate(localtime=True)
               msg['Message-ID'] = make_msgid(domain=self.get_domain_from_email(self.smtp_config['username']))
               
               # Invoice headers
               msg['X-Email-Template'] = 'invoice'
               msg['X-Email-Type'] = 'transactional'
               msg['X-Invoice-Number'] = invoice_data['invoice_number']
               
               # Send email
               result = self.send_email(msg)
               
               if result.success:
                   logger.info(f"    ✓ Invoice email sent for {invoice_data['invoice_number']}")
               else:
                   logger.error(f"    ❌ Failed to send invoice email: {result.error_message}")
               
           except Exception as e:
               logger.error(f"Failed invoice email template: {e}")
   
       def demonstrate_advanced_headers(self):
           """
           Demonstrate advanced email headers for tracking and compliance.
           """
           logger.info("--- Advanced Headers ---")
           
           try:
               # Tracking headers
               self.send_email_with_tracking_headers()
               
               # Compliance headers
               self.send_email_with_compliance_headers()
               
               # Custom headers
               self.send_email_with_custom_headers()
               
               logger.info("  ✓ Advanced headers completed")
               
           except Exception as e:
               logger.error(f"Failed advanced headers: {e}")
   
       def send_email_with_tracking_headers(self):
           """
           Send email with comprehensive tracking headers.
           """
           logger.info("--- Email with Tracking Headers ---")
           
           try:
               # Create message
               msg = MIMEText("This email includes comprehensive tracking headers for analytics.")
               
               # Basic headers
               msg['Subject'] = 'Email with Tracking Headers'
               msg['From'] = formataddr(('Tracking Sender', self.smtp_config['username']))
               msg['To'] = 'recipient@example.com'
               msg['Date'] = formatdate(localtime=True)
               msg['Message-ID'] = make_msgid(domain=self.get_domain_from_email(self.smtp_config['username']))
               
               # Tracking headers
               campaign_id = str(uuid.uuid4())
               email_id = str(uuid.uuid4())
               
               msg['X-Campaign-ID'] = campaign_id
               msg['X-Email-ID'] = email_id
               msg['X-Tracking-ID'] = f"track_{int(time.time())}"
               msg['X-Source'] = 'email_campaign'
               msg['X-Medium'] = 'email'
               msg['X-Campaign-Name'] = 'product_launch'
               msg['X-Segment'] = 'premium_users'
               msg['X-Send-Time'] = datetime.now().isoformat()
               
               # Analytics headers
               msg['X-Analytics-Domain'] = 'analytics.example.com'
               msg['X-Open-Tracking'] = 'enabled'
               msg['X-Click-Tracking'] = 'enabled'
               
               # Send email
               result = self.send_email(msg)
               
               if result.success:
                   logger.info("    ✓ Email with tracking headers sent successfully")
                   logger.info(f"      Campaign ID: {campaign_id}")
                   logger.info(f"      Email ID: {email_id}")
               else:
                   logger.error(f"    ❌ Failed to send email with tracking headers: {result.error_message}")
               
           except Exception as e:
               logger.error(f"Failed email with tracking headers: {e}")
   
       def send_email_with_compliance_headers(self):
           """
           Send email with compliance and legal headers.
           """
           logger.info("--- Email with Compliance Headers ---")
           
           try:
               # Create message
               msg = MIMEText("This email includes compliance headers for legal requirements.")
               
               # Basic headers
               msg['Subject'] = 'Email with Compliance Headers'
               msg['From'] = formataddr(('Compliance Team', self.smtp_config['username']))
               msg['To'] = 'recipient@example.com'
               msg['Date'] = formatdate(localtime=True)
               msg['Message-ID'] = make_msgid(domain=self.get_domain_from_email(self.smtp_config['username']))
               
               # Compliance headers
               msg['List-Unsubscribe'] = '<mailto:unsubscribe@example.com>'
               msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
               msg['List-ID'] = 'Product Updates <updates.example.com>'
               msg['List-Subscribe'] = '<mailto:subscribe@example.com>'
               msg['List-Help'] = '<mailto:help@example.com>'
               msg['List-Owner'] = '<mailto:owner@example.com>'
               msg['List-Archive'] = '<https://example.com/archive>'
               
               # Legal headers
               msg['X-Legal-Entity'] = 'Example Corp'
               msg['X-Privacy-Policy'] = 'https://example.com/privacy'
               msg['X-Terms-Of-Service'] = 'https://example.com/terms'
               msg['X-Data-Controller'] = 'privacy@example.com'
               msg['X-GDPR-Compliant'] = 'true'
               msg['X-CAN-SPAM-Compliant'] = 'true'
               
               # Organization headers
               msg['Organization'] = 'Example Corp'
               msg['X-Organization-Address'] = '123 Main St, City, State 12345'
               msg['X-Organization-Phone'] = '+1-555-123-4567'
               
               # Send email
               result = self.send_email(msg)
               
               if result.success:
                   logger.info("    ✓ Email with compliance headers sent successfully")
               else:
                   logger.error(f"    ❌ Failed to send email with compliance headers: {result.error_message}")
               
           except Exception as e:
               logger.error(f"Failed email with compliance headers: {e}")
   
       def send_email_with_custom_headers(self):
           """
           Send email with custom business headers.
           """
           logger.info("--- Email with Custom Headers ---")
           
           try:
               # Create message
               msg = MIMEText("This email includes custom business headers for internal tracking.")
               
               # Basic headers
               msg['Subject'] = 'Email with Custom Headers'
               msg['From'] = formataddr(('Custom Sender', self.smtp_config['username']))
               msg['To'] = 'recipient@example.com'
               msg['Date'] = formatdate(localtime=True)
               msg['Message-ID'] = make_msgid(domain=self.get_domain_from_email(self.smtp_config['username']))
               
               # Custom business headers
               msg['X-Department'] = 'Engineering'
               msg['X-Project'] = 'Mobile App Development'
               msg['X-Team'] = 'Backend Team'
               msg['X-Sprint'] = 'Sprint-24-Q1'
               msg['X-Priority-Level'] = 'medium'
               msg['X-Environment'] = 'production'
               
               # Custom workflow headers
               msg['X-Workflow-ID'] = str(uuid.uuid4())
               msg['X-Workflow-Step'] = 'notification'
               msg['X-Approval-Required'] = 'false'
               msg['X-Auto-Generated'] = 'true'
               
               # Custom metadata headers
               msg['X-User-Segment'] = 'enterprise'
               msg['X-Account-Type'] = 'premium'
               msg['X-Region'] = 'us-west-2'
               msg['X-Timezone'] = 'America/Los_Angeles'
               
               # Send email
               result = self.send_email(msg)
               
               if result.success:
                   logger.info("    ✓ Email with custom headers sent successfully")
               else:
                   logger.error(f"    ❌ Failed to send email with custom headers: {result.error_message}")
               
           except Exception as e:
               logger.error(f"Failed email with custom headers: {e}")
   
       def demonstrate_bounce_handling(self):
           """
           Demonstrate bounce handling and delivery status.
           """
           logger.info("--- Bounce Handling ---")
           
           try:
               # Send email with bounce tracking
               self.send_email_with_bounce_tracking()
               
               # Simulate bounce processing
               self.simulate_bounce_processing()
               
               logger.info("  ✓ Bounce handling completed")
               
           except Exception as e:
               logger.error(f"Failed bounce handling: {e}")
   
       def send_email_with_bounce_tracking(self):
           """
           Send email with bounce tracking headers.
           """
           logger.info("--- Email with Bounce Tracking ---")
           
           try:
               # Create message
               msg = MIMEText("This email includes bounce tracking for delivery monitoring.")
               
               # Basic headers
               msg['Subject'] = 'Email with Bounce Tracking'
               msg['From'] = formataddr(('Bounce Tracker', self.smtp_config['username']))
               msg['To'] = 'recipient@example.com'
               msg['Date'] = formatdate(localtime=True)
               msg['Message-ID'] = make_msgid(domain=self.get_domain_from_email(self.smtp_config['username']))
               
               # Bounce tracking headers
               bounce_id = str(uuid.uuid4())
               msg['X-Bounce-ID'] = bounce_id
               msg['X-Bounce-Address'] = 'bounces@example.com'
               msg['Return-Path'] = 'bounces@example.com'
               msg['Errors-To'] = 'bounces@example.com'
               
               # Delivery tracking
               msg['X-Delivery-Receipt'] = 'requested'
               msg['X-Read-Receipt'] = 'requested'
               msg['Disposition-Notification-To'] = self.smtp_config['username']
               
               # Send email
               result = self.send_email(msg)
               
               if result.success:
                   logger.info("    ✓ Email with bounce tracking sent successfully")
                   logger.info(f"      Bounce ID: {bounce_id}")
               else:
                   logger.error(f"    ❌ Failed to send email with bounce tracking: {result.error_message}")
               
           except Exception as e:
               logger.error(f"Failed email with bounce tracking: {e}")
   
       def simulate_bounce_processing(self):
           """
           Simulate bounce email processing.
           """
           logger.info("--- Bounce Processing Simulation ---")
           
           try:
               # Simulate different types of bounces
               bounce_types = [
                   {
                       'type': 'hard_bounce',
                       'reason': 'User unknown',
                       'email': 'nonexistent@example.com',
                       'action': 'Remove from list'
                   },
                   {
                       'type': 'soft_bounce',
                       'reason': 'Mailbox full',
                       'email': 'full@example.com',
                       'action': 'Retry later'
                   },
                   {
                       'type': 'block',
                       'reason': 'Spam filter',
                       'email': 'blocked@example.com',
                       'action': 'Review content'
                   }
               ]
               
               logger.info("    📊 Bounce processing simulation:")
               
               for bounce in bounce_types:
                   logger.info(f"      • {bounce['type'].title()}: {bounce['email']}")
                   logger.info(f"        Reason: {bounce['reason']}")
                   logger.info(f"        Action: {bounce['action']}")
                   
                   # In a real application, you would:
                   # 1. Parse bounce emails
                   # 2. Extract bounce information
                   # 3. Update recipient status
                   # 4. Take appropriate action
               
               logger.info("    ✓ Bounce processing simulation completed")
               
           except Exception as e:
               logger.error(f"Failed bounce processing simulation: {e}")
   
       def demonstrate_imap_integration(self):
           """
           Demonstrate IMAP integration for sent message handling.
           """
           logger.info("--- IMAP Integration ---")
           
           try:
               if not self.imap_config:
                   logger.info("    ℹ IMAP config not provided, skipping integration demo")
                   return
               
               # Send email and save to sent folder
               self.send_and_save_to_sent()
               
               # Sync sent messages
               self.sync_sent_messages()
               
               logger.info("  ✓ IMAP integration completed")
               
           except Exception as e:
               logger.error(f"Failed IMAP integration: {e}")
   
       def send_and_save_to_sent(self):
           """
           Send email and save copy to sent folder.
           """
           logger.info("--- Send and Save to Sent ---")
           
           try:
               # Create message
               msg = MIMEText("This email will be saved to the sent folder after sending.")
               
               # Headers
               msg['Subject'] = 'Email Saved to Sent Folder'
               msg['From'] = formataddr(('IMAP Sender', self.smtp_config['username']))
               msg['To'] = 'recipient@example.com'
               msg['Date'] = formatdate(localtime=True)
               msg['Message-ID'] = make_msgid(domain=self.get_domain_from_email(self.smtp_config['username']))
               
               # Send email
               result = self.send_email(msg)
               
               if result.success:
                   logger.info("    ✓ Email sent successfully")
                   
                   # Save to sent folder
                   self.save_to_sent_folder(msg)
               else:
                   logger.error(f"    ❌ Failed to send email: {result.error_message}")
               
           except Exception as e:
               logger.error(f"Failed send and save to sent: {e}")
   
       def save_to_sent_folder(self, msg):
           """
           Save sent message to IMAP sent folder.
           """
           try:
               with IMAPClient(config=self.imap_config) as client:
                   uid_service = IMAPMailboxUIDService(client)
                   
                   # Append message to sent folder
                   result = uid_service.append_message("Sent", msg.as_string())
                   
                   if result.success:
                       logger.info("    ✓ Message saved to sent folder")
                   else:
                       logger.error(f"    ❌ Failed to save to sent folder: {result.error_message}")
               
           except Exception as e:
               logger.error(f"Failed to save to sent folder: {e}")
   
       def sync_sent_messages(self):
           """
           Synchronize sent messages between SMTP and IMAP.
           """
           logger.info("--- Sync Sent Messages ---")
           
           try:
               with IMAPClient(config=self.imap_config) as client:
                   uid_service = IMAPMailboxUIDService(client)
                   uid_service.select("Sent")
                   
                   # Get recent sent messages
                   recent_sent = uid_service.create_message_set_from_search(
                       IMAPSearchCriteria.since_days(1)
                   )
                   
                   logger.info(f"    📧 Found {len(recent_sent)} recent sent messages")
                   
                   # Sync with local tracking
                   self.sync_with_local_tracking(uid_service, recent_sent)
                   
                   logger.info("    ✓ Sent messages synchronized")
               
           except Exception as e:
               logger.error(f"Failed to sync sent messages: {e}")
   
       def sync_with_local_tracking(self, uid_service, sent_messages):
           """
           Synchronize sent messages with local tracking.
           """
           try:
               if sent_messages.is_empty():
                   logger.info("    📧 No sent messages to sync")
                   return
               
               # Fetch message headers for syncing
               fetch_result = uid_service.uid_fetch(sent_messages, MessagePart.HEADER)
               
               if fetch_result.success:
                   messages = fetch_result.metadata.get('fetched_messages', [])
                   
                   synced_count = 0
                   for message in messages:
                       # Match with local tracking
                       if self.match_with_local_tracking(message):
                           synced_count += 1
                   
                   logger.info(f"    📊 Synchronized {synced_count} messages with local tracking")
               
           except Exception as e:
               logger.error(f"Failed to sync with local tracking: {e}")
   
       def match_with_local_tracking(self, message) -> bool:
           """
           Match sent message with local tracking data.
           """
           try:
               # In a real application, you would:
               # 1. Extract Message-ID from sent message
               # 2. Match with local sent message tracking
               # 3. Update delivery status
               # 4. Record timing information
               
               message_id = message.message_id
               
               # Simulate matching
               for sent_msg in self.sent_messages:
                   if sent_msg.get('message_id') == message_id:
                       sent_msg['synced'] = True
                       sent_msg['sync_time'] = datetime.now()
                       return True
               
               return False
               
           except Exception as e:
               logger.error(f"Failed to match with local tracking: {e}")
               return False
   
       def demonstrate_production_patterns(self):
           """
           Demonstrate production-ready patterns and best practices.
           """
           logger.info("--- Production Patterns ---")
           
           try:
               # Connection pooling
               self.demonstrate_connection_pooling()
               
               # Retry logic
               self.demonstrate_retry_logic()
               
               # Rate limiting
               self.demonstrate_rate_limiting()
               
               # Health monitoring
               self.demonstrate_health_monitoring()
               
               logger.info("  ✓ Production patterns completed")
               
           except Exception as e:
               logger.error(f"Failed production patterns: {e}")
   
       def demonstrate_connection_pooling(self):
           """
           Demonstrate SMTP connection pooling.
           """
           logger.info("--- Connection Pooling ---")
           
           try:
               # Connection pool simulation
               logger.info("    📡 SMTP connection pooling patterns:")
               logger.info("      • Reuse connections for multiple emails")
               logger.info("      • Connection lifecycle management")
               logger.info("      • Pool size optimization")
               logger.info("      • Connection health checks")
               
               # In a real application, you would implement:
               # 1. Connection pool manager
               # 2. Connection reuse logic
               # 3. Connection health monitoring
               # 4. Pool size management
               
               logger.info("    ✓ Connection pooling patterns demonstrated")
               
           except Exception as e:
               logger.error(f"Failed connection pooling demonstration: {e}")
   
       def demonstrate_retry_logic(self):
           """
           Demonstrate retry logic for failed sends.
           """
           logger.info("--- Retry Logic ---")
           
           try:
               # Retry configuration
               retry_config = {
                   'max_retries': 3,
                   'base_delay': 1.0,
                   'max_delay': 60.0,
                   'exponential_backoff': True
               }
               
               logger.info(f"    🔄 Retry configuration:")
               logger.info(f"      • Max retries: {retry_config['max_retries']}")
               logger.info(f"      • Base delay: {retry_config['base_delay']}s")
               logger.info(f"      • Max delay: {retry_config['max_delay']}s")
               logger.info(f"      • Exponential backoff: {retry_config['exponential_backoff']}")
               
               # Simulate retry scenarios
               retry_scenarios = [
                   ('Connection timeout', True),
                   ('Temporary server error', True),
                   ('Authentication failure', False),
                   ('Invalid recipient', False)
               ]
               
               for scenario, should_retry in retry_scenarios:
                   logger.info(f"      • {scenario}: {'Retry' if should_retry else 'Fail immediately'}")
               
               logger.info("    ✓ Retry logic patterns demonstrated")
               
           except Exception as e:
               logger.error(f"Failed retry logic demonstration: {e}")
   
       def demonstrate_rate_limiting(self):
           """
           Demonstrate rate limiting for email sending.
           """
           logger.info("--- Rate Limiting ---")
           
           try:
               # Rate limiting configuration
               rate_limits = {
                   'emails_per_minute': 60,
                   'emails_per_hour': 1000,
                   'emails_per_day': 10000,
                   'burst_limit': 10,
                   'burst_window': 60
               }
               
               logger.info(f"    📊 Rate limiting configuration:")
               for limit_type, limit_value in rate_limits.items():
                   logger.info(f"      • {limit_type.replace('_', ' ').title()}: {limit_value}")
               
               # Rate limiting implementation patterns
               logger.info("    🚦 Rate limiting patterns:")
               logger.info("      • Token bucket algorithm")
               logger.info("      • Sliding window counters")
               logger.info("      • Burst protection")
               logger.info("      • Adaptive rate limiting")
               
               logger.info("    ✓ Rate limiting patterns demonstrated")
               
           except Exception as e:
               logger.error(f"Failed rate limiting demonstration: {e}")
   
       def demonstrate_health_monitoring(self):
           """
           Demonstrate health monitoring for email system.
           """
           logger.info("--- Health Monitoring ---")
           
           try:
               # Health metrics
               health_metrics = {
                   'smtp_connection_status': 'healthy',
                   'sent_emails_last_hour': 245,
                   'failed_emails_last_hour': 3,
                   'average_send_time': 0.15,
                   'bounce_rate': 2.1,
                   'delivery_rate': 97.9,
                   'queue_size': 12
               }
               
               logger.info(f"    📈 Health monitoring metrics:")
               for metric, value in health_metrics.items():
                   logger.info(f"      • {metric.replace('_', ' ').title()}: {value}")
               
               # Health check patterns
               logger.info("    🏥 Health monitoring patterns:")
               logger.info("      • Connection health checks")
               logger.info("      • Performance metrics tracking")
               logger.info("      • Error rate monitoring")
               logger.info("      • Queue depth monitoring")
               logger.info("      • Delivery success tracking")
               
               logger.info("    ✓ Health monitoring patterns demonstrated")
               
           except Exception as e:
               logger.error(f"Failed health monitoring demonstration: {e}")
   
       def send_email(self, message) -> 'SendResult':
           """
           Send email using SMTP with proper error handling.
           """
           try:
               # Create SMTP connection
               if self.smtp_config.get('use_tls', True):
                   smtp = smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port'])
                   smtp.starttls()
               else:
                   smtp = smtplib.SMTP_SSL(self.smtp_config['host'], self.smtp_config['port'])
               
               # Authenticate
               smtp.login(self.smtp_config['username'], self.smtp_config['password'])
               
               # Send message
               from_addr = self.smtp_config['username']
               to_addrs = [message['To']]
               
               smtp.send_message(message, from_addr, to_addrs)
               smtp.quit()
               
               # Track successful send
               self.sent_messages.append({
                   'message_id': message['Message-ID'],
                   'to': message['To'],
                   'subject': message['Subject'],
                   'send_time': datetime.now(),
                   'status': 'sent'
               })
               
               return SendResult(success=True)
               
           except Exception as e:
               # Track failed send
               self.failed_messages.append({
                   'to': message.get('To', 'unknown'),
                   'subject': message.get('Subject', 'unknown'),
                   'error': str(e),
                   'fail_time': datetime.now()
               })
               
               return SendResult(success=False, error_message=str(e))
   
       def get_domain_from_email(self, email: str) -> str:
           """
           Extract domain from email address for Message-ID generation.
           """
           try:
               return email.split('@')[1]
           except (IndexError, AttributeError):
               return 'localhost'


   class SendResult:
       """
       Result object for email sending operations.
       """
       def __init__(self, success: bool, error_message: str = None):
           self.success = success
           self.error_message = error_message


   def main():
       """
       Main function to run the SMTP integration example.
       """
       # SMTP Configuration - Replace with your actual credentials
       smtp_config = {
           'host': 'smtp.gmail.com',
           'port': 587,
           'username': 'your_email@gmail.com',
           'password': 'your_app_password',
           'use_tls': True
       }
       
       # Optional IMAP Configuration for sent message handling
       imap_config = {
           'host': 'imap.gmail.com',
           'username': 'your_email@gmail.com',
           'password': 'your_app_password',
           'port': 993,
           'use_ssl': True
       }
       
       # Create and run the example
       example = ProductionEmailSender(smtp_config, imap_config)
       
       try:
           example.demonstrate_smtp_operations()
           logger.info("🎉 SMTP integration example completed successfully!")
           
       except Exception as e:
           logger.error(f"❌ Example failed: {e}")
           return 1
       
       return 0


   if __name__ == "__main__":
       exit(main())


Email Standards Reference
-------------------------

Required Headers (RFC 5322)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Mandatory headers
   msg['From'] = formataddr(('Sender Name', 'sender@example.com'))
   msg['To'] = formataddr(('Recipient Name', 'recipient@example.com'))
   msg['Subject'] = 'Email Subject'
   msg['Date'] = formatdate(localtime=True)
   msg['Message-ID'] = make_msgid(domain='example.com')

Message-ID Generation
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Proper Message-ID generation
   from email.utils import make_msgid
   
   # Generate unique Message-ID with domain
   message_id = make_msgid(domain='example.com')
   msg['Message-ID'] = message_id
   
   # Format: <unique-id@domain>
   # Example: <20240115123456.abc123@example.com>

Multipart Messages
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # HTML email with attachments
   msg = MIMEMultipart('mixed')
   
   # HTML content
   html_part = MIMEText(html_content, 'html')
   msg.attach(html_part)
   
   # File attachment
   with open('file.pdf', 'rb') as f:
       attachment = MIMEBase('application', 'pdf')
       attachment.set_payload(f.read())
       encoders.encode_base64(attachment)
       attachment.add_header('Content-Disposition', 'attachment', filename='file.pdf')
       msg.attach(attachment)

Authentication and Security
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # SMTP with TLS
   smtp = smtplib.SMTP('smtp.gmail.com', 587)
   smtp.starttls()
   smtp.login(username, password)
   
   # SMTP with SSL
   smtp = smtplib.SMTP_SSL('smtp.gmail.com', 465)
   smtp.login(username, password)

Compliance Headers
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Unsubscribe compliance
   msg['List-Unsubscribe'] = '<mailto:unsubscribe@example.com>'
   msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
   
   # Organization info
   msg['Organization'] = 'Your Company Name'
   
   # Legal compliance
   msg['X-Privacy-Policy'] = 'https://example.com/privacy'

Best Practices
--------------

✅ **DO:**

- Generate unique Message-IDs for each email

- Use proper RFC-compliant headers

- Implement retry logic for failures

- Use TLS/SSL for secure connections

- Include unsubscribe links for bulk emails

- Monitor bounce rates and delivery status

- Implement rate limiting

- Use proper MIME types for attachments

❌ **DON'T:**

- Reuse Message-IDs

- Skip required headers

- Send without authentication

- Ignore bounce handling

- Send bulk emails without throttling

- Use non-standard headers for critical data

- Forget to handle connection errors

- Send emails without proper encoding

Common SMTP Servers
-------------------

Gmail
~~~~~

.. code-block:: python

   smtp_config = {
       'host': 'smtp.gmail.com',
       'port': 587,
       'use_tls': True,
       'username': 'your_email@gmail.com',
       'password': 'your_app_password'  # Use app password!
   }

Outlook/Hotmail
~~~~~~~~~~~~~~~

.. code-block:: python

   smtp_config = {
       'host': 'smtp-mail.outlook.com',
       'port': 587,
       'use_tls': True,
       'username': 'your_email@outlook.com',
       'password': 'your_password'
   }

Custom Server
~~~~~~~~~~~~~

.. code-block:: python

   smtp_config = {
       'host': 'mail.yourcompany.com',
       'port': 587,  # or 465 for SSL
       'use_tls': True,  # or False for SSL
       'username': 'your_username',
       'password': 'your_password'
   }

Error Handling
--------------

.. code-block:: python

   try:
       result = send_email(message)
       if result.success:
           logger.info("Email sent successfully")
       else:
           logger.error(f"Email failed: {result.error_message}")
   
   except smtplib.SMTPAuthenticationError:
       logger.error("Authentication failed")
   except smtplib.SMTPRecipientsRefused:
       logger.error("Recipients refused")
   except smtplib.SMTPServerDisconnected:
       logger.error("Server disconnected")
   except Exception as e:
       logger.error(f"Unexpected error: {e}")

Next Steps
----------

For more advanced patterns, see:

- :doc:`client_advanced` - Advanced client features
- :doc:`production_patterns` - Production-ready patterns
- :doc:`monitoring_analytics` - Monitoring and analytics
- :doc:`error_handling` - Error handling patterns 