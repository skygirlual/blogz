from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:password@localhost:3306/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'T7lX@a$OxTVaC4pkqu'

class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(510))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(20))
    blogs = db.relationship('Blog', backref='owner')
    
    def __init__(self, email, password):
        self.email = email
        self.password = password

@app.before_request
def require_login():
    allowed_routes = ['register', 'login']
    if request.endpoint not in allowed_routes and 'email' not in session:
        return redirect('/login')

@app.route('/register', methods=['POST', 'GET'])
@app.route('/signup', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        verify = request.form['verify']

        # validation                                             *
        email_error = ""
        password_error = ""
        verify_error = ""
        error_count=0

        #email paramaters 
        if email == "":
            email_error = "email address not entered "
            error_count=error_count+1

        if "@" not in email and len(email) !=0:
            email_error = "email must contain 1 @ symbol "
            error_count=error_count+1

        if "." not in email and len(email) !=0:
            email_error = "email must contain exactly 1 . symbol "
            error_count=error_count+1

        if " " in email and len(email) !=0:
            email_error = "email must not contain any spaces "
            error_count=error_count+1

        if ((len(email) < 3 or len(email) > 20) and len(email) !=0):
            email_error = "email must contain 3 to 20 characters "
            error_count=error_count+1

        if len(password) < 3 or len(password) > 20 or " " in password:
            password_error = "Password must contain 3 to 20 characters and no spaces "
            error_count=error_count+1

        if password != verify:
            verify_error = "Passwords do not match"
            error_count=error_count+1
        
        login_errors=(email_error, password_error, verify_error)
        if error_count>0:
            for error in login_errors:
                if error != "":
                    flash(error, 'error')
            return render_template('register.html', email= email,  password= password, verify = verify)
    
        # creating new user account.
        existing_user = User.query.filter_by(email=email).first()
        if not existing_user:
            new_user =User(email, password)
            db.session.add(new_user)
            db.session.commit()
            session['email'] = email
            return redirect('/newpost')
        else:
            flash('Duplicate User. - you must use a unique email.', 'error')
            return render_template('register.html')
    else:
        return render_template('register.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method =='POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user==None:
            flash('Login Errror - Invalid or Unregistered email address', 'error')
            return render_template('/login.html', email=email)
        if user.password != password:
            flash('Login Errror - Password Incorrect', 'error')
            return render_template('/login.html', email=email)
        if user and user.password == password:
            session['email'] = email
            flash('Logged In', 'normal')
            return redirect('/newpost')
    return render_template('login.html')

@app.route('/logout')
def logout():
    del session['email']
    flash('You have been logged out', 'normal')
    return redirect('/login')

@app.route('/')
@app.route('/index/')
def index():
    return redirect ('/blog')

@app.route('/home/')
def home():
    #sort by email, convert to username in html.
    authors = User.query.order_by(User.email).all()
    return render_template('home.html', authors=authors)

@app.route('/blog/', methods=['POST', 'GET'])
def show_all_blog_posts():
    allPosts = db.session.query(Blog).order_by(Blog.id.desc()).all()
    return render_template('blogposts.html',title="My Fantastic Blog", posts=allPosts)

@app.route('/post/<int:post_id>/')
def show_post(post_id):
    onePost = Blog.query.filter_by(id=post_id).first()
    #validate post id is valid using query results
    # this fixes nav buttons out of range 
    if onePost == None:
        return redirect ('/blog')
    return render_template('post.html', posts=onePost, post_id=post_id)

@app.route('/singleUser/<int:user_id>/')
def show_users_posts(user_id):
    # validates user_id is in valid range
    if User.query.filter_by(id=user_id).first() == None:
        return redirect ('/blog')
    user_name = User.query.filter(User.id==user_id).first().email.split(sep='@')[0]
    user_Posts = Blog.query.order_by(Blog.id.desc()).filter(Blog.owner_id==user_id).all()
    return render_template('singleUser.html', posts=user_Posts, user_name=user_name)

@app.route('/singleUser/')
def show_my_posts():
    user_id = User.query.filter_by(email=session['email']).first()
    return redirect('/singleUser/%s' % user_id.id)

@app.route('/newpost/', methods=['POST', 'GET'])
def new_user_post():
    if request.method == 'POST':
        post_title = request.form['title']
        post_body = request.form['body']
        post_owner = User.query.filter_by(email=session['email']).first()

        # input validation
        if len(post_title) < 1 or len(post_title) > 120:
            flash('You forgot to enter a title.', 'error')
            return render_template('newpost.html', post_body=post_body)
        if len(post_body) < 1 or len(post_body) > 520:
            flash('You forgot to enter the body.', 'error')
            return render_template('newpost.html', post_title=post_title)

        new_post = Blog(post_title, post_body, post_owner)
        db.session.add(new_post)
        db.session.commit()
        new_post_id = new_post.id
        flash('Your new post has been posted.', 'normal')
        return redirect('/post/%s' % new_post_id)
    else:
        return render_template('newpost.html')

if __name__ == '__main__':
    app.run()
