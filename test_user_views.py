"""User view tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from models import db, User, Message, Like, Follow, DEFAULT_IMAGE_URL, DEFAULT_HEADER_IMAGE_URL


# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()

app.config['WTF_CSRF_ENABLED'] = False


class UserTemplateTestCase(TestCase):
    def setUp(self):
        Follow.query.delete()
        Like.query.delete()
        Message.query.delete()
        User.query.delete()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)
        u3 = User.signup("u3", "u3@email.com", "password", None)

        db.session.add(u1)
        db.session.add(u2)
        db.session.add(u3)
        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id
        self.u3_id = u3.id

    def tearDown(self):
        db.session.rollback()


class UserAuthTestCase(UserTemplateTestCase):
    def test_get_signup(self):
        """Tests signup form rendering"""
        with app.test_client() as c:
            resp = c.get('/signup')

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn('Join Warbler today', html)

    def test_post_signup_success(self):
        """Tests successful signup"""
        with app.test_client() as c:
            resp = c.post('/signup',
                          data={
                              'username': 'u4',
                              'password': 'password',
                              'email': 'u4@email.com',
                              'image_url': ''
                          },
                          follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn('u4', html)

    def test_signup_failure(self):
        """Tests signup failure due to duplicate username or email"""
        with app.test_client() as c:
            resp_user = c.post('/signup',
                               data={
                                   'username': 'u1',
                                   'password': 'password',
                                   'email': 'u3@email.com',
                                   'image_url': ''
                               },
                               follow_redirects=True)

            self.assertEqual(resp_user.status_code, 200)

            html = resp_user.get_data(as_text=True)
            self.assertIn('Username or email already taken', html)

            resp_email = c.post('/signup',
                                data={
                                    'username': 'u4',
                                    'password': 'password',
                                    'email': 'u1@email.com',
                                    'image_url': ''
                                },
                                follow_redirects=True)

            self.assertEqual(resp_email.status_code, 200)

            html = resp_email.get_data(as_text=True)
            self.assertIn('Username or email already taken', html)

    def test_get_login(self):
        """Tests login form rendering"""
        with app.test_client() as c:
            resp = c.get('/login')

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn('Welcome back.', html)
            self.assertIn('Log in', html)

    def test_post_login_success(self):
        """Tests successful login"""
        with app.test_client() as c:
            resp = c.post('/login',
                          data={
                              'username': 'u1',
                              'password': 'password'
                          },
                          follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn('Hello, u1!', html)

    def test_post_login_failure(self):
        """Tests unsuccesful login"""
        with app.test_client() as c:
            resp = c.post('/login',
                          data={
                              'username': 'u1',
                              'password': 'wrong_password'
                          },
                          follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn('Invalid credentials.', html)

    def test_post_logout_success(self):
        """Tests logout"""
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post('/logout', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn('Succesfully logged out', html)

    def test_post_logout_unauthorized(self):
        """Tests logout if someone is not already logged in"""
        with app.test_client() as c:
            resp = c.post('/logout', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn("Access unauthorized.", html)


class UserRoutesTestCase(UserTemplateTestCase):
    def setUp(self):
        super().setUp()
        u1 = User.query.get(self.u1_id)
        u2 = User.query.get(self.u2_id)

        u2.following.append(u1)

        db.session.commit()

    def test_list_users(self):
        """Tests displaying of users list"""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get('/users')

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn("u1", html)
            self.assertIn("u2", html)

    def test_list_users_unauthorized(self):
        """Tests displaying of users list with nobody logged in"""
        with app.test_client() as c:
            resp = c.get('/users', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn("Access unauthorized.", html)

    def test_list_users_search(self):
        """Tests displaying of users search result"""

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get('/users?q=u1')
            # how can we do this

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn("u1", html)
            self.assertNotIn("u2", html)

    def test_list_users_search_unauthorized(self):
        """Tests displaying of users search result with nobody logged in"""
        with app.test_client() as c:
            resp = c.get('/users', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn("Access unauthorized.", html)

    def test_show_user(self):
        """Tests show user"""
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id
            resp = c.get(f'/users/{self.u1_id}')

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn("@u1", html)

    def test_show_user_unauthorized(self):
        """Tests show user with nobody logged in"""
        with app.test_client() as c:
            resp = c.get(f'/users/{self.u1_id}', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn("Access unauthorized.", html)

    def test_show_following(self):
        """Tests show following"""
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u2_id

            resp = c.get(f'/users/{self.u2_id}/following')

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn("@u1", html)
            self.assertNotIn("@u3", html)

    def test_show_following_unauthorized(self):
        """Tests show following with nobody logged in"""
        with app.test_client() as c:
            resp = c.get(f'/users/{self.u1_id}/following', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn("Access unauthorized.", html)

    def test_show_followers(self):
        """Tests show followers"""
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f'/users/{self.u1_id}/followers')

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn("@u2", html)
            self.assertNotIn("@u3", html)

    def test_show_followers_unauthorized(self):
        """Tests show followers with nobody logged in"""
        with app.test_client() as c:
            resp = c.get(f'/users/{self.u1_id}/followers', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn("Access unauthorized.", html)

    def test_start_following(self):
        """Tests start following"""
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(f'/users/follow/{self.u3_id}', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn("@u3", html)
            self.assertNotIn("@u2", html)

    def test_start_following_failure(self):
        """Tests start following for self or someone already followed"""
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u2_id

            resp_self = c.post(f'/users/follow/{self.u2_id}',
                               follow_redirects=True)

            self.assertEqual(resp_self.status_code, 200)

            html = resp_self.get_data(as_text=True)
            self.assertIn("You cannot follow yourself!", html)


            resp_already = c.post(f'/users/follow/{self.u1_id}',
                                  follow_redirects=True)

            self.assertEqual(resp_already.status_code, 200)

            html = resp_already.get_data(as_text=True)
            self.assertIn("You are already following that person!", html)

    def test_start_following_unauthorized(self):
        """Tests start following with nobody logged in"""
        with app.test_client() as c:
            resp = c.post(f'/users/follow/{self.u1_id}', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn("Access unauthorized.", html)

    def test_stop_following_unauthorized(self):
        """Tests stop following with nobody logged in"""
        with app.test_client() as c:
            resp = c.post(f'/users/stop-following/{self.u1_id}', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn("Access unauthorized.", html)

    def test_view_edit_profile_form_unauthorized(self):
        """Tests edit profile with nobody logged in"""
        with app.test_client() as c:
            resp = c.get('/users/profile', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn("Access unauthorized.", html)

    def test_edit_profile_invalid(self):
        """Tests edit profile with invalid username or email"""
        with app.test_client() as c:
            resp = c.post('/users/profile', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn("Access unauthorized.", html)

    def test_delete_user_unauthorized(self):
        """Tests delete user with nobody logged in"""
        with app.test_client() as c:
            resp = c.post('/users/delete', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            html = resp.get_data(as_text=True)
            self.assertIn("Access unauthorized.", html)

