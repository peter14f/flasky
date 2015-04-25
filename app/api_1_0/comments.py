from .authentication import auth
from . import api
from ..models import Comment, Post
from flask import current_app, request, jsonify

@api.route('/comments/')
@auth.login_required
def get_comments():
    """
    comments = Comment.query.all()
    return jsonify({'comments': [comment.to_json() for comment in comments]})
    """
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.paginate(page,
                                        per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
                                        error_out=False)
    comments = pagination.items
    next = None
    prev = None
    if pagination.has_next:
        next = pagination.next_num
    if pagination.has_prev:
        prev = pagination.prev_num
    return jsonify({'comments': [comment.to_json() for comment in comments],
                    'prev': prev,
                    'next': next,
                    'count': pagination.total})

@api.route('/comments/<int:id>')
@auth.login_required
def get_post_comments(id):
    """
    post = Post.query.get_or_404(post_id)
    post_comments = post.comments
    return jsonify({'post_comments': [comment.to_json() for comment in post_comments]}})
    """
    post = Post.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = post.comments.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'], error_out=False)
    post_comments = pagination.items
    prev = None
    next = None
    if pagination.has_prev:
        prev = url_for('', id=id, page=pagination.prev_num, _external=True)
    if pagination.has_next:
        next = pagination.next_num
    return jsonify({'post_comments': [comment.to_json() for comment in post_comments],
                    'prev': prev,
                    'next': next,
                    'count': pagination.total})
