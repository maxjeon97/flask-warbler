"""Message View tests."""

# run these tests like:
#
#    FLASK_DEBUG=False python -m unittest test_message_views.py

import os
from unittest import TestCase

from models import db, Message, User, Follow, Like
from werkzeug.exceptions import Unauthorized

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app, CURR_USER_KEY

# app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# This is a bit of hack, but don't use Flask DebugToolbar

# app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageBaseViewTestCase(TestCase):
    def setUp(self):
        Follow.query.delete()
        Like.query.delete()
        Message.query.delete()
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        db.session.add_all([u1, u2])
        db.session.flush()

        m1 = Message(text="m1-text", user_id=u1.id)

        db.session.add(m1)
        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id
        self.m1_id = m1.id

    def tearDown(self):
        db.session.rollback()


class MessageAddViewTestCase(MessageBaseViewTestCase):
    def test_display_add_message(self):
        """Tests displaying of add message form"""
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get("/messages/new")

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn('Add my message!', html)

    def test_display_add_message_unauthorized(self):
        """Tests displaying of add message form"""
        with app.test_client() as c:
            resp = c.get("/messages/new", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn('Access unauthorized.', html)

    def test_add_message(self):
        """Tests adding of message"""
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post("/messages/new", data={"text": "Test message!"},
                            follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn('Test message!', html)

    def test_add_message_unauthorized(self):
        """Tests adding of message when nobody is logged in"""
        with app.test_client() as c:
            resp = c.post("/messages/new", data={"text": "Test message!"},
                          follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn('Access unauthorized.', html)

    def test_show_message(self):
        """Tests showing of message"""
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f"/messages/{self.m1_id}")

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn('m1-text', html)

    def test_show_message_unauthorized(self):
        """Tests showing of message when nobody is logged in"""
        with app.test_client() as c:
            resp = c.get(f"/messages/{self.m1_id}",
                         follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn('Access unauthorized.', html)


    def test_delete_message(self):
        """Tests deletion of message"""
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(f"/messages/{self.m1_id}/delete",
                          follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn('Message deleted!', html)
            self.assertNotIn('m1-text', html)

    def test_delete_message_unauthorized(self):
        """Tests showing of message when nobody is logged in"""
        with app.test_client() as c:
            resp = c.post(f"/messages/{self.m1_id}/delete",
                          follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn('Access unauthorized.', html)

    def test_delete_message_not_owned(self):
        """Tests that an Unauthorized error is raised when trying to delete
        someone else's message"""
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u2_id

            resp = c.post(f"/messages/{self.m1_id}/delete",
                          follow_redirects=True)

            self.assertEqual(resp.status_code, 401)

            html = resp.get_data(as_text=True)
            self.assertIn('ACCESS UNAUTHORIZED', html)
