import json

import flask
from flask import jsonify, request

from generate import generate_crosssec, write_obj_file

app = flask.Flask(__name__)
cache = None


@app.route("/")
def generate_pattern():
    global cache
    settings: dict = json.loads(request.args.get("settings"))  # type: ignore

    traces = generate_crosssec(settings)

    response = flask.jsonify({"lines3d": traces})
    cache = traces
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


@app.route("/export")
def export():
    global cache
    write_obj_file(cache)

    response = jsonify(success=True)
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


if __name__ == "__main__":
    app.run(debug=True)
