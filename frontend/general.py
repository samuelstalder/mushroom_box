import datetime
from flask import request

INNER_BOX = 0


class __Base:
    def to_dict(self):
        raise NotImplementedError("This is a base class")

    def to_mapped_dict(self, mapping):
        inner = self.to_dict()
        outer = {}
        for key, val in inner.items():
            mapped = mapping[key]
            outer[mapped] = val
        return outer


class Humidity(__Base):
    def __init__(self, box, inner, time, value):
        self.box = box
        self.inner = inner == INNER_BOX
        self.time = datetime.datetime.fromtimestamp(time).isoformat()
        self.value = value

    def to_dict(self):
        return {
            "box": self.box,
            "inner": self.inner,
            "time": self.time,
            "value": self.value
        }


class Temperatur(__Base):
    def __init__(self, box, time, value) -> None:
        self.box = box
        self.time = datetime.datetime.fromtimestamp(time).isoformat()
        self.value = value

    def to_dict(self):
        return {
            "box": self.box,
            "time": self.time,
            "value": self.value
        }


class Conditions:
    def __init__(self):
        self.until = Conditions.__get("until")
        self.since = Conditions.__get("since")
        self.box = Conditions.__get("box")

        self.url = None

    @staticmethod
    def __get(name: str, default=None, type=int):
        return request.args.get(name, default, type)

    def is_valid(self) -> bool:
        return not (self.until and self.since is None)

    def to_url(self) -> str:
        if self.url:
            return self.url

        until = ""
        since = ""
        box = ""
        if self.until is not None:
            until = "until={}".format(self.until)
        if self.since is not None:
            since = "since={}".format(self.since)
        if self.box is not None:
            box = "box={}".format(self.box)

        self.url = "&".join((i for i in (until, since, box) if i != ""))

        return self.url
