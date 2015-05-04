from . import api
from .authentication import auth
from ..models import User, Post
from flask import current_app, request, jsonify, url_for

@api.route('/users/<int:id>')
@auth.login_required
def get_user(id):
    user = User.query.get_or_404(id)
    return jsonify({
        'user': user.to_json()
    })

@api.route('/users/<int:id>/posts/')
@auth.login_required
def get_user_posts(id):
    """
    user = User.query.get_or_404(id)
    posts = Posts.query.filter_by(author=user).all()
    return jsonify({'user_posts': [post.to_json() for post in posts]})
    """
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter_by(author=user).paginate(
                    page,
                    per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
                    error_out=False)
    user_posts = pagination.items
    next = None
    prev = None
    if pagination.has_next:
        next = url_for('api.get_user_posts', id=id, page=pagination.next_num, _external=True)
    if pagination.has_prev:
        prev = url_for('api.get_user_posts', id=id, page=pagination.prev_num, _external=True)
    return jsonify({
        'user_posts': [post.to_json() for post in user_posts],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/users/<int:id>/timeline/')
@auth.login_required
def get_user_followed_posts(id):
    """
    user = User.query.get_or_404(id)
    posts = user.followed_posts.order_by(Post.timestamp.desc())
    return jsonify({'followed_posts': [post.jsonify() for post in posts]})
    """
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = user.followed_posts.order_by(Post.timestamp.desc()).paginate(
            page=page, 
            per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
            error_out=False)
    followed_posts = pagination.items
    next = None
    prev = None
    if pagination.has_next:
        next = url_for('api.get_user_followed_posts', id=id, page=pagination.next_num, _external=True)
    if pagination.has_prev:
        prev = url_for('api.get_user_followed_posts', id=id, page=pagination.prev_num, _external=True)
    return jsonify({
        'followed_posts': [post.to_json() for post in followed_posts],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })

