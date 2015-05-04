import unittest
from app import create_app, db
from app.models import Role, User, Post, Comment
from base64 import b64encode
from flask import url_for
import json

class APITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client()

    def tearDown(self):
        """ Flask will automatically remove database sessions at 
        the end of the request or when the application shuts down
        """
        db.session.remove() # close the session
        db.drop_all()
        self.app_context.pop()

    """ a helper method that returns the common headers that need to be
    sent with all requests. These include the authentication credentials
    and the MIME-type related headers.
    """
    def get_api_headers(self, email, password):
        return {
            'Authorization': 'Basic ' + b64encode(
                (email + ":" + password).encode('utf-8')).decode('utf-8'),
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    """
    This test no longer works with Flask-HTTPAuth 2.5.0
    Since when no authentication information is provided
    the verification callback is still called with
    empty email

    def test_no_auth(self):
        response = self.client.get(url_for('api.get_posts'),
                                   content_type='application/json')
        self.assertTrue(response.status_code == 401)
    """

    def test_404(self):
        response = self.client.get(
            '/wrong/url',
            headers=self.get_api_headers('email', 'password'))
        self.assertTrue(response.status_code == 404)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['error'] == 'not found')

    def test_bad_auth(self):
        # add a user
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(
            email='john@example.com',
            password='cat',
            confirmed=True,
            role=r)
        db.session.add(u)
        db.session.commit()

        # issue a request with bad token
        response = self.client.get(
            url_for('api.get_posts'),
            headers=self.get_api_headers('bad-token', ''))
        self.assertTrue(response.status_code == 401)

    def test_posts(self):
        # add a user
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(
            email='john@example.com', 
            password='cat',
            confirmed=True,
            role=r
        )
        db.session.add(u)
        db.session.commit()

        Post.generate_fake(testing=True)

        # get paginations of all posts
        response = self.client.get(
                url_for('api.get_posts'))
        self.assertTrue(response.status_code==200)
        json_response = json.loads(response.data.decode('utf-8'))
        next_url = json_response['next']
        self.assertTrue(next_url == url_for('api.get_posts', page=2, _external=True))
        
        # get next page
        response = self.client.get(
            url_for('api.get_posts', page=2))
        self.assertTrue(response.status_code==200)
        json_response = json.loads(response.data.decode('utf-8'))

        # write a post
        response = self.client.post(
            url_for('api.new_post'),
            headers=self.get_api_headers(
                email='john@example.com',
                password='cat'),
            data=json.dumps({'body': 'body of the *blog* post'}))
        self.assertTrue(response.status_code==201)
        url = response.headers.get('Location')
        self.assertIsNotNone(url)

        # get the new post
        response = self.client.get(
            url,
            headers=self.get_api_headers(
                'john@example.com', 'cat'))
        self.assertTrue(response.status_code==200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['url'] == url)
        self.assertTrue(json_response['body'] == 'body of the *blog* post')
        self.assertTrue(json_response['body_html'] ==
            '<p>body of the <em>blog</em> post</p>')

        # edit the new post
        chunks = url.split('/')
        post_id = chunks[-1]
        response = self.client.put(
                url_for('api.edit_post', id=post_id),
                headers=self.get_api_headers(
                    'john@example.com',
                    'cat'),
                data=json.dumps({'body': 'The post was *edited*'}))
        self.assertTrue(response.status_code==200)
        response = self.client.get(
            url,
            headers=self.get_api_headers(
                'john@example.com', 'cat'))
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['body'] == 'The post was *edited*')
        self.assertTrue(json_response['body_html'] == 
                            '<p>The post was <em>edited</em></p>')

        # test editing a post by a user who's not the author
        u2 = User(
            email='joe@example.com', 
            password='dog',
            confirmed=True,
            role=r)
        db.session.add(u2)
        db.session.commit()
        response = self.client.put(
            url_for('api.edit_post', id=post_id),
            headers=self.get_api_headers(
                'joe@example.com',
                'dog'),
            data=json.dumps({
                'body':'The post was edited by an *anonymous user*'}))
        self.assertTrue(response.status_code==403)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['error'] == 'forbidden')
        self.assertTrue(json_response['message'] == 'Insufficient permissions')

    def test_users(self):
        u = User(
            username='john',
            email="john@example.com",
            password="cat",
            confirmed=True)

        u2 = User(
            username='peter',
            email="peter@example.com",
            password="dog",
            confirmed=True)

        db.session.add(u)
        db.session.add(u2)
        db.session.commit()

        u.follow(u2)
        Post.generate_fake(testing=True)

        u = User.query.filter_by(email="john@example.com").first()
        response = self.client.get(url_for('api.get_user', id=u.id))
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(response.status_code == 200)
        self.assertTrue(json_response['user']['username'] == 'john')
        
        # get john's posts
        response = self.client.get(url_for('api.get_user_posts', id=u.id))
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))

        # go to page 2
        response = self.client.get(
            url_for('api.get_user_posts', id=u.id, page=2))
        self.assertTrue(response.status_code == 200)

        # get john's follower's posts
        response = self.client.get(url_for('api.get_user_followed_posts', id=u.id))
        self.assertTrue(response.status_code == 200)
        json_response = json.loads(response.data.decode('utf-8'))

        # go to page 2
        response = self.client.get(
            url_for('api.get_user_followed_posts', id=u.id, page=2))
        self.assertTrue(response.status_code == 200)

    def test_comments(self):
        u = User(
            email='john@example.com',
            password='cat',
            username='john')
        db.session.add(u)
        db.session.commit()

        # user is not confirmed

        # generate posts first, then comments
        Post.generate_fake(testing=True)
        Comment.generate_fake(testing=True)
        
        all_posts = Post.query.all()

        response = self.client.get(
            url_for('api.get_comments'),
            headers=self.get_api_headers(
                'john@example.com', 'cat'))
        self.assertTrue(response.status_code==403)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['error']=='forbidden')
        self.assertTrue(json_response['message']=='Unconfirmed account')

        u.confirmed = True
        db.session.add(u)
        db.session.commit()

        # user is now confirmed
        response = self.client.get(
            url_for('api.get_comments'),
            headers=self.get_api_headers(
                'john@example.com', 'cat'))
        self.assertTrue(response.status_code==200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['next']==
            url_for('api.get_comments', page=2, _external=True))

        # go to page two
        response = self.client.get(
            url_for('api.get_comments', page=2),
            headers=self.get_api_headers(
                'john@example.com', 'cat'))
        self.assertTrue(response.status_code==200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['prev']==
            url_for('api.get_comments', page=1, _external=True))
        
        # get comments of post 1 (page=1)
        response = self.client.get(
            url_for('api.get_post_comments', id=1),
            headers=self.get_api_headers(
                'john@example.com', 
                'cat'))
        self.assertTrue(response.status_code==200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['next'] == 
            url_for(
                'api.get_post_comments', 
                id=1, 
                page=2, 
                _external=True))

        # get comments of post 1 (page=2)
        response = self.client.get(
            url_for('api.get_post_comments', id=1, page=2),
            headers=self.get_api_headers(
                'john@example.com',
                'cat'))
        self.assertTrue(response.status_code==200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['prev'] == 
            url_for(
                'api.get_post_comments',
                id=1,
                page=1,
                _external=True))

    def test_authentication_token(self):
        u = User(
            email='john@example.com',
            password='cat',
            username='john',
            confirmed=True)

        db.session.add(u)
        db.session.commit()

        # without proper authentication headers
        response = self.client.get(
            url_for('api.get_token'))
        self.assertTrue(response.status_code==401)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['message']=='Invalid credentials')

        # with proper authentication headers
        response = self.client.get(
            url_for('api.get_token'),
            headers=self.get_api_headers(
                'john@example.com', 'cat'))

        self.assertTrue(response.status_code==200)
        json_response = json.loads(response.data.decode('utf-8'))
        token = json_response['token']

        # get posts using the token
        response = self.client.get(
            url_for('api.get_posts'),
            headers=self.get_api_headers(token, ""))
        self.assertTrue(response.status_code==200)

        