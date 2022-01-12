import json

from quart import Quart, jsonify, request
from wickergen.braidGenerator.visualize import write_obj_file

from generate import generate_crosssec

app = Quart(__name__)
cache = None


@app.route("/")
def generate_pattern():
    global cache
    settings: dict = json.loads(request.args.get("settings"))  # type: ignore

    traces = generate_crosssec(settings)

    response = jsonify({"lines3d": traces})
    cache = traces
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


@app.route("/animate3d")
def generate_pattern3d():
    global cache
    settings: dict = json.loads(request.args.get("settings"))  # type: ignore

    traces = generate_crosssec(settings, animate3d=True)

    response = jsonify({"lines3d": traces})
    cache = traces
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


@app.route("/animate2d")
def generate_pattern2d():
    global cache
    settings: dict = json.loads(request.args.get("settings"))  # type: ignore

    traces = generate_crosssec(settings, animate2d=True)

    response = jsonify({"lines3d": traces})
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
