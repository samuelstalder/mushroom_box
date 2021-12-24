import sqlite3
from flask import g

DATABASE = "mushroom.db"

def db_shema_init(db: sqlite3.Connection):
    with open("schema.sql", "r") as file:
        schema = file.read()
        db.executescript(schema)
        db.commit()


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db_shema_init(db)
    return db


