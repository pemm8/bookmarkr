# javascript:location.href='http://127.0.0.1:5000/add/?password=shh&url='+location.href';&title='+document.title';
# javascript:location.href='http://127.0.0.1:5000/add/?password=shh&'+'url='+encodeURIComponent(location.href)+'&title='+encodeURIComponent(document.title)
# javascript:location.href='http://127.0.0.1:5000/add/?key=Q4toiDrXTojcLkRLxV6FRm&'+'url='+encodeURIComponent(location.href)+'&title='+encodeURIComponent(document.title)


import hashlib
import os
import subprocess
import functools
import shortuuid

from flask import Flask, abort, redirect, render_template, request, url_for, session, escape, g, jsonify

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import exists

import flask_admin as admin
from flask_admin.contrib import sqla
from flask_admin.contrib.sqla import filters, ModelView

from flask_security import Security, SQLAlchemyUserDatastore, \
	UserMixin, RoleMixin, login_required, current_user, utils

from flask_mail import Mail, Message

from celery import Celery

import pytz
from datetime import datetime
datetime.utcnow().replace(tzinfo=pytz.utc)

# app configuration
APP_ROOT = os.path.dirname(os.path.realpath(__file__))
MEDIA_ROOT = os.path.join(APP_ROOT, 'static', 'img')
MEDIA_ROOT_TEST = os.path.join(APP_ROOT, 'static', 'img', 'test')
MEDIA_URL = '/static/img/'
PASSWORD = 'shh'
PHANTOM = '/usr/local/bin/phantomjs'
SCRIPT = os.path.join(APP_ROOT, 'screenshot.js')
SECRET_KEY = '987654321'

# security config
SECURITY_TRACKABLE = True
SECURITY_REGISTERABLE = True
SECURITY_CONFIRMABLE = True
SECURITY_PASSWORD_SALT = '5P499QDJVAW7S2MXFR4L3OYYLH7LY4DK'

# celery config
CELERY_BROKER_URL = 'amqp://localhost'
CELERY_RESULT_BACKEND = ''

# mail server settings
MAIL_SERVER = 'smtp.aol.com'
MAIL_PORT = 587
MAIL_USE_TLS = False
MAIL_USE_SSL = False
MAIL_USERNAME = 'paul.mclear@aol.co.uk'
MAIL_PASSWORD = 'gy9-A64-SKZ-BSt'
ADMINS = ['paul.mclear@aol.co.uk']

# db config
SQLALCHEMY_DATABASE_URI = 'sqlite:///%s' % os.path.join(APP_ROOT, 'bookmarks.db')
# SQLALCHEMY_DATABASE_URI = 'postgresql://paulmclear:password@localhost/bookmarker'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# create our flask app and wrappers
app = Flask(__name__)
app.config.from_object(__name__)
db = SQLAlchemy(app)
mail = Mail(app)
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# helper function for jinja2 image
def image_exists(imgurl):
	if os.path.exists(APP_ROOT + imgurl):
		return True
	else:
		return False

app.jinja_env.globals.update(image_exists=image_exists)

# define models for bookmarks & tags
tags = db.Table('tags',
	db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
	db.Column('bookmark_id', db.Integer, db.ForeignKey('bookmark.id'))
)

class Bookmark(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	url = db.Column(db.String)
	created_dateb = db.Column(db.DateTime, default=datetime.utcnow)
	image = db.Column(db.String, default='')
	title = db.Column(db.String, default='')
	tags = db.relationship('Tag', secondary=tags, backref=db.backref('bookmarks', lazy='dynamic'))
	public = db.Column(db.Boolean, default=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

	class Meta:
		ordering = (('created_date', 'desc'),)


	def fetch_image(self):
		url_hash = hashlib.md5(self.url).hexdigest()
		filename = 'bookmark-%s.png' % url_hash
		outfile = os.path.join(MEDIA_ROOT, filename)

		fetchimage_async.delay(self.url, outfile)

		self.image = os.path.join(MEDIA_URL, filename)


class Tag(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100))
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

	def __str__(self):
		return self.name

# Define user and role models
roles_users = db.Table('roles_users',
		db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
		db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class Role(db.Model, RoleMixin):
	id = db.Column(db.Integer(), primary_key=True)
	name = db.Column(db.String(80), unique=True)
	description = db.Column(db.String(255))

	def __str__(self):
		return self.name

class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(255), unique=True)
	password = db.Column(db.String(255))
	active = db.Column(db.Boolean())
	confirmed_at = db.Column(db.DateTime())
	roles = db.relationship('Role', secondary=roles_users,
							backref=db.backref('users', lazy='dynamic'))
	# User Tracking
	last_login_at = db.Column(db.DateTime())
	current_login_at = db.Column(db.DateTime())
	last_login_ip = db.Column(db.String(30))
	current_login_ip = db.Column(db.String(30))
	login_count = db.Column(db.Integer)

	# user bookmark def
	bookmarks = db.relationship('Bookmark', backref='marker', lazy='dynamic')
	tags = db.relationship('Tag', backref='tagger', lazy='dynamic')
	userkey = db.Column(db.String)

	def get_bookmarks(self, tagname=''):
		if tagname:
			tag = self.tags.filter_by(name=tagname).first()
			return tag.bookmarks
		else:
			return self.bookmarks.filter_by(public=True).all()

	def get_tags(self):
		return self.tags

	def __str__(self):
		return self.email

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# Create admin
admin = admin.Admin(app, name='Admin', template_mode='bootstrap3')

# Customise admin views
class BookmarkView(sqla.ModelView):
	form_ajax_refs = {
			'tags': {
				'fields': (Tag.name,)
			}
		}

class TagView(sqla.ModelView):
	form_excluded_columns = ['bookmarks']

# Add admin views
admin.add_view(BookmarkView(Bookmark, db.session))
admin.add_view(TagView(Tag, db.session))
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Role, db.session))

@app.before_request
def before_request():
	g.user = current_user

@app.route('/')
@app.route('/index')
@login_required
def index():
	# bookmarks = Bookmark.query.filter_by(public=True).all()
	uk = userkey_getorset()
	bookmarks = g.user.get_bookmarks()
	tags = g.user.get_tags()
	taglist = {}
	for tag in tags:
		taglist[tag.name] = ''
	return render_template('grid.html', object_list=bookmarks, tags=taglist, filtered=False)

@celery.task
def fetchimage_async(url, outfile):
	with app.app_context():
		params = [PHANTOM, SCRIPT, url, outfile]
		exitcode = subprocess.call(params)

@app.route('/test')
def test():
	# msg = Message("Test Async Mail", sender='paul.mclear@aol.co.uk', recipients=['paul.mclear@gmail.com'])
	# msg.body = "Testing"
	# send_email_async.delay(msg)
	# return redirect(url_for('index'))
	fetchimage_async.delay('http://www.google.com')
	return redirect(url_for('index'))

@app.route('/filter/<tagname>')
def filter(tagname):
	# q = Tag.query.filter_by(name=tagname).first()
	# if q is not None:
	tags = g.user.get_tags()
	taglist = {}
	for tag in tags:
		taglist[tag.name] = ''
	bookmarks = g.user.get_bookmarks(tagname)
	return render_template('grid.html', object_list=bookmarks, tags=taglist, filtered=True)
	# else:
	# 	return redirect(url_for('index'))

def userkey_getorset():
	if g.user.userkey is None:
		newuserkey = shortuuid.ShortUUID().random(length=22)
		checkunique = User.query.filter_by(userkey=newuserkey).first()
		if not checkunique is None:
			newuserkey = shortuuid.ShortUUID().random(length=22)
		u = User.query.filter_by(id = g.user.id).first()
		if not u is None:
			u.userkey = newuserkey
			db.session.commit()
			return newuserkey
	else:
		return g.user.userkey

@app.route('/add/')
def add():
	# password = request.args.get('password')
	# if password != PASSWORD:
	# 	abort(404)

	url = request.args.get('url')
	title = request.args.get('title')
	userkey = request.args.get('key')

	u = User.query.filter_by(userkey=userkey).first()

	if not u:
		abort(404)

	if url:
		b = Bookmark.query.filter_by(marker=u, url=url).first()
		if b is None:
		## Replaced logic
		# stmt = exists().where(Bookmark.url==url, Bookmark.marker==u)
		# indb = db.session.query(stmt).scalar()
		# if (indb == False):
			bookmark = Bookmark(url=url, title=title, public=True, marker=u)
			bookmark.fetch_image()
			db.session.add(bookmark)
			db.session.commit()
			# bookmark.save()
			return redirect(url)
	abort(404)

@app.route('/refresh/<int:id>')
def refresh(id):
	# user, bookmark
	b = Bookmark.query.filter_by(id=id).first()
	if b.marker == g.user:
		b.fetch_image()
		db.session.commit()
		return redirect(url_for('index'))

@app.route('/rm/<int:id>')
def remove(id):
	b = Bookmark.query.filter_by(id=id).first()
	if b:
		b.public = False
		db.session.commit()
	return redirect(url_for('index'))

if __name__ == '__main__':
	# create the bookmark table if it does not exist
	db.create_all()

	# run the application
	app.run(debug=True)