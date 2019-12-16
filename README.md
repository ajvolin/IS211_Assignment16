# IS211_FinalProject - Blog
## Adam Volin

This app is a simple blog that allows users to register for an account and create blog posts. The application uses two Python files, db.py and app.py. db.py abstracts database connections and querying to simplify the code. app.py contains all of the application route logic and uses db.py for communicating with the database. The database used is sqlite for portability. The database is initialized and filled with dummy data when the index route is visited if the schema doesn't already exist and the tables are empty.

This project makes extensive use of Bootstrap 4 (getbootstrap.com) for the layout and FontAwesome for iconography (fontawesome.com).

Published posts are visible by all users, authenticated or not. Unpublished posts are only visible to the users that created them. Posts can be unpublished, edited, and deleted only by the users that created them.

Categories can be created by authenticated users and can be used by other authenticated users.

Registration is open to any user.

There are three data models:
- Users
    - Holds user/author information
    - Used to authenticate users and to attach posts to
    - Has 5 fields
        - id - Unique identifier, primary key autoincrement
        - first_name - User's first name, text not null
        - last_name - User's last name, text not null
        - email - User's email address, text not null
        - password - User's login password, text not null
- Categories
    - Used to hold information about post categories
    - Has 4 fields
        - id - Unique identifier, primary key autoincrement
        - category_name - Name of the category for URL, text not null
        - category_display_name - Display name of the category, text not null
        - category_description - Description of the category, text null
- Posts
    - Used to store blog posts
    - Has 10 fields
        - id - Unique identifier, primary key autoincrement
        - author_id - ID of the user who the post belongs to, integer not null references users(id)
        - category_id - ID of the category the post belongs to, integer not null references categories(id)
        - title - The title of the post, text not null
        - slug - The permalink slug for the URL, text not null
        - short_content - A short preview of the post, text not null
        - content - The HTML content of the post, text not null
        - is_published - Indicates whether post is published or not, 0 or 1, integer
        - published_at - Date/time to publish the post at, timestamp not null
        - updated_at - Date/time to the post was last updated at, timestamp not null

### Run
python3 app.py

### Users
Emails = jsmith@example.com, jdoe@example.com, aapple@example.com
Password = password
