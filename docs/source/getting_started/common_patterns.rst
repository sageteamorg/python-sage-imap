.. _common_patterns:

Common Usage Patterns
=====================

This comprehensive guide demonstrates common patterns and solutions for typical IMAP scenarios using Python Sage IMAP. These patterns are based on real-world use cases and provide tested, production-ready solutions with emphasis on **UID-based operations for reliability**.

**⚠️ IMPORTANT: All patterns use UIDs for reliable operations. Avoid sequence numbers in production!**

Email Processing Patterns
-------------------------

Modern Email Processing with UIDs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A robust pattern for processing incoming emails using the enhanced MessageSet with UID-based operations:

.. code-block:: python

   from sage_imap.services import IMAPClient, IMAPMailboxUIDService
   from sage_imap.helpers.search import IMAPSearchCriteria
   from sage_imap.helpers.enums import Flag, MessagePart
   from sage_imap.models.message import MessageSet
   import time
   import logging
   
   logger = logging.getLogger(__name__)
   
   class ModernEmailProcessor:
       def __init__(self, config):
           self.config = config
           self.processed_count = 0
           self.error_count = 0
       
       def process_incoming_emails(self):
           """Process new incoming emails using UID-based operations."""
           
           with IMAPClient(config=self.config) as client:
               # Use UID service for reliable operations
               uid_service = IMAPMailboxUIDService(client)
               uid_service.select("INBOX")
               
               while True:
                   try:
                       # Create MessageSet from search results (UIDs)
                       unread_criteria = IMAPSearchCriteria.UNSEEN
                       msg_set = uid_service.create_message_set_from_search(unread_criteria)
                       
                       if msg_set.is_empty():
                           logger.info("No new emails to process")
                           time.sleep(30)
                           continue
                       
                       logger.info(f"Found {len(msg_set)} new emails")
                       
                       # Process in batches for efficiency
                       result = uid_service.process_messages_in_batches(
                           msg_set,
                           self.handle_message,
                           batch_size=50
                       )
                       
                       logger.info(
                           f"Batch processing result: {result.successful_messages} processed, "
                           f"{result.failed_messages} failed"
                       )
                       
                       self.processed_count += result.successful_messages
                       self.error_count += result.failed_messages
                       
                       # Brief pause between processing cycles
                       time.sleep(5)
                       
                   except Exception as e:
                       logger.error(f"Error in email processing loop: {e}")
                       time.sleep(60)
       
       def handle_message(self, message):
           """Handle individual message with enhanced EmailMessage features."""
           try:
               # Use enhanced EmailMessage properties
               sender = str(message.from_address) if message.from_address else "Unknown"
               subject = message.subject
               
               # Process based on content and metadata
               if self.is_support_email(message):
                   self.handle_support_email(message)
               elif self.is_order_email(message):
                   self.handle_order_email(message)
               elif message.has_attachments():
                   self.handle_email_with_attachments(message)
               else:
                   self.handle_general_email(message)
               
               # Mark as processed using UID
               if message.uid:
                   msg_set = MessageSet.from_uids([message.uid], mailbox=message.mailbox)
                   # Flag operations would be handled by the service
                   
           except Exception as e:
               logger.error(f"Failed to handle message {message.uid}: {e}")
               raise
       
       def is_support_email(self, message):
           """Enhanced support email detection."""
           support_indicators = [
               "support", "help", "assistance", "issue", "problem",
               "bug", "error", "ticket", "complaint"
           ]
           
           # Check sender
           sender = str(message.from_address).lower() if message.from_address else ""
           if any(indicator in sender for indicator in support_indicators):
               return True
           
           # Check subject
           subject = message.subject.lower()
           if any(indicator in subject for indicator in support_indicators):
               return True
           
           # Check body content
           body = (message.plain_body + " " + message.html_body).lower()
           return any(indicator in body for indicator in support_indicators)
       
       def is_order_email(self, message):
           """Enhanced order email detection."""
           order_indicators = [
               "order", "purchase", "invoice", "receipt", "payment",
               "transaction", "confirmation", "shipment", "delivery"
           ]
           
           subject = message.subject.lower()
           body = (message.plain_body + " " + message.html_body).lower()
           
           return any(indicator in subject or indicator in body 
                     for indicator in order_indicators)
       
       def handle_support_email(self, message):
           """Handle support-related emails with attachment processing."""
           logger.info(f"Processing support email: {message.subject}")
           
           # Extract support ticket information
           ticket_data = {
               'uid': message.uid,
               'subject': message.subject,
               'sender': str(message.from_address),
               'date': message.date,
               'body': message.get_body_preview(500),
               'attachments': message.get_attachment_filenames(),
               'is_reply': message.is_reply(),
               'priority': self.determine_priority(message)
           }
           
           # Process attachments if present
           if message.has_attachments():
               self.process_support_attachments(message)
           
           # Create support ticket in external system
           self.create_support_ticket(ticket_data)
       
       def handle_order_email(self, message):
           """Handle order-related emails with enhanced parsing."""
           logger.info(f"Processing order email: {message.subject}")
           
           # Extract order information
           order_data = {
               'uid': message.uid,
               'order_number': self.extract_order_number(message.subject),
               'customer_email': str(message.from_address),
               'total_amount': self.extract_amount_from_body(message.plain_body),
               'items': self.extract_order_items(message.html_body),
               'date': message.date
           }
           
           # Process order in external system
           self.process_order(order_data)
       
       def handle_email_with_attachments(self, message):
           """Handle emails with attachments using enhanced features."""
           logger.info(f"Processing email with {len(message.attachments)} attachments")
           
           # Process each attachment
           for attachment in message.attachments:
               if attachment.is_image:
                   self.process_image_attachment(attachment, message)
               elif attachment.content_type == 'application/pdf':
                   self.process_pdf_attachment(attachment, message)
               else:
                   self.process_generic_attachment(attachment, message)
       
       def handle_general_email(self, message):
           """Handle general emails with content analysis."""
           logger.info(f"Processing general email: {message.subject}")
           
           # Perform content analysis
           analysis = {
               'sentiment': self.analyze_sentiment(message.plain_body),
               'language': self.detect_language(message.plain_body),
               'keywords': self.extract_keywords(message.plain_body),
               'entities': self.extract_entities(message.plain_body)
           }
           
           # Store or process based on analysis
           self.store_email_analysis(message, analysis)

Advanced Batch Processing with MessageSet
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Leveraging the enhanced MessageSet for efficient bulk operations:

.. code-block:: python

   from datetime import datetime, timedelta
   from sage_imap.services import IMAPClient, IMAPMailboxUIDService
   from sage_imap.helpers.search import IMAPSearchCriteria
   from sage_imap.models.message import MessageSet
   
   class AdvancedBulkProcessor:
       def __init__(self, config, batch_size=100):
           self.config = config
           self.batch_size = batch_size
       
       def smart_archive_emails(self, days_old=30, preserve_important=True):
           """Smart archiving with importance detection."""
           
           with IMAPClient(config=self.config) as client:
               uid_service = IMAPMailboxUIDService(client)
               uid_service.select("INBOX")
               
               # Create date-based search criteria
               cutoff_date = datetime.now() - timedelta(days=days_old)
               date_str = cutoff_date.strftime("%d-%b-%Y")
               
               # Build complex search criteria
               old_criteria = IMAPSearchCriteria.before(date_str)
               
               if preserve_important:
                   # Exclude flagged (important) emails
                   old_criteria = IMAPSearchCriteria.and_criteria(
                       old_criteria,
                       IMAPSearchCriteria.not_criteria(IMAPSearchCriteria.FLAGGED)
                   )
               
               # Create MessageSet from search
               old_msg_set = uid_service.create_message_set_from_search(old_criteria)
               
               if old_msg_set.is_empty():
                   logger.info("No old emails to archive")
                   return
               
               logger.info(f"Found {len(old_msg_set)} emails to archive")
               
               # Process in optimized batches
               for batch in old_msg_set.iter_batches(batch_size=self.batch_size):
                   try:
                       # Move batch to archive
                       move_result = uid_service.uid_move(batch, "INBOX/Archive")
                       
                       if move_result.success:
                           logger.info(f"Archived {len(batch)} emails")
                       else:
                           logger.error(f"Failed to archive batch: {move_result.error_message}")
                       
                       # Brief pause between batches
                       time.sleep(0.5)
                       
                   except Exception as e:
                       logger.error(f"Error processing batch: {e}")
       
       def intelligent_spam_cleanup(self):
           """Intelligent spam detection and cleanup."""
           
           with IMAPClient(config=self.config) as client:
               uid_service = IMAPMailboxUIDService(client)
               uid_service.select("INBOX")
               
               # Multiple criteria for spam detection
               spam_criteria = IMAPSearchCriteria.or_criteria(
                   # Subject patterns
                   IMAPSearchCriteria.subject("URGENT"),
                   IMAPSearchCriteria.subject("WINNER"),
                   IMAPSearchCriteria.subject("FREE"),
                   IMAPSearchCriteria.subject("MONEY"),
                   # Body patterns
                   IMAPSearchCriteria.body("lottery"),
                   IMAPSearchCriteria.body("inheritance"),
                   # Size patterns (very small or very large)
                   IMAPSearchCriteria.and_criteria(
                       IMAPSearchCriteria.larger(10 * 1024 * 1024),  # >10MB
                       IMAPSearchCriteria.body("click here")
                   )
               )
               
               potential_spam = uid_service.create_message_set_from_search(spam_criteria)
               
               if potential_spam.is_empty():
                   logger.info("No potential spam found")
                   return
               
               # Advanced spam filtering with message content analysis
               confirmed_spam = self.analyze_and_filter_spam(uid_service, potential_spam)
               
               if confirmed_spam and not confirmed_spam.is_empty():
                   # Move to spam folder
                   uid_service.uid_move(confirmed_spam, "INBOX/Spam")
                   logger.info(f"Moved {len(confirmed_spam)} spam emails")
       
       def analyze_and_filter_spam(self, uid_service, potential_spam):
           """Analyze messages to confirm spam status."""
           confirmed_spam_uids = []
           
           # Process in smaller batches for analysis
           for batch in potential_spam.iter_batches(batch_size=20):
               fetch_result = uid_service.uid_fetch(batch, MessagePart.RFC822)
               
               if not fetch_result.success:
                   continue
               
               messages = fetch_result.metadata.get('fetched_messages', [])
               
               for message in messages:
                   spam_score = self.calculate_spam_score(message)
                   if spam_score > 0.8:  # 80% confidence threshold
                       confirmed_spam_uids.append(message.uid)
           
           if confirmed_spam_uids:
               return MessageSet.from_uids(confirmed_spam_uids, mailbox="INBOX")
           
           return None
       
       def calculate_spam_score(self, message):
           """Calculate spam probability score."""
           score = 0.0
           
           # Check for common spam indicators
           spam_keywords = [
               'urgent', 'winner', 'congratulations', 'lottery', 'inheritance',
               'million dollars', 'free money', 'click here now', 'limited time'
           ]
           
           subject_lower = message.subject.lower()
           body_lower = (message.plain_body + " " + message.html_body).lower()
           
           # Subject analysis
           for keyword in spam_keywords:
               if keyword in subject_lower:
                   score += 0.2
           
           # Body analysis
           for keyword in spam_keywords:
               if keyword in body_lower:
                   score += 0.1
           
           # Check for excessive caps
           if sum(1 for c in message.subject if c.isupper()) > len(message.subject) * 0.7:
               score += 0.3
           
           # Check for suspicious sender patterns
           sender = str(message.from_address).lower() if message.from_address else ""
           if any(pattern in sender for pattern in ['noreply@', 'no-reply@', 'lottery@']):
               score += 0.2
           
           return min(score, 1.0)  # Cap at 1.0

Real-Time Email Monitoring with IDLE
------------------------------------

Socket-Based Real-Time Updates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Implement real-time email monitoring using IMAP IDLE command with socket-based solutions:

.. code-block:: python

   import socket
   import threading
   import time
   import select
   from sage_imap.services import IMAPClient, IMAPMailboxUIDService
   from sage_imap.helpers.search import IMAPSearchCriteria
   from sage_imap.models.message import MessageSet
   from queue import Queue
   import websocket
   import json
   
   class RealTimeEmailMonitor:
       def __init__(self, config):
           self.config = config
           self.is_monitoring = False
           self.event_queue = Queue()
           self.callbacks = []
           self.websocket_server = None
           
       def add_callback(self, callback):
           """Add callback for email events."""
           self.callbacks.append(callback)
       
       def start_idle_monitoring(self):
           """Start IMAP IDLE monitoring for real-time updates."""
           
           def idle_worker():
               with IMAPClient(config=self.config) as client:
                   uid_service = IMAPMailboxUIDService(client)
                   uid_service.select("INBOX")
                   
                   # Get initial state
                   initial_uids = set(
                       uid_service.create_message_set_from_search(
                           IMAPSearchCriteria.ALL
                       ).parsed_ids
                   )
                   
                   while self.is_monitoring:
                       try:
                           # Enter IDLE mode
                           client.idle()
                           
                           # Wait for server response or timeout
                           ready = select.select([client.sock], [], [], 30)  # 30 second timeout
                           
                           if ready[0]:
                               # Server sent update
                               response = client.response('IDLE')[1]
                               client.done()  # Exit IDLE
                               
                               # Check for new messages
                               current_uids = set(
                                   uid_service.create_message_set_from_search(
                                       IMAPSearchCriteria.ALL
                                   ).parsed_ids
                               )
                               
                               new_uids = current_uids - initial_uids
                               deleted_uids = initial_uids - current_uids
                               
                               # Process new messages
                               if new_uids:
                                   self.handle_new_messages(uid_service, list(new_uids))
                               
                               # Process deleted messages
                               if deleted_uids:
                                   self.handle_deleted_messages(list(deleted_uids))
                               
                               initial_uids = current_uids
                           else:
                               # Timeout - refresh IDLE
                               client.done()
                               
                       except Exception as e:
                           logger.error(f"IDLE monitoring error: {e}")
                           time.sleep(5)  # Wait before retry
           
           self.is_monitoring = True
           self.monitor_thread = threading.Thread(target=idle_worker, daemon=True)
           self.monitor_thread.start()
       
       def handle_new_messages(self, uid_service, new_uids):
           """Handle newly arrived messages."""
           try:
               msg_set = MessageSet.from_uids(new_uids, mailbox="INBOX")
               
               # Fetch new messages
               fetch_result = uid_service.uid_fetch(msg_set, MessagePart.RFC822)
               
               if fetch_result.success:
                   messages = fetch_result.metadata.get('fetched_messages', [])
                   
                   for message in messages:
                       event = {
                           'type': 'new_message',
                           'uid': message.uid,
                           'subject': message.subject,
                           'sender': str(message.from_address),
                           'timestamp': time.time(),
                           'has_attachments': message.has_attachments(),
                           'size': message.size
                       }
                       
                       # Trigger callbacks
                       for callback in self.callbacks:
                           try:
                               callback(event)
                           except Exception as e:
                               logger.error(f"Callback error: {e}")
                       
                       # Add to event queue
                       self.event_queue.put(event)
                       
                       # Send WebSocket notification
                       self.send_websocket_notification(event)
                       
           except Exception as e:
               logger.error(f"Error handling new messages: {e}")
       
       def handle_deleted_messages(self, deleted_uids):
           """Handle deleted messages."""
           for uid in deleted_uids:
               event = {
                   'type': 'message_deleted',
                   'uid': uid,
                   'timestamp': time.time()
               }
               
               # Trigger callbacks
               for callback in self.callbacks:
                   try:
                       callback(event)
                   except Exception as e:
                       logger.error(f"Callback error: {e}")
               
               self.event_queue.put(event)
               self.send_websocket_notification(event)
       
       def stop_monitoring(self):
           """Stop IDLE monitoring."""
           self.is_monitoring = False
           if hasattr(self, 'monitor_thread'):
               self.monitor_thread.join(timeout=5)

WebSocket Integration for Real-Time Notifications
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create WebSocket server for real-time email notifications:

.. code-block:: python

   import asyncio
   import websockets
   import json
   from threading import Thread
   
   class EmailWebSocketServer:
       def __init__(self, host='localhost', port=8765):
           self.host = host
           self.port = port
           self.clients = set()
           self.server = None
           
       async def register_client(self, websocket, path):
           """Register new WebSocket client."""
           self.clients.add(websocket)
           logger.info(f"Client connected: {websocket.remote_address}")
           
           try:
               # Keep connection alive
               await websocket.wait_closed()
           finally:
               self.clients.remove(websocket)
               logger.info(f"Client disconnected: {websocket.remote_address}")
       
       async def broadcast_event(self, event):
           """Broadcast event to all connected clients."""
           if self.clients:
               message = json.dumps(event)
               # Create list copy to avoid set modification during iteration
               clients_copy = self.clients.copy()
               
               for client in clients_copy:
                   try:
                       await client.send(message)
                   except websockets.exceptions.ConnectionClosed:
                       self.clients.discard(client)
                   except Exception as e:
                       logger.error(f"Error sending to client: {e}")
                       self.clients.discard(client)
       
       def start_server(self):
           """Start WebSocket server in background thread."""
           def run_server():
               loop = asyncio.new_event_loop()
               asyncio.set_event_loop(loop)
               
               self.server = websockets.serve(
                   self.register_client,
                   self.host,
                   self.port
               )
               
               loop.run_until_complete(self.server)
               loop.run_forever()
           
           self.server_thread = Thread(target=run_server, daemon=True)
           self.server_thread.start()
           logger.info(f"WebSocket server started on {self.host}:{self.port}")
       
       def send_notification(self, event):
           """Send notification to WebSocket clients."""
           # This needs to be called from the main thread
           asyncio.run_coroutine_threadsafe(
               self.broadcast_event(event),
               self.server_thread._target.__globals__.get('loop')
           )

Complete Real-Time Email System
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Integrate IDLE monitoring with WebSocket notifications:

.. code-block:: python

   class CompleteRealTimeEmailSystem:
       def __init__(self, config):
           self.config = config
           self.email_monitor = RealTimeEmailMonitor(config)
           self.websocket_server = EmailWebSocketServer()
           self.notification_handlers = []
           
       def add_notification_handler(self, handler):
           """Add custom notification handler."""
           self.notification_handlers.append(handler)
       
       def start_system(self):
           """Start the complete real-time email system."""
           
           # Start WebSocket server
           self.websocket_server.start_server()
           
           # Add email event callback
           self.email_monitor.add_callback(self.handle_email_event)
           
           # Start IDLE monitoring
           self.email_monitor.start_idle_monitoring()
           
           logger.info("Real-time email system started")
       
       def handle_email_event(self, event):
           """Handle email events with notifications."""
           
           # Enhance event with additional processing
           if event['type'] == 'new_message':
               # Add priority classification
               event['priority'] = self.classify_priority(event)
               
               # Add category classification
               event['category'] = self.classify_category(event)
               
               # Add notification preferences
               event['notification_channels'] = self.get_notification_channels(event)
           
           # Send WebSocket notification
           self.websocket_server.send_notification(event)
           
           # Send to custom notification handlers
           for handler in self.notification_handlers:
               try:
                   handler(event)
               except Exception as e:
                   logger.error(f"Notification handler error: {e}")
           
           # Send platform-specific notifications
           self.send_platform_notifications(event)
       
       def classify_priority(self, event):
           """Classify email priority based on content."""
           urgent_keywords = ['urgent', 'asap', 'immediate', 'critical', 'emergency']
           
           subject_lower = event['subject'].lower()
           
           if any(keyword in subject_lower for keyword in urgent_keywords):
               return 'high'
           elif event['sender'].endswith('@yourcompany.com'):
               return 'medium'
           else:
               return 'low'
       
       def classify_category(self, event):
           """Classify email category."""
           subject = event['subject'].lower()
           sender = event['sender'].lower()
           
           if 'support' in subject or 'help' in subject:
               return 'support'
           elif 'order' in subject or 'invoice' in subject:
               return 'sales'
           elif 'meeting' in subject or 'calendar' in subject:
               return 'calendar'
           elif 'newsletter' in sender or 'noreply' in sender:
               return 'newsletter'
           else:
               return 'general'
       
       def get_notification_channels(self, event):
           """Determine notification channels based on event."""
           channels = ['websocket']  # Always include WebSocket
           
           if event['priority'] == 'high':
               channels.extend(['push', 'email', 'sms'])
           elif event['priority'] == 'medium':
               channels.extend(['push', 'email'])
           
           return channels
       
       def send_platform_notifications(self, event):
           """Send notifications to various platforms."""
           
           channels = event.get('notification_channels', [])
           
           if 'push' in channels:
               self.send_push_notification(event)
           
           if 'email' in channels:
               self.send_email_notification(event)
           
           if 'sms' in channels:
               self.send_sms_notification(event)
           
           if 'slack' in channels:
               self.send_slack_notification(event)
       
       def send_push_notification(self, event):
           """Send push notification (implement with your preferred service)."""
           logger.info(f"Sending push notification for email: {event['subject']}")
       
       def send_email_notification(self, event):
           """Send email notification to admin."""
           logger.info(f"Sending email notification for: {event['subject']}")
       
       def send_sms_notification(self, event):
           """Send SMS notification for high-priority emails."""
           logger.info(f"Sending SMS notification for urgent email: {event['subject']}")
       
       def send_slack_notification(self, event):
           """Send Slack notification."""
           logger.info(f"Sending Slack notification for: {event['subject']}")
       
       def stop_system(self):
           """Stop the real-time email system."""
           self.email_monitor.stop_monitoring()
           logger.info("Real-time email system stopped")

Advanced Content Processing Patterns
------------------------------------

AI-Powered Email Classification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Integrate machine learning for intelligent email processing:

.. code-block:: python

   import numpy as np
   from sklearn.feature_extraction.text import TfidfVectorizer
   from sklearn.naive_bayes import MultinomialNB
   from sklearn.pipeline import Pipeline
   import pickle
   import re
   
   class AIEmailClassifier:
       def __init__(self, config):
           self.config = config
           self.classifier = None
           self.categories = [
               'support', 'sales', 'marketing', 'spam', 
               'newsletter', 'personal', 'urgent', 'general'
           ]
           self.load_or_train_model()
       
       def load_or_train_model(self):
           """Load existing model or train new one."""
           try:
               with open('email_classifier.pkl', 'rb') as f:
                   self.classifier = pickle.load(f)
               logger.info("Loaded existing email classification model")
           except FileNotFoundError:
               logger.info("Training new email classification model")
               self.train_model()
       
       def train_model(self):
           """Train email classification model."""
           # In practice, you'd load training data from a database
           training_data = self.get_training_data()
           
           if not training_data:
               # Create simple rule-based classifier as fallback
               self.classifier = self.create_rule_based_classifier()
               return
           
           texts, labels = zip(*training_data)
           
           self.classifier = Pipeline([
               ('tfidf', TfidfVectorizer(
                   max_features=10000,
                   stop_words='english',
                   ngram_range=(1, 2)
               )),
               ('nb', MultinomialNB())
           ])
           
           self.classifier.fit(texts, labels)
           
           # Save trained model
           with open('email_classifier.pkl', 'wb') as f:
               pickle.dump(self.classifier, f)
       
       def get_training_data(self):
           """Get training data for the classifier."""
           # This would typically load from a database of labeled emails
           # For demo purposes, return empty list to use rule-based classifier
           return []
       
       def create_rule_based_classifier(self):
           """Create simple rule-based classifier."""
           
           class RuleBasedClassifier:
               def predict(self, texts):
                   predictions = []
                   for text in texts:
                       predictions.append(self._classify_text(text))
                   return predictions
               
               def _classify_text(self, text):
                   text_lower = text.lower()
                   
                   # Support keywords
                   if any(word in text_lower for word in ['support', 'help', 'issue', 'problem', 'bug']):
                       return 'support'
                   
                   # Sales keywords
                   elif any(word in text_lower for word in ['order', 'purchase', 'buy', 'sale', 'price']):
                       return 'sales'
                   
                   # Marketing keywords
                   elif any(word in text_lower for word in ['offer', 'deal', 'discount', 'promotion']):
                       return 'marketing'
                   
                   # Urgent keywords
                   elif any(word in text_lower for word in ['urgent', 'asap', 'immediate', 'critical']):
                       return 'urgent'
                   
                   # Spam keywords
                   elif any(word in text_lower for word in ['lottery', 'winner', 'free money', 'inheritance']):
                       return 'spam'
                   
                   # Newsletter indicators
                   elif any(word in text_lower for word in ['newsletter', 'unsubscribe', 'mailing list']):
                       return 'newsletter'
                   
                   else:
                       return 'general'
           
           return RuleBasedClassifier()
       
       def classify_email(self, message):
           """Classify email message."""
           # Combine subject and body for classification
           text = f"{message.subject} {message.plain_body}"
           
           # Clean text
           text = self.clean_text(text)
           
           # Predict category
           prediction = self.classifier.predict([text])[0]
           
           # Get confidence score if available
           confidence = 0.8  # Default confidence for rule-based
           if hasattr(self.classifier, 'predict_proba'):
               probabilities = self.classifier.predict_proba([text])[0]
               confidence = max(probabilities)
           
           return {
               'category': prediction,
               'confidence': confidence,
               'categories': self.categories
           }
       
       def clean_text(self, text):
           """Clean text for classification."""
           # Remove HTML tags
           text = re.sub(r'<[^>]+>', '', text)
           
           # Remove extra whitespace
           text = re.sub(r'\s+', ' ', text)
           
           # Remove special characters
           text = re.sub(r'[^\w\s]', '', text)
           
           return text.strip()

Advanced Email Processing with AI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Comprehensive email processing with AI classification and content extraction:

.. code-block:: python

   import json
   from datetime import datetime
   from sage_imap.services import IMAPClient, IMAPMailboxUIDService
   from sage_imap.helpers.search import IMAPSearchCriteria
   from sage_imap.models.message import MessageSet
   from sage_imap.helpers.enums import MessagePart
   
   class IntelligentEmailProcessor:
       def __init__(self, config):
           self.config = config
           self.ai_classifier = AIEmailClassifier(config)
           self.content_extractors = {
               'support': self.extract_support_info,
               'sales': self.extract_sales_info,
               'urgent': self.extract_urgent_info,
               'spam': self.extract_spam_info
           }
       
       def process_emails_intelligently(self):
           """Process emails with AI classification and smart routing."""
           
           with IMAPClient(config=self.config) as client:
               uid_service = IMAPMailboxUIDService(client)
               uid_service.select("INBOX")
               
               # Get unprocessed emails
               unprocessed_criteria = IMAPSearchCriteria.and_criteria(
                   IMAPSearchCriteria.UNSEEN,
                   IMAPSearchCriteria.not_criteria(
                       IMAPSearchCriteria.header("X-Processed", "true")
                   )
               )
               
               msg_set = uid_service.create_message_set_from_search(unprocessed_criteria)
               
               if msg_set.is_empty():
                   logger.info("No unprocessed emails found")
                   return
               
               # Process with AI classification
               result = uid_service.process_messages_in_batches(
                   msg_set,
                   self.process_single_email_with_ai,
                   batch_size=25
               )
               
               logger.info(f"AI processing complete: {result.successful_messages} processed")
       
       def process_single_email_with_ai(self, message):
           """Process single email with AI classification."""
           
           # Classify email
           classification = self.ai_classifier.classify_email(message)
           category = classification['category']
           confidence = classification['confidence']
           
           logger.info(f"Email classified as '{category}' with {confidence:.2f} confidence")
           
           # Extract category-specific information
           extracted_info = {}
           if category in self.content_extractors:
               extracted_info = self.content_extractors[category](message)
           
           # Create processing record
           processing_record = {
               'uid': message.uid,
               'timestamp': datetime.now().isoformat(),
               'classification': classification,
               'extracted_info': extracted_info,
               'sender': str(message.from_address),
               'subject': message.subject,
               'size': message.size,
               'has_attachments': message.has_attachments()
           }
           
           # Route email based on classification
           self.route_email_by_category(message, category, confidence)
           
           # Store processing results
           self.store_processing_results(processing_record)
           
           # Mark as processed
           self.mark_as_processed(message)
       
       def extract_support_info(self, message):
           """Extract support-specific information."""
           info = {}
           
           # Extract ticket ID if present
           ticket_pattern = r'(?:ticket|case|id)[\s#:]*(\w+)'
           match = re.search(ticket_pattern, message.subject, re.IGNORECASE)
           if match:
               info['ticket_id'] = match.group(1)
           
           # Extract urgency level
           urgency_keywords = {
               'critical': ['critical', 'down', 'outage', 'urgent'],
               'high': ['high', 'important', 'asap'],
               'medium': ['medium', 'normal'],
               'low': ['low', 'minor', 'when possible']
           }
           
           text = (message.subject + " " + message.plain_body).lower()
           for level, keywords in urgency_keywords.items():
               if any(keyword in text for keyword in keywords):
                   info['urgency'] = level
                   break
           else:
               info['urgency'] = 'medium'
           
           # Extract contact information
           info['customer_email'] = str(message.from_address)
           
           # Extract issue description
           if message.plain_body:
               # Get first paragraph as issue summary
               paragraphs = message.plain_body.split('\n\n')
               if paragraphs:
                   info['issue_summary'] = paragraphs[0][:500]
           
           return info
       
       def extract_sales_info(self, message):
           """Extract sales-specific information."""
           info = {}
           
           # Extract order numbers
           order_pattern = r'(?:order|invoice)[\s#:]*(\w+)'
           match = re.search(order_pattern, message.subject, re.IGNORECASE)
           if match:
               info['order_number'] = match.group(1)
           
           # Extract monetary amounts
           amount_pattern = r'\$[\d,]+\.?\d*'
           amounts = re.findall(amount_pattern, message.plain_body)
           if amounts:
               info['amounts'] = amounts
           
           # Extract product mentions
           product_keywords = ['product', 'item', 'service', 'subscription']
           text = message.plain_body.lower()
           for keyword in product_keywords:
               if keyword in text:
                   info['product_related'] = True
                   break
           
           return info
       
       def extract_urgent_info(self, message):
           """Extract urgent email information."""
           info = {}
           
           # Extract deadline information
           deadline_pattern = r'(?:deadline|due|by)[\s:]*(\w+\s+\d+)'
           match = re.search(deadline_pattern, message.plain_body, re.IGNORECASE)
           if match:
               info['deadline'] = match.group(1)
           
           # Extract action items
           action_keywords = ['action', 'todo', 'task', 'required', 'need']
           text = message.plain_body.lower()
           info['requires_action'] = any(keyword in text for keyword in action_keywords)
           
           return info
       
       def extract_spam_info(self, message):
           """Extract spam indicators for analysis."""
           info = {}
           
           # Count spam indicators
           spam_indicators = [
               'lottery', 'winner', 'congratulations', 'free money',
               'click here', 'urgent', 'limited time', 'act now'
           ]
           
           text = (message.subject + " " + message.plain_body).lower()
           info['spam_indicator_count'] = sum(
               1 for indicator in spam_indicators if indicator in text
           )
           
           # Check for suspicious URLs
           url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
           urls = re.findall(url_pattern, message.html_body)
           info['url_count'] = len(urls)
           
           return info
       
       def route_email_by_category(self, message, category, confidence):
           """Route email to appropriate folder based on category."""
           
           # Only auto-route if confidence is high enough
           if confidence < 0.7:
               logger.info(f"Low confidence ({confidence:.2f}), leaving in INBOX")
               return
           
           folder_mapping = {
               'support': 'INBOX/Support',
               'sales': 'INBOX/Sales',
               'marketing': 'INBOX/Marketing',
               'spam': 'INBOX/Spam',
               'newsletter': 'INBOX/Newsletter',
               'urgent': 'INBOX/Urgent'
           }
           
           target_folder = folder_mapping.get(category)
           if target_folder and message.uid:
               try:
                   with IMAPClient(config=self.config) as client:
                       uid_service = IMAPMailboxUIDService(client)
                       uid_service.select("INBOX")
                       
                       msg_set = MessageSet.from_uids([message.uid], mailbox="INBOX")
                       uid_service.uid_move(msg_set, target_folder)
                       
                       logger.info(f"Moved email to {target_folder}")
                       
               except Exception as e:
                   logger.error(f"Failed to move email: {e}")
       
       def store_processing_results(self, record):
           """Store processing results for analysis."""
           # In practice, this would store to a database
           logger.info(f"Storing processing record for UID {record['uid']}")
       
       def mark_as_processed(self, message):
           """Mark email as processed."""
           # In practice, this would add a custom header or flag
           logger.info(f"Marked email {message.uid} as processed")

Webhook Integration Patterns
----------------------------

Email-to-Webhook Bridge
~~~~~~~~~~~~~~~~~~~~~~~

Forward email events to external webhooks for integration:

.. code-block:: python

   import requests
   import json
   import hmac
   import hashlib
   from urllib.parse import urljoin
   
   class EmailWebhookBridge:
       def __init__(self, config, webhook_config):
           self.config = config
           self.webhook_config = webhook_config
           self.retry_attempts = 3
           self.retry_delay = 1.0
       
       def setup_email_to_webhook_forwarding(self):
           """Set up forwarding of email events to webhooks."""
           
           # Start real-time monitoring
           monitor = RealTimeEmailMonitor(self.config)
           monitor.add_callback(self.forward_to_webhook)
           monitor.start_idle_monitoring()
           
           logger.info("Email-to-webhook forwarding started")
       
       def forward_to_webhook(self, event):
           """Forward email event to configured webhooks."""
           
           # Enhance event with additional metadata
           enhanced_event = self.enhance_event(event)
           
           # Send to each configured webhook
           for webhook in self.webhook_config.get('endpoints', []):
               self.send_webhook(webhook, enhanced_event)
       
       def enhance_event(self, event):
           """Enhance event with additional metadata."""
           enhanced = event.copy()
           
           # Add metadata
           enhanced['webhook_metadata'] = {
               'version': '1.0',
               'timestamp': time.time(),
               'source': 'python-sage-imap',
               'event_id': f"evt_{int(time.time())}_{event.get('uid', 'unknown')}"
           }
           
           # Add email content if needed (for new messages)
           if event['type'] == 'new_message' and event.get('uid'):
               enhanced = self.add_email_content(enhanced)
           
           return enhanced
       
       def add_email_content(self, event):
           """Add full email content to event."""
           try:
               with IMAPClient(config=self.config) as client:
                   uid_service = IMAPMailboxUIDService(client)
                   uid_service.select("INBOX")
                   
                   msg_set = MessageSet.from_uids([event['uid']], mailbox="INBOX")
                   fetch_result = uid_service.uid_fetch(msg_set, MessagePart.RFC822)
                   
                   if fetch_result.success:
                       messages = fetch_result.metadata.get('fetched_messages', [])
                       if messages:
                           message = messages[0]
                           event['email_content'] = {
                               'plain_body': message.plain_body,
                               'html_body': message.html_body,
                               'headers': dict(message.headers),
                               'attachments': [
                                   {
                                       'filename': att.filename,
                                       'content_type': att.content_type,
                                       'size': att.size
                                   }
                                   for att in message.attachments
                               ]
                           }
           except Exception as e:
               logger.error(f"Failed to add email content: {e}")
           
           return event
       
       def send_webhook(self, webhook_config, event):
           """Send event to webhook endpoint."""
           
           for attempt in range(self.retry_attempts):
               try:
                   # Prepare payload
                   payload = self.prepare_payload(webhook_config, event)
                   
                   # Prepare headers
                   headers = {
                       'Content-Type': 'application/json',
                       'User-Agent': 'python-sage-imap/1.0'
                   }
                   
                   # Add signature if secret is configured
                   if webhook_config.get('secret'):
                       signature = self.generate_signature(
                           webhook_config['secret'],
                           json.dumps(payload)
                       )
                       headers['X-Signature'] = signature
                   
                   # Send request
                   response = requests.post(
                       webhook_config['url'],
                       json=payload,
                       headers=headers,
                       timeout=30
                   )
                   
                   response.raise_for_status()
                   
                   logger.info(f"Webhook sent successfully to {webhook_config['url']}")
                   return
                   
               except requests.exceptions.RequestException as e:
                   logger.warning(f"Webhook attempt {attempt + 1} failed: {e}")
                   if attempt < self.retry_attempts - 1:
                       time.sleep(self.retry_delay * (2 ** attempt))
                   else:
                       logger.error(f"Failed to send webhook after {self.retry_attempts} attempts")
       
       def prepare_payload(self, webhook_config, event):
           """Prepare webhook payload."""
           payload = {
               'event': event,
               'webhook_config': {
                   'name': webhook_config.get('name', 'unnamed'),
                   'version': webhook_config.get('version', '1.0')
               }
           }
           
           # Filter sensitive data if configured
           if webhook_config.get('filter_sensitive', True):
               payload = self.filter_sensitive_data(payload)
           
           return payload
       
       def filter_sensitive_data(self, payload):
           """Filter sensitive data from payload."""
           # Remove or mask sensitive information
           if 'email_content' in payload.get('event', {}):
               content = payload['event']['email_content']
               
               # Mask email bodies if they contain sensitive patterns
               sensitive_patterns = [
                   r'\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b',  # Credit card
                   r'\b\d{3}-\d{2}-\d{4}\b',              # SSN
                   r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Email
               ]
               
               for pattern in sensitive_patterns:
                   content['plain_body'] = re.sub(pattern, '[REDACTED]', content['plain_body'])
                   content['html_body'] = re.sub(pattern, '[REDACTED]', content['html_body'])
           
           return payload
       
       def generate_signature(self, secret, payload):
           """Generate HMAC signature for webhook security."""
           signature = hmac.new(
               secret.encode('utf-8'),
               payload.encode('utf-8'),
               hashlib.sha256
           ).hexdigest()
           
           return f"sha256={signature}"

Security and Authentication Patterns
------------------------------------

Secure Email Processing
~~~~~~~~~~~~~~~~~~~~~~~

Implement secure email processing with encryption and authentication:

.. code-block:: python

   import ssl
   import keyring
   from cryptography.fernet import Fernet
   from cryptography.hazmat.primitives import hashes
   from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
   import base64
   import os
   
   class SecureEmailProcessor:
       def __init__(self, config):
           self.config = config
           self.encryption_key = self.get_or_create_encryption_key()
           self.cipher_suite = Fernet(self.encryption_key)
       
       def get_or_create_encryption_key(self):
           """Get or create encryption key for sensitive data."""
           try:
               # Try to get existing key from keyring
               key = keyring.get_password("sage_imap", "encryption_key")
               if key:
                   return key.encode()
           except Exception:
               pass
           
           # Generate new key
           password = os.environ.get('IMAP_ENCRYPTION_PASSWORD', 'default_password')
           salt = os.urandom(16)
           
           kdf = PBKDF2HMAC(
               algorithm=hashes.SHA256(),
               length=32,
               salt=salt,
               iterations=100000,
           )
           
           key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
           
           # Store in keyring
           try:
               keyring.set_password("sage_imap", "encryption_key", key.decode())
           except Exception:
               logger.warning("Could not store encryption key in keyring")
           
           return key
       
       def create_secure_connection(self):
           """Create secure IMAP connection with enhanced SSL."""
           
           # Enhanced SSL context
           ssl_context = ssl.create_default_context()
           ssl_context.check_hostname = True
           ssl_context.verify_mode = ssl.CERT_REQUIRED
           
           # Set minimum TLS version
           ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
           
           # Enhanced cipher configuration
           ssl_context.set_ciphers('ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:RSA+AESGCM:RSA+AES:!aNULL:!MD5:!DSS')
           
           # Create connection with enhanced security
           config = self.config.copy()
           config['ssl_context'] = ssl_context
           
           return IMAPClient(config=config)
       
       def process_emails_securely(self):
           """Process emails with enhanced security measures."""
           
           with self.create_secure_connection() as client:
               uid_service = IMAPMailboxUIDService(client)
               uid_service.select("INBOX")
               
               # Get emails with secure criteria
               secure_criteria = IMAPSearchCriteria.and_criteria(
                   IMAPSearchCriteria.UNSEEN,
                   IMAPSearchCriteria.header("X-Security-Level", "high")
               )
               
               msg_set = uid_service.create_message_set_from_search(secure_criteria)
               
               if not msg_set.is_empty():
                   # Process with security measures
                   result = uid_service.process_messages_in_batches(
                       msg_set,
                       self.process_secure_email,
                       batch_size=10  # Smaller batches for security
                   )
                   
                   logger.info(f"Securely processed {result.successful_messages} emails")
       
       def process_secure_email(self, message):
           """Process email with security measures."""
           
           # Encrypt sensitive content
           encrypted_data = self.encrypt_email_content(message)
           
           # Log security event
           self.log_security_event({
               'event': 'secure_email_processed',
               'uid': message.uid,
               'sender': str(message.from_address),
               'timestamp': time.time(),
               'security_level': self.assess_security_level(message)
           })
           
           # Store encrypted data
           self.store_encrypted_email(message.uid, encrypted_data)
       
       def encrypt_email_content(self, message):
           """Encrypt sensitive email content."""
           
           sensitive_content = {
               'subject': message.subject,
               'body': message.plain_body,
               'sender': str(message.from_address),
               'headers': dict(message.headers)
           }
           
           # Convert to JSON and encrypt
           json_content = json.dumps(sensitive_content)
           encrypted_content = self.cipher_suite.encrypt(json_content.encode())
           
           return encrypted_content
       
       def decrypt_email_content(self, encrypted_data):
           """Decrypt email content."""
           try:
               decrypted_data = self.cipher_suite.decrypt(encrypted_data)
               return json.loads(decrypted_data.decode())
           except Exception as e:
               logger.error(f"Failed to decrypt email content: {e}")
               return None
       
       def assess_security_level(self, message):
           """Assess security level of email."""
           
           # Check for security indicators
           security_keywords = [
               'confidential', 'sensitive', 'classified', 'private',
               'secure', 'encrypted', 'password', 'credentials'
           ]
           
           content = (message.subject + " " + message.plain_body).lower()
           
           if any(keyword in content for keyword in security_keywords):
               return 'high'
           elif message.has_attachments():
               return 'medium'
           else:
               return 'low'
       
       def log_security_event(self, event):
           """Log security-related events."""
           # Implement secure logging
           logger.info(f"Security event: {event['event']} for UID {event['uid']}")
       
       def store_encrypted_email(self, uid, encrypted_data):
           """Store encrypted email data."""
           # Implement secure storage
           logger.info(f"Stored encrypted email data for UID {uid}")

Performance Monitoring and Analytics
------------------------------------

Email Processing Analytics
~~~~~~~~~~~~~~~~~~~~~~~~~~

Comprehensive monitoring and analytics for email processing:

.. code-block:: python

   import time
   from collections import defaultdict, deque
   from datetime import datetime, timedelta
   import threading
   import json
   
   class EmailProcessingAnalytics:
       def __init__(self):
           self.metrics = defaultdict(lambda: defaultdict(int))
           self.performance_data = defaultdict(list)
           self.error_tracking = defaultdict(list)
           self.processing_times = deque(maxlen=1000)
           self.hourly_stats = defaultdict(lambda: defaultdict(int))
           self.lock = threading.Lock()
       
       def record_email_processed(self, message, processing_time, category=None):
           """Record email processing metrics."""
           with self.lock:
               current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
               
               # Basic metrics
               self.metrics['total']['processed'] += 1
               self.metrics['performance']['total_time'] += processing_time
               self.processing_times.append(processing_time)
               
               # Category metrics
               if category:
                   self.metrics['categories'][category] += 1
               
               # Hourly metrics
               self.hourly_stats[current_hour]['processed'] += 1
               self.hourly_stats[current_hour]['total_time'] += processing_time
               
               # Sender metrics
               sender = str(message.from_address) if message.from_address else "unknown"
               sender_domain = sender.split('@')[-1] if '@' in sender else sender
               self.metrics['senders'][sender_domain] += 1
               
               # Size metrics
               if message.size:
                   size_category = self.categorize_size(message.size)
                   self.metrics['sizes'][size_category] += 1
               
               # Attachment metrics
               if message.has_attachments():
                   self.metrics['attachments']['with_attachments'] += 1
                   self.metrics['attachments']['total_attachments'] += len(message.attachments)
               else:
                   self.metrics['attachments']['without_attachments'] += 1
       
       def record_error(self, error_type, message, details=None):
           """Record processing errors."""
           with self.lock:
               error_record = {
                   'timestamp': datetime.now().isoformat(),
                   'error_type': error_type,
                   'message_uid': getattr(message, 'uid', None),
                   'message_subject': getattr(message, 'subject', None),
                   'details': details
               }
               
               self.error_tracking[error_type].append(error_record)
               self.metrics['errors'][error_type] += 1
       
       def categorize_size(self, size):
           """Categorize email by size."""
           if size < 1024:  # < 1KB
               return 'tiny'
           elif size < 10 * 1024:  # < 10KB
               return 'small'
           elif size < 100 * 1024:  # < 100KB
               return 'medium'
           elif size < 1024 * 1024:  # < 1MB
               return 'large'
           else:  # >= 1MB
               return 'huge'
       
       def get_performance_summary(self):
           """Get performance summary."""
           with self.lock:
               if not self.processing_times:
                   return {}
               
               times = list(self.processing_times)
               times.sort()
               
               return {
                   'total_processed': self.metrics['total']['processed'],
                   'total_errors': sum(self.metrics['errors'].values()),
                   'average_processing_time': sum(times) / len(times),
                   'median_processing_time': times[len(times) // 2],
                   'p95_processing_time': times[int(len(times) * 0.95)],
                   'min_processing_time': min(times),
                   'max_processing_time': max(times),
                   'error_rate': sum(self.metrics['errors'].values()) / max(self.metrics['total']['processed'], 1)
               }
       
       def get_hourly_trends(self, hours=24):
           """Get hourly processing trends."""
           with self.lock:
               now = datetime.now().replace(minute=0, second=0, microsecond=0)
               trends = []
               
               for i in range(hours):
                   hour = now - timedelta(hours=i)
                   stats = self.hourly_stats.get(hour, {'processed': 0, 'total_time': 0})
                   
                   avg_time = 0
                   if stats['processed'] > 0:
                       avg_time = stats['total_time'] / stats['processed']
                   
                   trends.append({
                       'hour': hour.isoformat(),
                       'processed': stats['processed'],
                       'average_time': avg_time
                   })
               
               return list(reversed(trends))
       
       def get_category_distribution(self):
           """Get email category distribution."""
           with self.lock:
               total = sum(self.metrics['categories'].values())
               if total == 0:
                   return {}
               
               return {
                   category: (count / total) * 100
                   for category, count in self.metrics['categories'].items()
               }
       
       def get_top_senders(self, limit=10):
           """Get top email senders by volume."""
           with self.lock:
               senders = list(self.metrics['senders'].items())
               senders.sort(key=lambda x: x[1], reverse=True)
               return senders[:limit]
       
       def get_error_summary(self):
           """Get error summary."""
           with self.lock:
               return {
                   'error_counts': dict(self.metrics['errors']),
                   'recent_errors': {
                       error_type: errors[-5:]  # Last 5 errors of each type
                       for error_type, errors in self.error_tracking.items()
                   }
               }
       
       def export_analytics(self, filepath):
           """Export analytics to JSON file."""
           with self.lock:
               analytics_data = {
                   'export_timestamp': datetime.now().isoformat(),
                   'performance_summary': self.get_performance_summary(),
                   'hourly_trends': self.get_hourly_trends(),
                   'category_distribution': self.get_category_distribution(),
                   'top_senders': self.get_top_senders(),
                   'error_summary': self.get_error_summary(),
                   'size_distribution': dict(self.metrics['sizes']),
                   'attachment_stats': dict(self.metrics['attachments'])
               }
               
               with open(filepath, 'w') as f:
                   json.dump(analytics_data, f, indent=2, default=str)

Integration Examples
--------------------

Database Integration Pattern
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Integrate email processing with database storage:

.. code-block:: python

   import sqlite3
   from contextlib import contextmanager
   from datetime import datetime
   
   class EmailDatabaseIntegration:
       def __init__(self, db_path):
           self.db_path = db_path
           self.init_database()
       
       def init_database(self):
           """Initialize database schema."""
           with self.get_db_connection() as conn:
               conn.executescript("""
                   CREATE TABLE IF NOT EXISTS emails (
                       uid INTEGER PRIMARY KEY,
                       message_id TEXT UNIQUE,
                       subject TEXT,
                       sender TEXT,
                       recipients TEXT,
                       date_received TIMESTAMP,
                       date_processed TIMESTAMP,
                       size INTEGER,
                       category TEXT,
                       priority TEXT,
                       has_attachments BOOLEAN,
                       processing_status TEXT,
                       error_message TEXT
                   );
                   
                   CREATE TABLE IF NOT EXISTS email_content (
                       uid INTEGER PRIMARY KEY,
                       plain_body TEXT,
                       html_body TEXT,
                       headers TEXT,
                       FOREIGN KEY (uid) REFERENCES emails (uid)
                   );
                   
                   CREATE TABLE IF NOT EXISTS attachments (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       email_uid INTEGER,
                       filename TEXT,
                       content_type TEXT,
                       size INTEGER,
                       file_path TEXT,
                       FOREIGN KEY (email_uid) REFERENCES emails (uid)
                   );
                   
                   CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails(sender);
                   CREATE INDEX IF NOT EXISTS idx_emails_date ON emails(date_received);
                   CREATE INDEX IF NOT EXISTS idx_emails_category ON emails(category);
               """)
       
       @contextmanager
       def get_db_connection(self):
           """Get database connection with context management."""
           conn = sqlite3.connect(self.db_path)
           conn.row_factory = sqlite3.Row
           try:
               yield conn
               conn.commit()
           except Exception:
               conn.rollback()
               raise
           finally:
               conn.close()
       
       def store_email(self, message, category=None, priority=None):
           """Store email in database."""
           with self.get_db_connection() as conn:
               # Store main email record
               conn.execute("""
                   INSERT OR REPLACE INTO emails (
                       uid, message_id, subject, sender, recipients,
                       date_received, date_processed, size, category,
                       priority, has_attachments, processing_status
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               """, (
                   message.uid,
                   message.message_id,
                   message.subject,
                   str(message.from_address),
                   json.dumps([str(addr) for addr in message.all_recipients]),
                   message.date,
                   datetime.now().isoformat(),
                   message.size,
                   category,
                   priority,
                   message.has_attachments(),
                   'processed'
               ))
               
               # Store email content
               conn.execute("""
                   INSERT OR REPLACE INTO email_content (
                       uid, plain_body, html_body, headers
                   ) VALUES (?, ?, ?, ?)
               """, (
                   message.uid,
                   message.plain_body,
                   message.html_body,
                   json.dumps(dict(message.headers))
               ))
               
               # Store attachments
               for attachment in message.attachments:
                   file_path = self.save_attachment(message.uid, attachment)
                   conn.execute("""
                       INSERT INTO attachments (
                           email_uid, filename, content_type, size, file_path
                       ) VALUES (?, ?, ?, ?, ?)
                   """, (
                       message.uid,
                       attachment.filename,
                       attachment.content_type,
                       attachment.size,
                       file_path
                   ))
       
       def save_attachment(self, uid, attachment):
           """Save attachment to filesystem."""
           import os
           from pathlib import Path
           
           # Create attachments directory
           attachments_dir = Path("attachments") / str(uid)
           attachments_dir.mkdir(parents=True, exist_ok=True)
           
           # Save attachment
           file_path = attachments_dir / attachment.filename
           return str(attachment.save_to_file(attachments_dir))
       
       def get_emails_by_category(self, category, limit=100):
           """Get emails by category."""
           with self.get_db_connection() as conn:
               cursor = conn.execute("""
                   SELECT * FROM emails 
                   WHERE category = ? 
                   ORDER BY date_received DESC 
                   LIMIT ?
               """, (category, limit))
               return [dict(row) for row in cursor.fetchall()]
       
       def get_processing_stats(self):
           """Get email processing statistics."""
           with self.get_db_connection() as conn:
               stats = {}
               
               # Total emails
               cursor = conn.execute("SELECT COUNT(*) as total FROM emails")
               stats['total_emails'] = cursor.fetchone()['total']
               
               # By category
               cursor = conn.execute("""
                   SELECT category, COUNT(*) as count 
                   FROM emails 
                   WHERE category IS NOT NULL 
                   GROUP BY category
               """)
               stats['by_category'] = {row['category']: row['count'] for row in cursor.fetchall()}
               
               # By day
               cursor = conn.execute("""
                   SELECT DATE(date_received) as date, COUNT(*) as count 
                   FROM emails 
                   WHERE date_received >= date('now', '-30 days')
                   GROUP BY DATE(date_received)
                   ORDER BY date
               """)
               stats['by_day'] = [dict(row) for row in cursor.fetchall()]
               
               # Top senders
               cursor = conn.execute("""
                   SELECT sender, COUNT(*) as count 
                   FROM emails 
                   GROUP BY sender 
                   ORDER BY count DESC 
                   LIMIT 10
               """)
               stats['top_senders'] = [dict(row) for row in cursor.fetchall()]
               
               return stats

Complete Example: Production Email System
-----------------------------------------

Putting It All Together
~~~~~~~~~~~~~~~~~~~~~~~

A complete production-ready email processing system:

.. code-block:: python

   import logging
   import threading
   import time
   from datetime import datetime
   import signal
   import sys
   
   class ProductionEmailSystem:
       def __init__(self, config):
           self.config = config
           self.is_running = False
           
           # Initialize components
           self.ai_classifier = AIEmailClassifier(config)
           self.analytics = EmailProcessingAnalytics()
           self.db_integration = EmailDatabaseIntegration("emails.db")
           self.webhook_bridge = EmailWebhookBridge(config, config.get('webhooks', {}))
           self.security_processor = SecureEmailProcessor(config)
           self.realtime_monitor = CompleteRealTimeEmailSystem(config)
           
           # Set up logging
           self.setup_logging()
           
           # Set up signal handlers
           signal.signal(signal.SIGINT, self.shutdown_handler)
           signal.signal(signal.SIGTERM, self.shutdown_handler)
       
       def setup_logging(self):
           """Set up comprehensive logging."""
           logging.basicConfig(
               level=logging.INFO,
               format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
               handlers=[
                   logging.FileHandler('email_processor.log'),
                   logging.StreamHandler(sys.stdout)
               ]
           )
       
       def start(self):
           """Start the complete email processing system."""
           logger.info("Starting Production Email System")
           
           self.is_running = True
           
           # Start real-time monitoring
           self.realtime_monitor.add_notification_handler(self.handle_realtime_event)
           self.realtime_monitor.start_system()
           
           # Start webhook forwarding
           self.webhook_bridge.setup_email_to_webhook_forwarding()
           
           # Start batch processing
           self.batch_processor_thread = threading.Thread(
               target=self.run_batch_processing,
               daemon=True
           )
           self.batch_processor_thread.start()
           
           # Start analytics reporting
           self.analytics_thread = threading.Thread(
               target=self.run_analytics_reporting,
               daemon=True
           )
           self.analytics_thread.start()
           
           logger.info("Production Email System started successfully")
           
           # Keep main thread alive
           try:
               while self.is_running:
                   time.sleep(1)
           except KeyboardInterrupt:
               self.shutdown()
       
       def handle_realtime_event(self, event):
           """Handle real-time email events."""
           if event['type'] == 'new_message':
               start_time = time.time()
               
               try:
                   # Process with AI classification
                   self.process_realtime_email(event)
                   
                   processing_time = time.time() - start_time
                   
                   # Record analytics
                   # Note: We'd need the actual message object for full analytics
                   logger.info(f"Real-time processing completed in {processing_time:.2f}s")
                   
               except Exception as e:
                   logger.error(f"Real-time processing failed: {e}")
                   self.analytics.record_error('realtime_processing', None, str(e))
       
       def process_realtime_email(self, event):
           """Process real-time email event."""
           # In a production system, this would:
           # 1. Fetch the full email
           # 2. Classify with AI
           # 3. Store in database
           # 4. Route appropriately
           # 5. Send notifications
           
           logger.info(f"Processing real-time email: {event['subject']}")
       
       def run_batch_processing(self):
           """Run batch processing for comprehensive email handling."""
           while self.is_running:
               try:
                   # Process with intelligent classification
                   processor = IntelligentEmailProcessor(self.config)
                   processor.process_emails_intelligently()
                   
                   # Clean up old emails
                   bulk_processor = AdvancedBulkProcessor(self.config)
                   bulk_processor.smart_archive_emails()
                   bulk_processor.intelligent_spam_cleanup()
                   
                   # Wait before next batch
                   time.sleep(300)  # 5 minutes
                   
               except Exception as e:
                   logger.error(f"Batch processing error: {e}")
                   time.sleep(60)  # Wait 1 minute on error
       
       def run_analytics_reporting(self):
           """Run periodic analytics reporting."""
           while self.is_running:
               try:
                   # Generate analytics report
                   performance = self.analytics.get_performance_summary()
                   trends = self.analytics.get_hourly_trends()
                   
                   logger.info(f"Analytics: {performance['total_processed']} emails processed, "
                              f"{performance['error_rate']:.2%} error rate")
                   
                   # Export analytics
                   if performance['total_processed'] > 0:
                       timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                       self.analytics.export_analytics(f"analytics_{timestamp}.json")
                   
                   # Wait 1 hour for next report
                   time.sleep(3600)
                   
               except Exception as e:
                   logger.error(f"Analytics reporting error: {e}")
                   time.sleep(300)  # Wait 5 minutes on error
       
       def shutdown_handler(self, signum, frame):
           """Handle shutdown signals."""
           logger.info(f"Received signal {signum}, shutting down...")
           self.shutdown()
       
       def shutdown(self):
           """Graceful shutdown."""
           logger.info("Shutting down Production Email System")
           
           self.is_running = False
           
           # Stop real-time monitoring
           try:
               self.realtime_monitor.stop_system()
           except Exception as e:
               logger.error(f"Error stopping real-time monitor: {e}")
           
           # Export final analytics
           try:
               final_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
               self.analytics.export_analytics(f"final_analytics_{final_timestamp}.json")
           except Exception as e:
               logger.error(f"Error exporting final analytics: {e}")
           
           logger.info("Production Email System shutdown complete")

    if __name__ == "__main__":
        # Configuration
        config = {
            'host': 'imap.example.com',
            'username': 'your_email@example.com',
            'password': 'your_password',
            'use_ssl': True,
            'port': 993,
            'webhooks': {
                'endpoints': [
                    {
                        'name': 'primary_webhook',
                        'url': 'https://your-api.com/webhooks/email',
                        'secret': 'your_webhook_secret',
                        'filter_sensitive': True
                    }
                ]
            }
        }
        
        # Start the production system
        system = ProductionEmailSystem(config)
        system.start()

This comprehensive guide covers advanced patterns for modern email processing with Python Sage IMAP, including real-time monitoring with socket-based solutions, AI integration, security measures, and production-ready system architecture. All patterns emphasize the use of UIDs for reliable operations and leverage the enhanced MessageSet capabilities for optimal performance. 