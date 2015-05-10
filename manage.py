#!/usr/bin/env python
import os
import errno
import socket

COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

from app import create_app, db
from app.models import User, Role, Post, Comment, Permission
from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)

def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role,
                Permission=Permission, Post=Post, Comment=Comment)

manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)

@manager.command
def test(coverage=False):
    """Run the unit tests."""
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        import sys
        os.environ['FLASK_COVERAGE'] = '1'
        os.execvp(sys.executable, [sys.executable] + sys.argv)
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print('coverage Summary:')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print('HTML version: file://%s/index.html' % covdir)
        COV.erase()

@manager.command
def profile(length=25, profile_dir=None):
    """Start the application under the code profiler."""
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(
        app.wsgi_app, restrictions=[length],
        profile_dir=profile_dir)
    app.run()

@manager.command
def deploy():
    """Run deployment tasks."""
    from flask.ext.migrate import upgrade
    from app.models import Role, User

    # migrate database to latest revision
    upgrade()

    # create user roles
    Role.insert_roles()

    # create self-follows for all users
    User.add_self_follows()

@app.teardown_request
def commit_on_request_success(exception):
    """ We need to commit at the end of every request if successful.
        Flask-SQLAlchemy deprecated this behavior so we add our own handler for
        it, which also lets us customize handling of exceptions.

        Because of how Gunicorn's master/worker model works it sometimes ends
        up with socket errors on the exception stack that flask will pass into
        this function, but they are not really errors.
        See https://github.com/mitsuhiko/flask/issues/984 for details.
    """
    def _is_gunicorn_ignored_err(exc):
        if type(exc) == socket.error and \
                exc.errno in (errno.EAGAIN, errno.ECONNABORTED):
            return True
    if not exception or _is_gunicorn_ignored_err(exception):
        db.session.commit()
    else:
        app.logger.error(
            "No SQL commit due to exception: {0}".format(exception))

if __name__ == '__main__':
    manager.run()
