"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase

from models import db, User, Message

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()

class MessageModelTestCase(TestCase):
    def setUp(self):
        db.drop_all()
        db.create_all()

        u = User.signup("u", "u@email.com", "password", None)
        m1 = Message(text="test")
        u.messages.append(m1)

        db.session.add(u)
        db.session.commit()

        self.u_id = u.id
        self.m1_id = m1.id

    def tearDown(self):
        db.session.rollback()

    def test_message_model(self):
        """Tests that message was instantiated for a user"""

        u = User.query.get(self.u_id)

        m1 = Message.query.get(self.m1_id)

        self.assertEqual(len(u.messages), 1)
        self.assertEqual(m1.text, "test")
        self.assertEqual(m1.user_id, u.id)

    def test_message_likes(self):
        """Tests that message like functionality works"""

        u_liker = User.signup("u_liker", "u_liker@email.com", "password", None)

        m1 = Message.query.get(self.m1_id)

        u_liker.likes.append(m1)

        db.session.add(u_liker)
        db.session.commit()

        self.assertEqual(u_liker.likes, [m1])
        self.assertEqual(m1.users_liked, [u_liker])