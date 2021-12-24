import json
from flask import Blueprint, abort, current_app
from flask.templating import render_template
from markupsafe import Markup

import general

frontend = Blueprint("frontend", __name__)


class TemplateRequest:
    def __init__(self, url, title, inner, headers) -> None:
        self.url = url
        self.title = title
        self.inner = inner
        self.headers = headers

    def to_obj(self):
        return {
            "url": self.url,
            "inner": self.inner,
            "title": self.title,
            "headers": self.headers
        }

    def to_json(self):
        return json.dumps(self.to_obj())

    def to_markup(self):
        return Markup(self.to_json())


class __Base:

    def __init__(self):
        self.cond = general.Conditions()

    INNER = ""
    BACKEND = ""
    TITLE = ""
    HEADERS = {
    }

    def is_valid(self) -> bool:
        return self.cond.is_valid()

    def to_markup(self):
        backend = "{}?{}".format(self.BACKEND, self.cond.to_url())
        return TemplateRequest(backend, self.TITLE, self.INNER, self.HEADERS).to_markup()


class Temp(__Base):
    INNER = "temp"
    BACKEND = "/api/temp"
    TITLE = "Temperature Data"
    HEADERS = {
        "internal": ["box", "time", "value"],
        "external": ["Box ID",  "Time", "Value"],
    }


class Hum(__Base):
    INNER = "hum"
    BACKEND = "/api/hum"
    TITLE = "Humidity Data"
    HEADERS = {
        "internal": ["box", "inner", "time", "value"],
        "external": ["Box ID", "Is Inner", "Time", "Value"],
    }


@frontend.route("/", methods=["GET"])
def root():
    req = [Temp(), Hum()]
    return handle(req, "Overview")


@frontend.route("/temp", methods=["GET"])
def temp():
    req = Temp()
    return handle([req], "Temperature")


@frontend.route("/hum", methods=["GET"])
def hum():
    req = Hum()
    return handle([req], "Humidity")


def get_boxes():
    QUERY = """
        SELECT DISTINCT
            box
        FROM
            humidity
        ORDER by
            box
        ASC
        ;
    """
    # get DB
    import db
    con = db.get_db()
    cur = con.cursor()

    cur.execute(QUERY)
    res = cur.fetchall()
    cur.close()
    res = [i[0] for i in res]

    return res


def handle(requests, title):
    for r in requests:
        if not r.is_valid():
            abort(400)

    all_boxes = "All"
    selected = all_boxes
    boxes = [all_boxes]
    boxes.extend(get_boxes())
    cond = general.Conditions()

    if cond.box is not None:
        selected = cond.box

    return render_template("dynamic.html", requests=[r.to_markup() for r in requests], title=title, boxes=boxes, selected=selected, all_boxes=all_boxes)
