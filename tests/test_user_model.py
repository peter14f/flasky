import unittest
from app import create_app, db
from app.models import User, Role, Permission, AnonymousUser, Follow, Post
import time
from datetime import datetime

class UserModelTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_setter(self):
        u = User(password='cat')
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self):
        u = User(password='cat')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verification(self):
        u = User(password='cat')
        self.assertTrue(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))

    def test_password_salts_are_random(self):
        u1 = User(password='cat')
        u2 = User(password='cat')
        self.assertTrue(u1.password_hash != u2.password_hash)

    def test_valid_confirmation_token(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token()
        self.assertTrue(u.confirm(token))

    def test_invalid_confirmation_token(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token()
        self.assertFalse(u.confirm(token+'.'))
        self.assertFalse(u.confirmed)

    # the right token is used, but confirm() is called too late
    def test_expired_confirmation_token(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token(1)
        time.sleep(2)
        self.assertFalse(u.confirm(token))

    def test_valid_reset_token(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_reset_token()
        self.assertTrue(u.reset_password(token, 'dog'))
        self.assertTrue(u.verify_password('dog'))

    def test_invalid_reset_token(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_reset_token()
        self.assertFalse(u.reset_password(token + '.', 'dog'))
        self.assertTrue(u.verify_password('cat'))

    def test_valid_email_change_token(self):
        u = User(password='cat', email='testing@gmail.com')
        db.session.add(u)
        db.session.commit()
        token = u.generate_email_change_token('flasky@gmail.com')
        self.assertTrue(u.change_email(token))
        self.assertTrue(u.email == 'flasky@gmail.com')

    def test_invalid_email_change_token(self):
        u = User(password='cat', email='testing@gmail.com')
        db.session.add(u)
        db.session.commit()
        token = u.generate_email_change_token('flasky@gmail.com')
        self.assertFalse(u.change_email(token+'.'))
        self.assertTrue(u.email == 'testing@gmail.com')

    """ user 2 tries to change her email to the same one that
        user 1 is using with the correct token
    """
    def test_duplicate_email_change_token(self):
        u1 = User(password='cat', email='testing1@gmail.com')
        u2 = User(password='cat', email='testing2@gmail.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u2.generate_email_change_token('testing1@gmail.com')
        self.assertFalse(u2.change_email(token))
        self.assertTrue(u2.email == 'testing2@gmail.com')

    def test_roles_and_permissions(self):
        Role.insert_roles()
        u = User(email='john@example.com', password='cat')
        self.assertTrue(u.can(Permission.WRITE_ARTICLES))
        self.assertFalse(u.can(Permission.MODERATE_COMMENTS))

    def test_anonymous_user(self):
        u = AnonymousUser()
        self.assertFalse(u.can(Permission.FOLLOW))

    def test_timestamps(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        delta1 = datetime.utcnow() - u.member_since
        delta2 = datetime.utcnow() - u.last_seen
        self.assertTrue(delta1.total_seconds() < 3)
        self.assertTrue(delta2.total_seconds() < 3)

    def test_ping(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        last_seen_before = u.last_seen
        u.ping()
        last_seen_after = u.last_seen
        self.assertTrue(last_seen_after > last_seen_before)

    def test_gravatar(self):
        u = User(password='cat', email="john@example.com")
        with self.app.test_request_context('/'):
            gravatar = u.gravatar()
            gravatar_256 = u.gravatar(size=256)
            gravatar_pg = u.gravatar(rating='pg')
            gravatar_retro = u.gravatar(default='retro')
        with self.app.test_request_context('/', base_url='https://example.com'):
            gravatar_ssl = u.gravatar()
        self.assertTrue('http://www.gravatar.com/avatar/' +
                        'd4c74594d841139328695756648b6bd6' in gravatar)
        self.assertTrue('s=256' in gravatar_256)
        self.assertTrue('r=pg' in gravatar_pg)
        self.assertTrue('d=retro' in gravatar_retro)
        self.assertTrue('https://secure.gravatar.com/avatar/' +
                        'd4c74594d841139328695756648b6bd6' in gravatar_ssl)

    def test_follows(self):
        u1 = User(email='john@example.com', password='cat')
        u2 = User(email='susan@example.org', password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertFalse(u1.is_followed_by(u2))
        timestamp_before = datetime.utcnow()
        u1.follow(u2)
        db.session.add(u1)
        db.session.commit()
        timestamp_after = datetime.utcnow()
        self.assertTrue(u1.is_following(u2))
        self.assertFalse(u1.is_followed_by(u2))
        self.assertTrue(u2.is_followed_by(u1))
        self.assertTrue(u1.followed.count() == 2)
        self.assertTrue(u2.followers.count() == 2)
        f = u1.followed.all()[-1]
        self.assertTrue(f.followed == u2)
        self.assertTrue(timestamp_before <= f.timestamp <= timestamp_after)
        f = u2.followers.all()[-1]
        self.assertTrue(f.follower == u1)
        u1.unfollow(u2)
        db.session.add(u1)
        db.session.commit()
        self.assertTrue(u1.followed.count() == 1)
        self.assertTrue(u2.followers.count() == 1)
        self.assertTrue(Follow.query.count() == 2)
        u2.follow(u1)
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        db.session.delete(u2)
        db.session.commit()
        self.assertTrue(Follow.query.count() == 1)

    def test_followed_posts(self):
        user_john = User(email='john@example.com', password='123')
        user_susan = User(email='susan@example.com', password='123')
        user_david = User(email='david@example.com', password='123')
        db.session.add(user_john)
        db.session.add(user_susan)
        db.session.add(user_david)
        db.session.commit()
        post_susan = Post(author_id=user_susan.id, body='Blog post by susan')
        post_john1 = Post(author_id=user_john.id, body='Blog post by john')
        post_john2 = Post(author_id=user_john.id, body='Blog post by david')
        post_david = Post(author_id=user_david.id, body='Second blog post by john')
        db.session.add(post_john1)
        db.session.add(post_john2)
        db.session.add(post_susan)
        db.session.add(post_david)
        db.session.commit()
        user_john.follow(user_david)
        user_susan.follow(user_john)
        user_susan.follow(user_david)
        susan_followed_posts_list = user_susan.followed_posts.all()
        self.assertTrue(len(susan_followed_posts_list) == 4)

