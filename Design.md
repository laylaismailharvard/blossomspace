For Blossom Space, my CS50 final project, I decided that Flask would be optimal to allow for the user data to be saved in an easily accessible way
via SQL with comabtibility with HMTL, CSS, a backend in Python, and Jinja. This route was the easiest, considering that Flask allows for integration
of multiple programming languages, which I found vital to the creation of Blossom Space.

For user authentication, I decided that Flask-Login would be essential because it maintains the users session. Implementing @login_required was
needed because it allowed for me to differentiate what a logged-in vs. non-logged-in user should see. For instance, any user can see someone's post, their profile, and search. However, only a logged-in user would be able to create their own profile, make and delete their own posts, and save posts. Without using these methods, my website wouldn't work the same way. Through Flask, I also got access to things like Werkzeug's generate_password_hash and confirm_password, both of which that helped me validate user authetication.

As far as my database, I decided that 3 tables would be best: users, posts, and saved_posts. In users, this table stores the username and password,
name and bio, and the user's id. I set it up this way so that a user's name is associated with their username, and similarly for the other attributes as well. In the posts table, I have the content, author_id, title, and time created, so that users can make a post and all of the post information is tied in one table. In the saved_posts table, I have it linked to what posts a user has saved. This table is a little in the middle of both tables, connecting both a users personal info (their id) and posts.

For my functions, I choose to use SQL commands like LIKE, UPDATE, DELETE, and other commands, to keep the tables neat and updated. Another example of a design choice I made was in the index function. I made sure to only fetch the required amount of posts per page, limiting the load on the server because it doesn't have to fetch all of the posts on the website. Secondly, I also made sure to have validation checks on the login page and
create/delete post to make sure that users are authenticated.

I used 2 customn templates to help the presentation. For the highlight template, all the terms in the search bar are highlighted, which helps users to easily identify what they searched. The saved template keeps users from saving a post twice. I chose to use these templates to extend the functionality of the program I've written and to extend the aesthetic of the website!
