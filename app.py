#importing the needed libraries
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3, re
from werkzeug.security import generate_password_hash, check_password_hash

#initializing flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here' #setting a secure key
login_manager = LoginManager(app)
login_manager.login_view = 'login'

#sets class for flask login
class User(UserMixin):
    def __init__(self, id, username, password, name=None, bio=None):
        self.id = id
        self.username = username
        self.password = password
        self.name = name
        self.bio = bio

#loads user for flask login
@login_manager.user_loader
def load_user(user_id):
    with get_db_connection() as conn:
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    return User(**user) if user else None

#connects the sql database to the app.py
def get_db_connection():
    conn = sqlite3.connect('blog.db')
    conn.row_factory = sqlite3.Row
    return conn


#function that populates the posts on the homepage
@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    posts_per_page = 5
    offset = (page - 1) * posts_per_page

    with get_db_connection() as conn:
        total_posts = conn.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
        total_pages = (total_posts + posts_per_page - 1) // posts_per_page
        posts = conn.execute('''
            SELECT posts.*, users.username, users.id as author_id
            FROM posts
            JOIN users ON posts.author_id = users.id
            ORDER BY posts.created DESC
            LIMIT ? OFFSET ?
        ''', (posts_per_page, offset)).fetchall()

    return render_template('index.html', posts=posts, page=page, total_pages=total_pages)

#allows the user to create accounts
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        #gets the users input
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        error = None
        #validates the username and passwords
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif password != confirm_password:
            error = 'Passwords do not match.'

        #enters the new user info into the table and associates it with the user's id 
        if not error:
            with get_db_connection() as conn:
                if conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone():
                    error = 'Username already exists.'
                else:
                    conn.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                                 (username, generate_password_hash(password)))
                    conn.commit()
                    flash('Registration successful! Please log in.')
                    return redirect(url_for('login'))

        flash(error)

    return render_template('register.html')

#log the user in
@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        #initializes a list of all of the information from the users table
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        #checks that the list and username and password given are match
        if user and check_password_hash(user['password'], password):
            user_obj = User(user['id'], user['username'], user['password'], user['name'], user['bio'])
            #logs in the user
            login_user(user_obj)
            flash('Logged in successfully!')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!')
    return render_template('login.html')

#logs the user out
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!')
    return redirect(url_for('index'))

#shows the post of a user when the title is clicked on
@app.route('/post/<int:post_id>')
def post(post_id):
    conn = get_db_connection()
    post = conn.execute('''SELECT posts.*, users.username
                           FROM posts
                           JOIN users ON posts.author_id = users.id
                           WHERE posts.id = ?''', (post_id,)).fetchone()
    conn.close()
    return render_template('post.html', post=post)

#allows users to create posts
@app.route('/create', methods=('GET', 'POST'))
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        #validates that the user put in the correct information
        if not title or not content:
            flash('Title and content are required!')
        else:
            #updates the post information to the posts table in blog.db
            conn = get_db_connection()
            conn.execute('INSERT INTO posts (title, content, author_id) VALUES (?, ?, ?)',
                         (title, content, current_user.id))
            conn.commit()
            conn.close()
            flash('Your post has been created!')
            return redirect(url_for('index'))
    return render_template('create_post.html')

#allows a user to delete their own posts
@app.route('/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()

    #checks that the post exists
    if post is None:
        conn.close()
        abort(404)
    #checks that the post is the users
    if post['author_id'] != current_user.id:
        conn.close()
        abort(403)

    #updates the post table and deletes the post
    conn.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()
    flash('Your post has been deleted.')
    #reroutes user
    return redirect(url_for('index'))

#allows users to save posts
@app.route('/save_post/<int:post_id>', methods=['POST'])
@login_required
def save_post(post_id):
    conn = get_db_connection()

    # checks if the post exists
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    if not post:
        conn.close()
        abort(404)

    # checks if the user has already saved this post
    already_saved = conn.execute('SELECT * FROM saved_posts WHERE user_id = ? AND post_id = ?',
                                 (current_user.id, post_id)).fetchone()
    if already_saved:
        flash('You have already saved this post.')
        conn.close()
        return redirect(url_for('post', post_id=post_id))

    # saves the post
    conn.execute('INSERT INTO saved_posts (user_id, post_id) VALUES (?, ?)', (current_user.id, post_id))
    conn.commit()
    conn.close()

    flash('Post saved successfully!')
    return redirect(url_for('post', post_id=post_id))

#creates a route for the user to see their own posts
@app.route('/saved_posts')
@login_required
def saved_posts():
    conn = get_db_connection()
    #checks to see what posts the user has saved before
    saved = conn.execute('''SELECT posts.*, users.username
                            FROM posts
                            JOIN saved_posts ON posts.id = saved_posts.post_id
                            JOIN users ON posts.author_id = users.id
                            WHERE saved_posts.user_id = ?
                            ORDER BY posts.created DESC''', (current_user.id,)).fetchall()
    conn.close()
    #populates the posts saved by the user
    return render_template('saved_posts.html', posts=saved)

@app.route('/profile')
@login_required
def profile():
    conn = get_db_connection()
    posts = conn.execute('''SELECT * FROM posts
                            WHERE author_id = ?
                            ORDER BY created DESC''', (current_user.id,)).fetchall()
    conn.close()
    return render_template('profile.html', user=current_user, posts=posts)

#allows users to update their own profile
@app.route('/update_profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        #user inputs information
        name = request.form['name']
        bio = request.form['bio']
        conn = get_db_connection()
        #updates the user table to include these new info
        conn.execute('UPDATE users SET name = ?, bio = ? WHERE id = ?',
                     (name, bio, current_user.id))
        conn.commit()
        conn.close()
        flash('Profile updated successfully!')
        return redirect(url_for('profile'))
    return render_template('update_profile.html', user=current_user)

#custom template to highlight a word when a user searches it
@app.template_filter('highlight')
def highlight_keyword(text, keyword):
    if not keyword:
        return text
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    return pattern.sub(f'<span class="highlight">{keyword}</span>', text)

#allows user to search a post by user or any key words
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        keyword = request.form['keyword']
        conn = get_db_connection()
        posts = conn.execute('''SELECT posts.*, users.username
                                FROM posts
                                JOIN users ON posts.author_id = users.id
                                WHERE posts.title LIKE ?
                                OR posts.content LIKE ?
                                OR users.username LIKE ?
                                ORDER BY posts.created DESC''',
                             ('%' + keyword + '%', '%' + keyword + '%', '%' + keyword + '%')).fetchall()
        conn.close()
        return render_template('search_results.html', posts=posts, keyword=keyword)
    return render_template('search.html')

#populates another user's profile when you click on it
@app.route('/user/<int:user_id>')
def user_profile(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    posts = conn.execute('''SELECT * FROM posts
                            WHERE author_id = ?
                            ORDER BY created DESC''', (user_id,)).fetchall()
    conn.close()
    if user is None:
        abort(404)
    return render_template('user_profile.html', user=user, posts=posts)

#customn template filter to check if a post is saved by a user
@app.template_filter('saved_by_user')
def saved_by_user(post_id, user_id):
    conn = get_db_connection()
    saved = conn.execute('SELECT * FROM saved_posts WHERE user_id = ? AND post_id = ?',
                         (user_id, post_id)).fetchone()
    conn.close()
    return saved is not None

if __name__ == '__main__':

    app.run(debug=True)

