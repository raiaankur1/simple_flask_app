from flask import Blueprint, render_template, request
from flask_blog.models import Post

main = Blueprint('main', __name__)

@main.route("/home")
@main.route("/")
def hello():
	page = request.args.get('page', 1, type=int)
	posts_list = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
	return render_template('home.html',posts=posts_list)

@main.route("/about")
def about():
	return render_template('about.html',title="About")