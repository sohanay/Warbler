"""Message View tests."""

import os
from unittest import TestCase

from models import db, connect_db, Message, User
from datetime import datetime


os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        self.client = app.test_client()

        all_messages = Message.query.all()
        for test_message in all_messages:
            db.session.delete(test_message)
        db.session.commit()
        all_users = User.query.all()
        for test_user in all_users:
            db.session.delete(test_user)
        db.session.commit()
        testuser1 = User.signup(username="testuser1",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None,
                                    header_image_url=None,
                                    bio=None)
        testuser2 = User.signup(username="testuser2", 
                                    email="test2@test.com",
                                    password="testuser2",
                                    image_url=None,
                                    header_image_url=None,
                                    bio=None)
        db.session.add(testuser1)
        db.session.add(testuser2)
        db.session.commit()
        
        message_1 = Message(text="Test Message 1",
        timestamp=datetime.utcnow(),
        user_id=testuser1.id)
        message_2 = Message(text="Test Message 2",
        timestamp=datetime.utcnow(),
        user_id=testuser2.id)
        message_3 = Message(text="Test Message 3",
        timestamp=datetime.utcnow(),
        user_id=testuser2.id)
        for msg in [message_1, message_2, message_3]:
            db.session.add(msg)
        db.session.commit()

    def tearDown(self):
        """Tear down"""
        db.session.rollback()

    def test_add_message(self):
        """Can user add a message?"""

        with self.client as c:
            testuser1 = User.query.filter_by(username="testuser1").first()
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = testuser1.id

            resp = c.post("/messages/new", data={"text": "Hello"})

            self.assertEqual(resp.status_code, 302)

            msg = Message.query.order_by(Message.timestamp.asc()).first()
            self.assertEqual(msg.text, "Hello")
    
    def test_show_own_message(self):
        """Can user view their own message"""

        with self.client as c:
            testuser1 = User.query.filter_by(username="testuser1").first()
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = testuser1.id

            message_1 = Message.query.filter_by(text="Test Message 1").first()

            resp = c.get(f"/messages/{message_1.id}")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Test Message 1",html)
            self.assertIn("testuser1",html)

    def test_show_others_message(self):
        """Can user view another user's message"""

        testuser1 = User.query.filter_by(username="testuser1").first()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = testuser1.id

            message_2 = Message.query.filter_by(text="Test Message 2").first()

            resp = c.get(f"/messages/{message_2.id}")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Test Message 2",html)
            self.assertIn("testuser2",html)
    
    def test_delete_own_message(self):
        """ Can user delete their message """
        with self.client as c:
                testuser1 = User.query.filter_by(username="testuser1").first()
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = testuser1.id

                message_1 = Message.query.filter_by(text="Test Message 1").first()

                resp = c.post(f"/messages/{message_1.id}/delete", follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertNotIn("Test Message 1",html)

    def test_delete_others_message(self):
        """ Can user delete someone else's message """
        with self.client as c:
                testuser1 = User.query.filter_by(username="testuser1").first()
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = testuser1.id

                message_2 = Message.query.filter_by(text="Test Message 2").first()

                resp = c.post(f"/messages/{message_2.id}/delete", follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn("Access unauthorized.",html)

                resp = c.get(f"/messages/{message_2.id}")
                html = resp.get_data(as_text=True)

                self.assertIn("Test Message 2",html)
    
    def test_anonymous_user_add_message(self):
        """ Can a message be added if no one is logged in """
        with self.client as c:
                testuser1 = User.query.filter_by(username="testuser1").first()
                message_1 = Message.query.filter_by(text="Test Message 1").first()

                resp = c.post(f"/messages/new", follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn("Access unauthorized.",html)

                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = testuser1.id

                resp = c.get(f"/messages/{message_1.id}")
                html = resp.get_data(as_text=True)
                self.assertIn("Test Message 1",html)

    def test_anonymous_user_delete_message(self):
        """ Can a message be deleted if no one is logged in """
        with self.client as c:
                testuser1 = User.query.filter_by(username="testuser1").first()
                message_1 = Message.query.filter_by(text="Test Message 1").first()

                resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn("Access unauthorized.",html)

                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = testuser1.id

                resp = c.get(f"/messages/{message_1.id}")
                html = resp.get_data(as_text=True)
                self.assertIn("Test Message 1",html)
    