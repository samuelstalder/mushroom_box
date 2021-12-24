from flask import Blueprint, request, abort, current_app

import db
from general import Temperatur, Humidity

blueprint = Blueprint("api", __name__)


@blueprint.route("/", methods=["GET"])
def list_api():
    routes = []
    for rule in current_app.url_map.iter_rules():
        url = str(rule)
        if not url.startswith("/api"):
            continue
        url = url.rstrip("/")

        methods = sorted(rule.methods)

        routes.append({
            "url": url,
            "methods": methods}
        )

    return {
        "routes": routes
    }


class Temp:
    MAPPING = {
        "box": "b",
        "time": "t",
        "value": "v"
    }

    @staticmethod
    @blueprint.route("/temp", methods=["GET"], )
    def entrypoint_tmp():
        """
            Returns all the humidities entries concerning all boxes 
            in the last hour.
        """
        box = request.args.get("box", default=None, type=int)
        return Temp.__handle(box)

    @staticmethod
    @blueprint.route("/temp/<int:tid>", methods=["GET"])
    def entrypoint_tmp_box(tid: int):
        """
            Returns all the entries concerning a single box
            from the last hour.
        """
        return Temp.__handle(tid)

    @staticmethod
    def __handle(tid):
        QUERY = """
                SELECT 
                    box, time, value 
                FROM 
                   temperatur 
                {where}
                ORDER BY 
                    time
                ASC;
                """

        # default
        where = """
                WHERE 
                    {cond} 
                {addition}
                """

        addition = ""

        if tid is not None:
            addition = "AND box = (?)"

        cond = handle_cond()
        where = where.format(cond=cond, addition=addition)
        query = QUERY.format(where=where)

        # get DB
        con = db.get_db()
        cur = con.cursor()

        if tid is not None:
            cur.execute(query, (tid, ))
        else:
            cur.execute(query)

        res = [Temperatur(*it).to_mapped_dict(Temp.MAPPING)
               for it in cur.fetchall()]

        cur.close()

        return {
            "mapping": Temp.MAPPING,
            "values": res
        }


class Hum:
    MAPPING = {
        "box": "b",
        "inner": "i",
        "time": "t",
        "value": "v"
    }

    @staticmethod
    @blueprint.route("/hum", methods=["GET"])
    def entrypoint_hum():
        """
            Returns all the humidities entries concerning all boxes 
            in the last hour.
        """
        box = request.args.get("box", default=None, type=int)
        return Hum.__handle(box)

    @staticmethod
    @blueprint.route("/hum/<int:tid>", methods=["GET"])
    def entrypoint_hum_box(tid: int):
        """
            Returns all the entries concerning a single box
            from the last hour.
        """
        return Hum.__handle(tid)

    @staticmethod
    def __handle_query(tid) -> str:
        QUERY = """
                SELECT 
                    box, inner, time, value 
                FROM 
                    humidity 
                WHERE
                    {cond}
                {addition}
                ORDER BY
                    time 
                ASC
                ;
                """
        cond = handle_cond()
        addition = ""

        if tid is not None:
            addition = "AND box = (?)"

        query = QUERY.format(cond=cond, addition=addition)
        return query

    @staticmethod
    def __handle(tid):
        query = Hum.__handle_query(tid)

        # get DB
        con = db.get_db()
        cur = con.cursor()

        if tid is not None:
            cur.execute(query, (tid, ))
        else:
            cur.execute(query)

        res = cur.fetchall()
        cur.close()

        return {
            "mapping": Hum.MAPPING,
            "values": [Humidity(*it).to_mapped_dict(Hum.MAPPING) for it in res]
        }


def handle_cond() -> str:
    from general import Conditions

    TIME = "time"
    UNTIL = TIME
    SINCE = 'strftime("%s", "now", "-1 hour")'

    cond = Conditions()
    until, since = cond.until, cond.since

    # illegal request
    if until is not None and since is None:
        abort(400)
    elif until is not None and since is not None:
        cond = "time BETWEEN {} and {}".format(since, until)
    else:  # until = None
        if since is None:  # smaller
            since = SINCE
        cond = "{} >= {}".format(UNTIL, since)
    return cond
