"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from flask_bcrypt import Bcrypt
from models import db, User, Message, Follow, DEFAULT_IMAGE_URL, DEFAULT_HEADER_IMAGE_URL

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app
bcrypt = Bcrypt()


# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()


class UserModelTestCase(TestCase):
    def setUp(self):
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)

        u2.following.append(u1)

        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        self.u1_id = u1.id
        self.u2_id = u2.id

    def tearDown(self):
        db.session.rollback()

    def test_user_model(self):
        """Tests that new user was instantiated"""
        u1 = User.query.get(self.u1_id)

        # User should have no messages & 1 followers
        self.assertEqual(len(u1.messages), 0)
        self.assertEqual(len(u1.followers), 1)

    def test_is_following(self):
        """Tests is_followed method"""

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        self.assertTrue(u2.is_following(u1))
        self.assertFalse(u1.is_following(u2))


    def test_is_followed_by(self):
        """Tests is_followed_by method"""

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        self.assertTrue(u1.is_followed_by(u2))
        self.assertFalse(u2.is_followed_by(u1))

    def test_follow_relationship(self):
        """Tests the relationship between User and Follow"""

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        self.assertEqual(u1.followers, [u2])
        self.assertEqual(u1.following, [])
        self.assertEqual(u2.followers, [])
        self.assertEqual(u2.following, [u1])

    def test_signup_success(self):
        """Tests signup success"""

        u3 = User.signup("u3", "u3@email.com", "password", None)

        self.assertEqual(u3.username, 'u3')
        self.assertEqual(u3.email, 'u3@email.com')
        self.assertNotEqual(u3.password, 'password')
        self.assertEqual(u3.password[0], '$')
        self.assertTrue(bcrypt.check_password_hash(u3.password, "password"))
        self.assertEqual(u3.image_url, DEFAULT_IMAGE_URL)

        db.session.add(u3)
        db.session.commit()

        self.assertEqual(u3.header_image_url, DEFAULT_HEADER_IMAGE_URL)
        self.assertEqual(u3.bio, '')
        self.assertEqual(u3.location, '')



    # def test_signup_failure(self):
    #     """Tests signup failure"""

    #     u3 = User.signup("u1", "u3@email.com", "password", None)






    def test_authenticate_success(self):
        "Tests User.authenticate() success"

        u1 = User.query.get(self.u1_id)
        u1_prime = User.authenticate('u1', 'password')
        self.assertEqual(u1, u1_prime)

    def test_authenticate_failure(self):
        "Tests User.authenticate() failure"

        self.assertFalse(User.authenticate('wrong_username', 'password'))
        self.assertFalse(User.authenticate('u1', 'wrong_password'))

    def test_liked_relationship(self):
        """Tests relationship between user and likes"""

        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        message = Message(text='test_content')
        u1.messages.append(message)
        u2.likes.append(message)

        self.assertEqual(u2.likes, [message])
        self.assertEqual(message.users_liked, [u2])







