import math
from copy import deepcopy

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
from wickergen.braidGenerator import util_classes, utils, visualize
from wickergen.braidGenerator.util_classes import Arena, Strand


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


def generate_trace_from_settings(settings, is_x: bool):
    rows = settings["myRows"]
    cols = settings["myCols"]
    subd = settings["mode"]  # subdivides curvature
    mode = 2 ** subd
    modeinv = {1: 4, 2: 2, 4: 1, 8: 0.5}

    traces = []
    amp = Config.spacing * mode / 2

    if is_x:
        curves_per_plane = rows
        curves_per_row = cols
        amp_per_plane = amp
        amp_per_row = 0
        per_plane = "xstart"
        per_row = "ystart"

    else:
        curves_per_plane = cols
        curves_per_row = rows
        amp_per_plane = 0
        amp_per_row = amp
        per_plane = "ystart"
        per_row = "xstart"

    for i in range(curves_per_row + 1):
        for j in range(curves_per_plane):
            trace = {"x": [], "y": [], "z": []}
            traces.append(trace)

            trace[per_plane] = (
                j // mode * Config.spacing * mode + Config.spacing / 2 * mode
            )

            trace[per_row] = i * Config.spacing
            trace["ampx"] = amp_per_plane
            trace["ampy"] = amp_per_row
            trace["period"] = Config.period / modeinv[mode]
            trace["offset"] = (
                trace["period"] / 2 * (j % 2)
                if modeinv[mode] > 1
                else j / curves_per_row * Config.period
            )
            if settings["parallel"]:
                trace["offset"] = 0
    return traces


def compute_pipegear_position(strand) -> tuple[float, float, float]:
    # x = (max(strand.x) - min(strand.x)) / 2
    # y = (max(strand.y) - min(strand.y)) / 2
    x = strand.x[-1]
    y = strand.y[-1]
    z = min(strand.z) - 0.5
    return x, y, z


def compute_split_pipegear_position(strand) -> Strand:
    # x = (max(strand.x) - min(strand.x)) / 2
    # y = (max(strand.y) - min(strand.y)) / 2
    x = strand.x[-1]
    y = strand.y[-1]
    z = min(strand.z) - 0.5
    pipestrand = Strand(0)
    pipestrand.x = [strand.x, x]
    pipestrand.y = [strand.y, y]
    pipestrand.z = [strand.z - 0.07, z]
    return pipestrand


def calc_3d_robot_plane(
    strands: list[Strand],
    relative_time: float = 0.0,
    robot_pos_fn=compute_split_pipegear_position,
    steps=Arena.animation_steps,
    slice_height=Arena.interpolate_steps_per_meter,
) -> list[list[Strand]]:
    """
    relative_time: float between 0 and 1.
    starts 3d animation from that relative vertical position
    """
    minz, maxz = utils.min_max_z_from_strands(strands)
    # note: z is vertical component of 3d coordinate.
    # time is -z because we weave top-down
    cut_threshold = maxz - (maxz - minz) * relative_time

    animation_steps = []
    for i in range(steps):
        new_strands = []
        for strand in strands:
            # stop if animation has more steps then strand
            if i >= len(strand.z):
                break
            threshold = cut_threshold - i * slice_height
            new_strand = deepcopy(strand)
            indexes = np.argwhere(strand.z < threshold)
            new_strand.z = np.delete(new_strand.z, indexes)
            new_strand.x = np.delete(new_strand.x, indexes)
            new_strand.y = np.delete(new_strand.y, indexes)

            if len(new_strand.x) > 0:
                pipe_strand = robot_pos_fn(new_strand)

                new_strands.append(new_strand)
        animation_steps.append(new_strands)

    return animation_steps


def generate_crosssec(settings, animate2d=False, animate3d=False):
    rows = settings["myRows"]
    cols = settings["myCols"]

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
        traces += generate_trace_from_settings(settings, True)

    traces += generate_trace_from_settings(settings, False)

    for trace in traces:
        if settings["angled"]:
            sineAroundCircle(trace)
        else:
            generate_trace_points(trace)
    strands = list_to_strand(traces)

    if animate2d:
        visualize.plot_animated_strands(strands, False)

    if animate3d:
        utils.interpolate_strands(strands, kind="cubic", step_size=1)

        animated_strands_3d = visualize.calc_3d_robot_plane(
            strands, robot_pos_fn=compute_pipegear_position, steps=6, slice_height=0.05
        )

        visualize.plot_3d_animated_strands(animated_strands_3d, save=False)

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


def list_to_strand(traces):
    res = []
    for trace in traces:
        strand = util_classes.Strand(0)
        strand.x = trace["x"]
        strand.y = trace["y"]
        strand.z = trace["z"]
        res.append(strand)
    return res
