#!/usr/bin/python
# -*- coding: utf-8 -*-

"""db.py: IS 211 Final Project."""

__author__ = 'Adam Volin'
__email__ = 'Adam.Volin56@spsmail.cuny.edu'

import sqlite3
from flask import current_app, g
import datetime


DATABASE = 'blog.db'


def make_dicts(cursor, row):
    """
    Function to create dictionaries from returned
    rows.
    """

    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))


def get_db():
    """
    Function to connect to and get the database
    connection.
    """

    db = getattr(g, '_database', None)

    if db is None:
        db = g._database = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
        db.row_factory = make_dicts

    return db


def query(query, args=(), one=False):
    """
    Function to query the database.
    """

    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()

    return (rv[0] if rv else None) if one else rv


def insert(query, vals=(), many=False):
    """
    Function to insert rows into the database.
    """

    if many:
        cur = get_db().executemany(query, vals)
    else:
        cur = get_db().execute(query, vals)

    last_row_id = cur.lastrowid
    cur.close()
    get_db().commit()
    return last_row_id


def update(query, vals=()):
    """
    Function to update rows from the database.
    """

    cur = get_db().execute(query, vals)
    cur.close()
    get_db().commit()
    return True


def delete(query, vals=()):
    """
    Function to delete rows from the database.
    """

    cur = get_db().execute(query, vals)
    cur.close()
    get_db().commit()
    return True


def close_connection(exception):
    """
    Function to close the connection to the database.
    """

    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    """
    Function to initialize the database schema
    and insert test data.
    """

    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

    # Check for records, insert test data if empty
    users = query("select * from users")
    categories = query("select * from categories")
    posts = query("select * from posts")

    if not users:
        insert("Insert into users (first_name, last_name, email, password)\
                     values (?, ?, ?, ?)",
                (
                    ("John", "Smith", "jsmith@example.com", "password"),
                    ("Jane", "Doe", "jdoe@example.com", "password"),
                    ("Amy", "Apple", "aapple@example.com", "password")
                ),
                True
            )
        print("Loaded dummy users into db")

    if not categories:
        insert("Insert into categories\
                (\
                    category_name,\
                    category_display_name,\
                    category_description\
                ) values (?, ?, ?)",
                (
                    ("python-basics", "Python Basics", "Posts about basic Python programming skills."),
                    ("advanced-python", "Advanced Python", "Posts about advanced Python programming skills."),
                ),
                True
            )
        print("Loaded dummy categories into db")

    if not posts:
        short_content = """
            <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Vitae auctor eu augue ut lectus arcu bibendum at varius. Arcu non sodales neque sodales ut etiam sit amet. Eget nunc lobortis mattis aliquam. Feugiat nisl pretium fusce id velit ut tortor pretium. Duis ut diam quam nulla porttitor. Ipsum dolor sit amet consectetur adipiscing. Quis lectus nulla at volutpat diam. Lorem ipsum dolor sit amet consectetur adipiscing elit duis tristique. Leo integer malesuada nunc vel risus commodo viverra. At ultrices mi tempus imperdiet nulla malesuada pellentesque. Viverra aliquet eget sit amet. Netus et malesuada fames ac turpis egestas integer eget aliquet. Fames ac turpis egestas integer eget aliquet.</p>
        """
        content = """
            <h1>Testing the content</h1><p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Vitae auctor eu augue ut lectus arcu bibendum at varius. Arcu non sodales neque sodales ut etiam sit amet. Eget nunc lobortis mattis aliquam. Feugiat nisl pretium fusce id velit ut tortor pretium. Duis ut diam quam nulla porttitor. Ipsum dolor sit amet consectetur adipiscing. Quis lectus nulla at volutpat diam. Lorem ipsum dolor sit amet consectetur adipiscing elit duis tristique. Leo integer malesuada nunc vel risus commodo viverra. At ultrices mi tempus imperdiet nulla malesuada pellentesque. Viverra aliquet eget sit amet. Netus et malesuada fames ac turpis egestas integer eget aliquet. Fames ac turpis egestas integer eget aliquet.</p><p>Non consectetur a erat nam. Urna molestie at elementum eu facilisis sed odio morbi quis. Orci dapibus ultrices in iaculis nunc. Ac feugiat sed lectus vestibulum. Feugiat sed lectus vestibulum mattis ullamcorper velit. Etiam erat velit scelerisque in dictum non consectetur a. Scelerisque varius morbi enim nunc faucibus. Turpis massa tincidunt dui ut ornare lectus. Eget nunc lobortis mattis aliquam. Proin libero nunc consequat interdum. Elementum integer enim neque volutpat ac tincidunt vitae.</p><p>Ut lectus arcu bibendum at varius vel pharetra. Posuere urna nec tincidunt praesent semper. Sit amet facilisis magna etiam tempor orci eu. Sapien eget mi proin sed libero enim. Lacus vel facilisis volutpat est velit egestas dui id ornare. Dui id ornare arcu odio ut sem. Eget lorem dolor sed viverra ipsum nunc aliquet bibendum enim. Fermentum leo vel orci porta non pulvinar neque laoreet. Volutpat ac tincidunt vitae semper. Ut sem viverra aliquet eget sit amet. Ac turpis egestas sed tempus urna et pharetra pharetra massa. In egestas erat imperdiet sed. Pharetra diam sit amet nisl suscipit adipiscing bibendum est.</p><p>Amet nisl suscipit adipiscing bibendum est ultricies integer quis. Viverra mauris in aliquam sem fringilla ut. Turpis nunc eget lorem dolor sed viverra ipsum nunc. Odio facilisis mauris sit amet massa. Feugiat pretium nibh ipsum consequat nisl vel pretium lectus quam. Turpis tincidunt id aliquet risus feugiat in. Blandit turpis cursus in hac habitasse platea. Nibh ipsum consequat nisl vel. Enim praesent elementum facilisis leo. Cursus vitae congue mauris rhoncus aenean vel elit scelerisque mauris. Accumsan tortor posuere ac ut consequat. Id venenatis a condimentum vitae sapien pellentesque.</p><p>Sed odio morbi quis commodo odio. Velit sed ullamcorper morbi tincidunt ornare massa eget egestas purus. Ullamcorper malesuada proin libero nunc consequat interdum varius. Porta nibh venenatis cras sed felis eget velit aliquet sagittis. Metus dictum at tempor commodo ullamcorper a lacus vestibulum sed. Egestas fringilla phasellus faucibus scelerisque eleifend. Aliquam sem et tortor consequat id porta nibh venenatis cras. Accumsan lacus vel facilisis volutpat est velit egestas. Egestas sed tempus urna et pharetra pharetra massa. Blandit cursus risus at ultrices mi tempus imperdiet. Risus nullam eget felis eget nunc lobortis mattis aliquam. Pellentesque pulvinar pellentesque habitant morbi tristique senectus et netus et.</p>
        """
        timestamp = datetime.datetime.now()
        insert("Insert into posts\
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
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    (1, 1, "Lorem Ipsum", "lorem-ipsum", short_content, content, 1, timestamp, timestamp),
                    (1, 2, "Lorem Doplor", "lorem-doplor", short_content, content, 1, timestamp, timestamp),
                    (2, 1, "Lorem Consectetur", "lorem-consectetur", short_content, content, 1, timestamp, timestamp),
                    (2, 2, "Lorem Ipsum", "lorem-ipsum-1", short_content, content, 1, timestamp, timestamp),
                    (3, 1, "Lorem Doplor", "lorem-doplor-1", short_content, content, 1, timestamp, timestamp),
                    (3, 2, "Lorem Consectetur", "lorem-consectetur-1", short_content, content, 1, timestamp, timestamp),
                    (1, 1, "Lorem Ipsum Dolor", "lorem-ipsum-dolor", short_content, content, 0, timestamp, timestamp),
                    (2, 2, "Lorem Ipsum Consectetur", "lorem-ipsum-consectetur", short_content, content, 0, timestamp, timestamp),
                    (3, 1, "Lorem Ipsum Ipsum", "lorem-ipsum-ipsum", short_content, content, 0, timestamp, timestamp)
                ),
                True
            )
        print("Loaded dummy posts results into db")
