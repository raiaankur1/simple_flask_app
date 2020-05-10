from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import login_user, current_user, logout_user, login_required
from flask_blog import db, bcrypt
from flask_blog.models import User, Post
from flask_blog.users.forms import RegistrationForm, LoginForm, UpdateAccountForm, RequestResetForm, ResetPasswordForm
from flask_blog.users.utils import save_picture, send_request_email

users = Blueprint('users', __name__)


@users.route("/register", methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('main.hello'))
	form = RegistrationForm()
	if form.validate_on_submit():
		hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		user = User(username=form.username.data, email=form.email.data, password=hashed_pw)
		db.session.add(user)
		db.session.commit()
		flash(f'Account created for { form.username.data}! You can now Login', 'success')
		return redirect(url_for('main.login'))
	return render_template('register.html',title="Sign Up",form=form)

@users.route("/login", methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('main.hello'))
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user and bcrypt.check_password_hash(user.password, form.password.data):
			login_user(user, remember=form.remember.data)
			next_page = request.args.get('next')

			return redirect(next_page) if next_page else redirect(url_for('main.hello'))
		else:
			flash(f'Incorrect Email or Password entered', 'danger')	
	return render_template('login.html',title="Login",form=form)

@users.route("/logout")
def logout():
	logout_user()
	return redirect(url_for('main.hello'))


@users.route("/account", methods=['GET', 'POST'])
@login_required
def account():
	form = UpdateAccountForm()
	if form.validate_on_submit():
		if form.picture.data:
			if current_user.image_file != 'default.jpg' :
				os.remove(users.root_path + '/static/profile/' + current_user.image_file )
			picture_file = save_picture(form.picture.data)
			current_user.image_file = picture_file
		current_user.username = form.username.data
		current_user.email = form.email.data
		db.session.commit()
		flash(f'Your account credentials have been updated!', 'success')
		return redirect(url_for('users.account'))
	elif request.method == 'GET':
		form.username.data = current_user.username
		form.email.data = current_user.email
	image_file = url_for('static', filename='profile/'+ current_user.image_file)
	return render_template('account.html', title="Account",image_file=image_file, form=form)





@users.route("/user/<string:username>")
def user_posts(username):
	page = request.args.get('page', 1, type=int)
	user = User.query.filter_by(username=username).first_or_404()
	posts_list = Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
	return render_template('user_posts.html',posts=posts_list, user=user)



@users.route("/reset_password",methods=['GET', 'POST'])
def reset_request():
	if current_user.is_authenticated:
		return redirect(url_for('main.hello'))
	form = RequestResetForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		send_request_email(user)
		flash('An email has been sent to you with instructions to reset your account password.', 'info')

	return render_template('reset_request.html', title='Reset Password', form = form)


@users.route("/reset_password/<token>",methods=['GET', 'POST'])
def reset_token(token):
	if current_user.is_authenticated:
		return redirect(url_for('main.hello'))
	user = User.verify_reset_token(token)
	if user is None:
		flash('That is an invalid or expired token!', 'warning')
		return redirect(url_for('users.reset_request'))
	form = ResetPasswordForm()
	if form.validate_on_submit():
		hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		user.password = hashed_pw
		db.session.commit()
		flash(f'Your password has been updated! You can now Login', 'success')
		return redirect(url_for('users.login'))
	return render_template('reset_token.html', title='Reset Password', form=form)
		