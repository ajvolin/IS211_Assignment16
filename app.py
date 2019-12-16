#!/usr/bin/python
# -*- coding: utf-8 -*-

"""app.py: IS 211 Final Project."""

__author__ = 'Adam Volin'
__email__ = 'Adam.Volin56@spsmail.cuny.edu'

from flask import Flask, render_template, request, session, redirect, abort, url_for
from db import init_db, query, insert, update, delete, close_connection
import datetime
import re

app = Flask(__name__)
# Set a secret key for Flask to use to encrypt the session,
# best practice is to store this in an environment file
# but for simplicity will be stored here
app.secret_key = "5c8fce510fa3c5f9bb251cd1b13fd6eb"


def check_auth():
    """
    Function to determine if a user is authenticated
    by checking if the auth key is in the session.
    """

    if "auth" in session:
        return True
    return False


def get_categories():
    """
    Function to get a dictionary of categories.
    """

    # Query the database to return categories
    categories = query("select * \
                        from categories \
                        order by category_display_name asc")

    return categories


def get_slug(slug, title):
    """
    Function to generate a unique slug for a post.
    """

    # Check if slug value is blank, if it is, transform the title into a slug
    if (slug.strip() == ""):
        slug = title.strip().lower().replace(" ", "-")
    # Otherwise make sure the slug is formatted properly
    else:
        slug = slug.strip().lower().replace(" ", "-")

    # Check the db for matching slugs and 
    slugs = query("select slug \
                    from posts \
                    where slug = ? or slug GLOB ?", (slug, slug + "-[0-9]"))
    
    if slugs:
        slug = slug + "-" + str(len(slugs))
    
    return slug

# Index route
@app.route('/')
def index():
    """
    Function to determine the proper route to redirect to
    for the root route of the application.
    """

    # Initialize the database if necessary
    # Not an ideal place for this, but will do for testing
    init_db()

    # Set the breadcrumbs for the route
    breadcrumbs = [
        {"title": "Home", "url": "/"}
    ]

    # Query the database to return posts
    posts = query("select p.*, \
                  c.category_name, \
                  c.category_display_name, \
                  u.first_name as author_first_name, \
                  u.last_name as author_last_name \
            from posts p \
            inner join categories c \
            on c.id = p.category_id \
            inner join users u \
            on u.id = p.author_id \
            where p.is_published = 1 and published_at <= ?\
            order by updated_at desc, published_at desc", (datetime.datetime.now(),))

    return render_template("public/index.html",
                               breadcrumbs=breadcrumbs,
                               posts=posts,
                               categories=get_categories(),
                               page=1,
                               alert=session.pop("alert", None)
                               )


# Login route - GET
@app.route('/register')
def get_register():
    """
    Function to display the registration form to register
    a new user for the application.
    """

    # Check if authenticated, if not, render the registration page
    if not check_auth():
        # Set the breadcrumbs for the route
        breadcrumbs = [
            {"title": "Home", "url": "/"},
            {"title": "Register", "url": "/register"}
        ]

        return render_template("auth/register.html",
                               breadcrumbs=breadcrumbs,
                               errors=session.pop("errors", None),
                               alert=session.pop("alert", None)
                               )
    # Otherwise redirect to the dashboard
    else:
        return redirect("/dashboard")


# Register route - POST
@app.route('/register', methods=['POST'])
def post_register():
    """Function to register a user upon form submission.
    Validates data and either adds user or returns error messages.
    """
    # Check if authenticated, if not, redirect to login page
    if check_auth():
        return redirect("/dashboard")

    def validate(form):
        """Function to validate the new user data."""

        # Dictionary to store error messages and original input in
        validation_errors = {"messages": {}, "input": {}}

        # Validate first_name input field
        if (form["first_name"].strip() == ""):
            validation_errors["messages"].update(
                {"first_name": "First name is a required field."})

        # Validate last_name input field
        if (form["last_name"].strip() == ""):
            validation_errors["messages"].update(
                {"last_name": "Last name is a required field."})

        # Validate email input field
        if not re.search(r'^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$',
                         form["email"]):
            validation_errors["messages"].update(
                {"email": "A valid email address is required."})

        # Validate password input field
        if len(form['password']) < 8:
            validation_errors["messages"].update(
                {"password": "Password must be at least 8 characters long."})

        # Validate password_confirm input field
        if (form["password_confirm"].strip() == ""):
            validation_errors["messages"].update(
                {"password_confirm": "Password confirmation is a required field."})
        if (form["password_confirm"] != form["password"]):
            validation_errors["messages"].update(
                {"password_confirm": "Passwords do not match."})

        # If there are messages in the dictionary, add the original input
        if validation_errors["messages"]:
            validation_errors.update({"input": dict(form)})
        # Otherwise reset the dictionary to empty
        else:
            validation_errors = {}

        # Return the dictionary
        return validation_errors

    # Call the validate function and store the return value in a variable
    validation = validate(request.form)
    # If the dictionary is empty, insert the user in the database
    if not validation:
        row_id = insert("Insert into users\
                (first_name, last_name, email, password)\
                values (?, ?, ?, ?)",
                    (
                        request.form["first_name"],
                        request.form["last_name"],
                        request.form["email"],
                        request.form["password"]
                    )
                )

        session['auth'] = {
            'id': row_id,
            'first_name': request.form["first_name"],
            'last_name': request.form["last_name"],
            'email':  request.form["email"]
        }

        # Add an alert message to the session to be displayed on the page
        session["alert"] = {
            "level": "success",
            "message": "Success registered!"
        }

        # Redirect to the dashboard
        return redirect("/dashboard")
    # Otherwise redirect back and display the error messages
    else:
        # Add the errors to be displayed to the session
        session["errors"] = validation
        # Redirect back to /register
        return redirect("/register")

# Login route - GET
@app.route('/login')
def get_login():
    """
    Function to check if a user is not authenticated and render the
    template to login if they're not or redirect to the dashboard
    if they are.
    """

    # Check if authenticated, if not, render the login page
    if not check_auth():
        return render_template("auth/login.html",
                               alert=session.pop("alert", None)
                               )
    # Otherwise redirect to the dashboard
    else:
        return redirect("/dashboard")


# Login route - POST
@app.route('/login', methods=['POST'])
def post_login():
    """Function to authenticate a user upon login form submission."""

    def authenticate(email, password):
        """Function to validate provided credentials."""

        # Query the database to see if email and password input
        # match a row in the users table
        auth = query("select id, \
                            first_name,\
                            last_name,\
                            email\
                            from users\
                            where email = ? and password = ?",
                     (email, password),
                     True
                     )
        # Returns the result, type None or dict
        return auth

    # Call the validation function and store the result in a variable
    auth = authenticate(request.form["email"], request.form["password"])
    # Check to see if authenticated, if so put the returned
    # data in the session and redirect to the dashboard
    if auth:
        session['auth'] = auth
        session["alert"] = {
            "level": "success",
            "message": "Successfully logged in!"
        }
        return redirect("/dashboard")
    # Otherwise set an alert message and redirect
    # to the login page
    else:
        session["alert"] = {
            "level": "danger",
            "message": "Could not validate the provided credentials. Please try again!"
        }
        return redirect("/login")


# Logout route
@app.route('/logout')
def logout():
    """
    Function to logout the authenticated user.
    """

    # Check if authenticated, if so pop the
    # auth key from the session
    if check_auth():
        session.pop("auth", None)
    # Redirect to the application root
    return redirect("/")


# Dashboard route
@app.route('/dashboard')
def dashboard():
    """
    Function to render the dashboard template to.
    """

    # Check if authenticated, if not, redirect to login page
    if not check_auth():
        return redirect("/login")

    # Otherwise continue
    # Set the breadcrumbs for the route
    breadcrumbs = [
        {"title": "Home", "url": "/"},
        {"title": "Dashboard", "url": "/dashboard"}
    ]
    # Query the database to return posts belonging to the authenticated user
    posts = query("select p.*, \
                  c.category_name, \
                  c.category_display_name, \
                  u.first_name, \
                  u.last_name \
            from posts p \
            inner join categories c \
            on c.id = p.category_id \
            inner join users u \
            on u.id = p.author_id \
            where u.id = ? \
            order by updated_at desc, published_at desc", (session['auth']['id'], ))

    # Render the dashboard template, passing in
    # breadcrumbs, posts, and alerts
    return render_template("admin/dashboard.html",
                           breadcrumbs=breadcrumbs,
                           posts=posts,
                           categories=get_categories(),
                           alert=session.pop("alert", None)
                           )


# View post route
@app.route('/post/<id>')
def get_post(id):
    """
    Function to render the view_post template.
    Queries the database for a record matching the
    id or slug argument.
    """

    # Query the database to find the post with the
    # id number passed in

    post = query("select p.*, \
                         c.category_name, \
                         c.category_display_name, \
                         u.first_name author_first_name, \
                         u.last_name author_last_name\
                    from posts p \
                    inner join categories c \
                    on c.id = p.category_id \
                    inner join users u \
                    on u.id = p.author_id \
                    where p.id = ? or p.slug = ?", (id, id), True)

    # Check that a row was returned, if not abort with a 404 error
    if not post:
        abort(404)

    # Set the breadcrumbs for the route
    breadcrumbs = [
        {"title": "Home", "url": "/"},
        {"title": post['category_display_name'], "url": "/category/"+post['category_name']},
        {"title": post['title'], "url": "/post/"+post['slug']}
    ]
    # Render the view_post template, passing in
    # breadcrumbs, post, and alerts
    return render_template("public/view_post.html",
                           breadcrumbs=breadcrumbs,
                           post=post,
                           alert=session.pop("alert", None)
                           )


# Add post route - GET
@app.route('/post/add')
def get_add_post():
    """
    Function to render the add_post template and pass errors and alerts.
    """

    # Check if authenticated, if not, redirect to login page
    if not check_auth():
        return redirect("/login")

    # Set the breadcrumbs for the route
    breadcrumbs = [
        {"title": "Home", "url": "/"},
        {"title": "Dashboard", "url": "/dashboard"},
        {"title": "Add Post", "url": "/post/add"}
    ]

    # Render the template, passing in
    # breadcrumbs, errors, and alerts
    return render_template("admin/add/add_post.html",
                           breadcrumbs=breadcrumbs,
                           categories=get_categories(),
                           errors=session.pop("errors", None),
                           alert=session.pop("alert", None)
                           )


# Add post route - POST
@app.route('/post/add', methods=['POST'])
def post_add_post():
    """
    Function to run on submit. Validates data and either
    adds post or returns error messages.
    """

    # Check if authenticated, if not, redirect to login page
    if not check_auth():
        return redirect("/login")

    def validate(form):
        """Function to validate the new post data."""

        # Dictionary to store error messages and original input in
        validation_errors = {"messages": {}, "input": {}}

        # Validate category_id input field
        if (form["category_id"].strip() == ""):
            validation_errors["messages"].update(
                {"category_id": "Category is required."})
        # Check that category exists
        elif (not query("select id \
                        from categories \
                        where id = ?",
                        (int(form["category_id"]), ),
                        True)):
            validation_errors["messages"].update(
                {"category_id": "Please select a category from the list."})

        # Validate title input field
        if (form["title"].strip() == ""):
            validation_errors["messages"].update(
                {"last_name": "Title is a required field."})

        # Validate content input field
        if (form["content"].strip() == ""):
            validation_errors["messages"].update(
                {"content": "Post content is required."})

        # Validate published_at input field
        if (form["published_at"].strip() != ""):
            try:
                datetime.datetime.strptime(form["published_at"], '%Y-%m-%d %H:%M')
            except ValueError:
                validation_errors["messages"].update(
                    {"published_at": "A valid date is required."})

        # If there are messages in the dictionary, add the original input
        if validation_errors["messages"]:
            validation_errors.update({"input": dict(form)})
        # Otherwise reset the dictionary to empty
        else:
            validation_errors = {}

        # Return the dictionary
        return validation_errors

    # Call the validate function and store the return value in a variable
    validation = validate(request.form)
    # If the dictionary is empty, insert the post in the database
    if not validation:
        slug = get_slug(request.form["slug"], request.form["title"])
        timestamp = datetime.datetime.now() \
                        if request.form["published_at"].strip() == "" \
                        else datetime.datetime.strptime(
                                request.form["published_at"], '%Y-%m-%d %H:%M')
        is_published = 1 if not request.form.get('save', None) else 0
        row_id = insert("Insert into posts\
                        (\
                            author_id,\
                            category_id,\
                            title,\
                            slug,\
                            short_content,\
                            content,\
                            is_published,\
                            published_at,\
                            updated_at\
                        )\
                        values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            session["auth"]["id"],
                            request.form["category_id"],
                            request.form["title"],
                            slug,
                            request.form["short_content"],
                            request.form["content"],
                            is_published,
                            timestamp,
                            timestamp
                        )
                    )

        # Add an alert message to the session to be displayed on the page
        session["alert"] = {
            "level": "success",
            "message": "Post added successfully!"
        }

        # Redirect to the new post
        return redirect("/post/{}".format(slug))
    # Otherwise redirect back and display the error messages
    else:
        # Add the errors to be displayed to the session
        session["errors"] = validation
        # Redirect back to /post/add
        return redirect("/post/add")


# Edit post route - GET
@app.route('/post/<id>/edit')
def get_edit_post(id):
    """
    Function to render the edit_post template and pass errors and alerts.
    """

    # Check if authenticated, if not, redirect to login page
    if not check_auth():
        return redirect("/login")

    # Query the database to find the post with the
    # id passed in belonging to the authenticated user
    post = query("select * \
                from posts \
                where id = ? or slug = ? and author_id = ?",
                (id, id, session["auth"]["id"]), True)

    # Check that a row was returned, if not abort with a 404 error
    if not post:
        abort(404)

    # Set the breadcrumbs for the route
    breadcrumbs = [
        {"title": "Home", "url": "/"},
        {"title": "Dashboard", "url": "/dashboard"},
        {"title": post['title'], "url": "/post/"+post['slug']},
        {"title": "Edit Post", "url": "/post/{}/edit".format(post['slug'])}
    ]

    # Render the template, passing in
    # breadcrumbs, categories, post, errors, and alerts
    return render_template("admin/edit/edit_post.html",
                           breadcrumbs=breadcrumbs,
                           categories=get_categories(),
                           post=post,
                           errors=session.pop("errors", None),
                           alert=session.pop("alert", None)
                           )


# Edit post route - POST
@app.route('/post/<id>/edit', methods=['POST'])
def post_edit_post(id):
    """
    Function to run on submit. Validates data and either
    edits post or returns error messages.
    """

    # Check if authenticated, if not, redirect to login page
    if not check_auth():
        return redirect("/login")

    # Query the database to find the post with the
    # id passed in belonging to the authenticated user
    post = query("select * \
                from posts \
                where id = ? or slug = ? and author_id = ?",
                (id, id, session["auth"]["id"]), True)

    # Check that a row was returned, if not abort with a 404 error
    if not post:
        abort(404)

    def validate(form):
        """Function to validate the new post data."""

        # Dictionary to store error messages and original input in
        validation_errors = {"messages": {}, "input": {}}

        # Validate category_id input field
        if (form["category_id"].strip() == ""):
            validation_errors["messages"].update(
                {"category_id": "Category is required."})
        # Check that category exists
        elif (not query("select id \
                        from categories \
                        where id = ?",
                        (int(form["category_id"]), ),
                        True)):
            validation_errors["messages"].update(
                {"category_id": "Please select a category from the list."})

        # Validate title input field
        if (form["title"].strip() == ""):
            validation_errors["messages"].update(
                {"last_name": "Title is a required field."})

        # Validate content input field
        if (form["content"].strip() == ""):
            validation_errors["messages"].update(
                {"content": "Post content is required."})

        # Validate published_at input field
        if (form["published_at"].strip() != ""):
            try:
                datetime.datetime.strptime(form["published_at"], '%Y-%m-%d %H:%M')
            except ValueError:
                validation_errors["messages"].update(
                    {"published_at": "A valid date is required."})

        # If there are messages in the dictionary, add the original input
        if validation_errors["messages"]:
            validation_errors.update({"input": dict(form)})
        # Otherwise reset the dictionary to empty
        else:
            validation_errors = {}

        # Return the dictionary
        return validation_errors

    # Call the validate function and store the return value in a variable
    validation = validate(request.form)
    # If the dictionary is empty, insert the post in the database
    if not validation:
        timestamp = datetime.datetime.now()
        is_published = 1 if request.form.get('publish', None) \
                        else 0 if request.form.get('unpublish', None) \
                                else post["is_published"]
        row_id = update("update posts \
                        set category_id = ?, \
                            title = ?,\
                            short_content = ?,\
                            content = ?,\
                            is_published = ?,\
                            published_at = ?,\
                            updated_at = ? \
                        where id = ? and author_id = ?",
                        (
                            request.form["category_id"],
                            request.form["title"],
                            request.form["short_content"],
                            request.form["content"],
                            is_published,
                            datetime.datetime.strptime(
                                                request.form["published_at"]
                                                , '%Y-%m-%d %H:%M'),
                            timestamp,
                            post["id"],
                            session["auth"]["id"]
                        )
                    )

        # Add an alert message to the session to be displayed on the page
        session["alert"] = {
            "level": "success",
            "message": "Post updated successfully!"
        }

        # Redirect to the new post
        return redirect("/post/{}".format(post["slug"]))
    # Otherwise redirect back and display the error messages
    else:
        # Add the errors to be displayed to the session
        session["errors"] = validation
        # Redirect back to /post/{}/edit
        return redirect("/post/{}/edit".format(id))


# Delete post route - GET
@app.route('/post/<id>/delete')
def get_delete_post(id):
    """
    Function to delete a post.

    Queries the database for records matching the
    id argument and deletes them.
    """

    # Check if authenticated, if not, redirect to login page
    if not check_auth():
        return redirect("/login")

    # Query the database to find the post with the
    # id number passed in belonging to the authenticated user
    post = query("select * from posts\
                      where id = ? and author_id = ?", (id, session["auth"]["id"]), True)

    # Check that a row was returned, if not return an HTTP 404 error
    if not post:
        abort(404)

    # Execute the delete statements
    delete("delete from posts where id = ?", (id, ))

    # Add an alert message to the session
    session["alert"] = {
        "level": "success",
        "message": "Deleted post successfully."
    }
    return redirect("/dashboard")


# View category route
@app.route('/category/<id>')
def get_category(id):
    """
    Function to render the view_category template.
    Queries the database for a record matching the
    id argument.
    """

    # Query the database to find the category with the
    # id passed in
    category = query("select * \
                    from categories \
                    where id = ? or category_name = ?", (id, id), True)

    # Check that a row was returned, if not abort with a 404 error
    if not category:
        abort(404)

    # Query the database to return posts
    posts = query("select p.*, \
                    u.first_name as author_first_name, \
                    u.last_name as author_last_name \
                from posts p \
                inner join users u \
                on u.id = p.author_id \
                where p.is_published = 1 and p.published_at <= ? \
                    and p.category_id = ?\
                order by p.updated_at desc, p.published_at desc",
                (datetime.datetime.now(), category["id"]))

    # Set the breadcrumbs for the route
    breadcrumbs = [
        {"title": "Home", "url": "/"},
        {"title": category['category_display_name'],
                "url": "/category/"+category['category_name']},
    ]
    # Render the view_category template, passing in
    # breadcrumbs, category, posts, and alerts
    return render_template("public/view_category.html",
                           breadcrumbs=breadcrumbs,
                           category=category,
                           categories=get_categories(),
                           posts=posts,
                           page=1,
                           alert=session.pop("alert", None)
                           )


# Add category route - GET
@app.route('/category/add')
def get_add_category():
    """
    Function to render the add_category template and pass errors and alerts.
    """

    # Check if authenticated, if not, redirect to login page
    if not check_auth():
        return redirect("/login")

    # Set the breadcrumbs for the route
    breadcrumbs = [
        {"title": "Home", "url": "/"},
        {"title": "Dashboard", "url": "/dashboard"},
        {"title": "Add Category", "url": "/category/add"}
    ]

    # Render the template, passing in
    # breadcrumbs, errors, and alerts
    return render_template("admin/add/add_category.html",
                           breadcrumbs=breadcrumbs,
                           errors=session.pop("errors", None),
                           alert=session.pop("alert", None)
                           )


# Add category route - POST
@app.route('/category/add', methods=['POST'])
def post_add_category():
    """
    Function to run on submit. Validates data and either
    adds category or returns error messages.
    """

    # Check if authenticated, if not, redirect to login page
    if not check_auth():
        return redirect("/login")

    def validate(form):
        """Function to validate the new category data."""

        # Dictionary to store error messages and original input in
        validation_errors = {"messages": {}, "input": {}}

        # Validate category_name input field
        if (form["category_name"].strip() == ""):
            validation_errors["messages"].update(
                {"category_name": "Category name is required."})
        # Check if category exists
        elif (query("select category_name \
                        from categories \
                        where category_name = ?",
                        (form["category_name"], ),
                        True)):
            validation_errors["messages"].update(
                {"category_name": "Category name already exists."})

        # Validate title input field
        if (form["category_display_name"].strip() == ""):
            validation_errors["messages"].update(
                {"last_name": "Category display name is a required field."})

        # If there are messages in the dictionary, add the original input
        if validation_errors["messages"]:
            validation_errors.update({"input": dict(form)})
        # Otherwise reset the dictionary to empty
        else:
            validation_errors = {}

        # Return the dictionary
        return validation_errors

    # Call the validate function and store the return value in a variable
    validation = validate(request.form)
    # If the dictionary is empty, insert the category in the database
    if not validation:
        insert("Insert into categories\
                        (\
                            category_name,\
                            category_display_name,\
                            category_description\
                        )\
                        values (?, ?, ?)",
                        (
                            request.form["category_name"].lower(),
                            request.form["category_display_name"],
                            request.form["category_description"]
                        )
                    )

        # Add an alert message to the session to be displayed on the page
        session["alert"] = {
            "level": "success",
            "message": "Category added successfully!"
        }

        # Redirect to the new category
        return redirect("/category/{}".format(request.form["category_name"].lower()))
    # Otherwise redirect back and display the error messages
    else:
        # Add the errors to be displayed to the session
        session["errors"] = validation
        # Redirect back to /category/add
        return redirect("/category/add")


# Edit category route - GET
@app.route('/category/<id>/edit')
def get_edit_category(id):
    """
    Function to render the edit_category template and pass errors and alerts.
    """

    # Check if authenticated, if not, redirect to login page
    if not check_auth():
        return redirect("/login")

    # Query the database to find the category with the
    # id passed in
    category = query("select * \
                        from categories \
                        where id = ? or category_name = ?",
                        (id, id),
                        True)

    # Check that a row was returned, if not abort with a 404 error
    if not category:
        abort(404)

    # Set the breadcrumbs for the route
    breadcrumbs = [
        {"title": "Home", "url": "/"},
        {"title": "Dashboard", "url": "/dashboard"},
        {"title": category["category_display_name"], "url": "/category/"+category['category_name']},
        {"title": "Edit Category", "url": "/category/{}/edit".format(category['category_name'])}
    ]

    # Render the template, passing in
    # breadcrumbs, category, errors, and alerts
    return render_template("admin/edit/edit_category.html",
                           breadcrumbs=breadcrumbs,
                           category=category,
                           errors=session.pop("errors", None),
                           alert=session.pop("alert", None)
                           )


# Edit category route - POST
@app.route('/category/<id>/edit', methods=['POST'])
def post_edit_category(id):
    """
    Function to run on submit. Validates data and either
    edits category or returns error messages.
    """

    # Check if authenticated, if not, redirect to login page
    if not check_auth():
        return redirect("/login")

    # Query the database to find the category with the
    # id passed in
    category = query("select * \
                        from categories \
                        where id = ? or category_name = ?",
                        (id, id),
                        True)

    # Check that a row was returned, if not abort with a 404 error
    if not category:
        abort(404)

    def validate(form):
        """Function to validate the new category data."""

        # Dictionary to store error messages and original input in
        validation_errors = {"messages": {}, "input": {}}

        # Validate category_name input field
        if (form["category_name"].strip() == ""):
            validation_errors["messages"].update(
                {"category_name": "Category name is required."})
        # Check if category exists
        elif (query("select category_name \
                        from categories \
                        where category_name = ? and id != ?",
                        (form["category_name"], category["id"]),
                        True)):
            validation_errors["messages"].update(
                {"category_name": "Category name already exists."})

        # Validate title input field
        if (form["category_display_name"].strip() == ""):
            validation_errors["messages"].update(
                {"last_name": "Category display name is a required field."})

        # If there are messages in the dictionary, add the original input
        if validation_errors["messages"]:
            validation_errors.update({"input": dict(form)})
        # Otherwise reset the dictionary to empty
        else:
            validation_errors = {}

        # Return the dictionary
        return validation_errors

    # Call the validate function and store the return value in a variable
    validation = validate(request.form)
    # If the dictionary is empty, insert the post in the database
    if not validation:
        update("update categories \
                set category_name = ?, \
                    category_display_name = ?,\
                    category_description = ?\
                where id = ?",
                (
                    request.form["category_name"],
                    request.form["category_display_name"],
                    request.form["category_description"],
                    category["id"]
                )
            )

        # Add an alert message to the session to be displayed on the page
        session["alert"] = {
            "level": "success",
            "message": "Category updated successfully!"
        }

        # Redirect to the updated category
        return redirect("/category/{}".format(request.form["category_name"].lower()))
    # Otherwise redirect back and display the error messages
    else:
        # Add the errors to be displayed to the session
        session["errors"] = validation
        # Redirect back to /category/{}/edit
        return redirect("/category/{}/edit".format(id))


# Delete category route - GET
@app.route('/category/<id>/delete')
def get_delete_category(id):
    """
    Function to delete a category.

    Queries the database for records matching the
    id argument and deletes them.
    """

    # Check if authenticated, if not, redirect to login page
    if not check_auth():
        return redirect("/login")

    # Query the database to find the category with the
    # id number passed in
    category = query("select * from categories\
                      where id = ?", (id, ), True)

    # Check that a row was returned, if not return an HTTP 404 error
    if not category:
        abort(404)

    # Check to see if posts have this category id
    posts = query("select id from posts\
                   where category_id = ?", (id, ))

    # If there are, return to dashboard with an error message
    if posts:
        # Add an alert message to the session to be displayed on the page
        session["alert"] = {
            "level": "danger",
            "message": "Category could not be deleted, \
                        there are {} posts in the category. \
                        Update the post(s) categories first."\
                            .format(len(posts))
        }
        # Redirect to the dashboard
        return redirect("/dashboard")

    # Execute the delete statements
    delete("delete from categories where id = ?", (id, ))

    # Add an alert message to the session
    session["alert"] = {
        "level": "success",
        "message": "Deleted category successfully."
    }
    return redirect("/dashboard")



@app.teardown_appcontext
def teardown(exception):
    close_connection(exception)


if __name__ == '__main__':
    app.run()
