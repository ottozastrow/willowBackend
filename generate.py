import math

import matplotlib.pyplot as plt
import numpy as np


class Config:
    spacing = 0.22
    pipe_length = 0.5
    module_length = 5
    z_spacing = spacing
    module_length = module_length // z_spacing * z_spacing
    period = spacing * 16


def sineAroundCircle(trace):
    angle_x = 15
    radius = Config.module_length / (2 * np.pi * 5 / 360) / 3

    angles = np.linspace(0, math.radians(angle_x), 100)

    frequency = 1 / (trace["period"] / 64) * 2

    x = trace["xstart"] + (
        radius + trace["ampx"] * np.sin(frequency * (angles + trace["offset"]))
    ) * np.cos(angles)

    z = 0 + (
        radius + trace["ampx"] * np.sin(frequency * (angles + trace["offset"]))
    ) * np.sin(angles)

    y = (
        trace["ampy"] * np.sin((z + trace["offset"]) * 2 * np.pi / trace["period"])
        + trace["ystart"]
    )

    trace["x"] = x.tolist()
    trace["y"] = y.tolist()
    trace["z"] = z.tolist()


def generate_trace_points(trace):
    z = np.linspace(
        0, Config.module_length, int(Config.module_length / Config.z_spacing) * 20
    )
    x = (
        trace["ampx"] * np.sin((z + trace["offset"]) * 2 * np.pi / trace["period"])
        + trace["xstart"]
    )
    y = (
        trace["ampy"] * np.sin((z + trace["offset"]) * 2 * np.pi / trace["period"])
        + trace["ystart"]
    )

    trace["x"] = x.tolist()
    trace["y"] = y.tolist()
    trace["z"] = z.tolist()


def generate_crosssec(settings):
    rows = settings["myRows"]
    cols = settings["myCols"]
    subd = settings["mode"]  # subdivides curvature
    mode = 2 ** subd
    modeinv = {1: 4, 2: 2, 4: 1, 8: 0.5}

    xi = np.linspace(0, rows * Config.spacing, rows + 1)
    yi = np.linspace(0, cols * Config.spacing, cols + 1)
    traces = []
    if settings["verticals"]:
        for i in range(rows + 1):
            for j in range(cols + 1):
                trace = {"x": [], "y": [], "z": []}
                traces.append(trace)
                trace["period"] = Config.period
                trace["xstart"] = xi[i]
                trace["ystart"] = yi[j]
                trace["ampx"] = 0
                trace["ampy"] = 0
                trace["offset"] = 0

    if not settings["only_x"]:
        amp = Config.spacing * mode / 2
        for i in range(cols + 1):
            for j in range(rows):

                trace = {"x": [], "y": [], "z": []}
                traces.append(trace)
                trace["xstart"] = (
                    j // mode * Config.spacing * mode + Config.spacing / 2 * mode
                )
                trace["ystart"] = i * Config.spacing
                trace["ampx"] = amp
                trace["ampy"] = 0
                trace["period"] = Config.period / modeinv[mode]
                trace["offset"] = (
                    trace["period"] / 2 * (j % 2)
                    if modeinv[mode] > 1
                    else j / rows * Config.period
                )
                if settings["parallel"]:
                    trace["offset"] = 0

    amp = Config.spacing * mode / 2
    for j in range(rows + 1):
        for i in range(cols):

            trace = {"x": [], "y": [], "z": []}
            traces.append(trace)

            trace["ystart"] = (
                i // mode * Config.spacing * mode + Config.spacing / 2 * mode
            )

            trace["xstart"] = j * Config.spacing
            trace["ampy"] = amp
            trace["ampx"] = 0
            trace["period"] = Config.period / modeinv[mode]
            trace["offset"] = (
                trace["period"] / 2 * (i % 2)
                if modeinv[mode] > 1
                else i / cols * Config.period
            )
            if settings["parallel"]:
                trace["offset"] = 0

    for trace in traces:
        if settings["angled"]:
            sineAroundCircle(trace)
        else:
            generate_trace_points(trace)

    return traces


def visualize_points(x, y):
    w = max(x) - min(x)
    h = max(y) - min(y)
    plt.rcParams["figure.figsize"] = (8, h / w * 8)

    plt.scatter(x, y)
    plt.show()


def points_list_from_strand_xyz(trace):
    points = []
    for i in range(len(trace["x"])):
        points.append(
            [
                trace["x"][i],
                trace["y"][i],
                trace["z"][i],
            ]
        )
    return points


def write_obj_file(traces, path: str = "generater_output.obj"):
    def pt_to_str(pts):
        return [str((round(pt, 5))) for pt in pts]

    with open(path, "w") as ofile:
        vertex_count = 1
        for trace in traces:
            strand_points = points_list_from_strand_xyz(trace)
            for point in strand_points:
                line = "v " + " ".join(pt_to_str(point)) + "\n"
                ofile.write(line)
            indices = [
                str(i) for i in range(vertex_count, len(strand_points) + vertex_count)
            ]
            vertex_count += len(strand_points)
            indices = "l " + " ".join(indices) + "\n"
            ofile.write(indices)

    print("wrote obj file to ", path)
