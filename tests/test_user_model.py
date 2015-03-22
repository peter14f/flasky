import unittest
from app import create_app, db
from app.models import User
import time

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