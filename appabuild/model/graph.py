"""
Module containing all required classes and methods to create a mermaid graph from a set of foreground datasets.
"""

import os

import sympy
from mermaid.graph import Graph

from appabuild.database.databases import ForegroundDatabase
from appabuild.database.serialized_data import SerializedExchange
from appabuild.logger import logger


def extract_params_from_matching(matching: str):
    """
    Extract the list of parameters from a parameter matching.
    A parameter matching is an expression used to replace a parameter,
    for example energy: time * power.
    :param matching: a parameter matching.
    :return: the list of parameters used in the parameter matching.
    """
    # values = re.findall("[a-zA-Z_]+", matching)
    # return set(values)
    exp = sympy.simplify(matching)
    params = exp.atoms(sympy.Symbol)
    return set([str(param) for param in params])


def build_parameters_str(parameters: list[str], exchange: SerializedExchange) -> str:
    params = []
    matches = {}

    for key, value in exchange.parameters_matching.items():
        if type(value) in [str, dict]:
            matches[key] = value

    if exchange.switch is not None:
        for option in exchange.switch.options:
            for key, value in option.parameters_matching.items():
                if type(value) in [str]:
                    matches[key] = (
                        (matches[key] + " + " if key in matches else "")
                        + value
                        + " * "
                        + exchange.switch.name
                    )
                else:
                    matches[key] = exchange.switch.name

    params.extend(set(parameters).difference(matches.keys()))
    for key, value in matches.items():
        params.append(key + "=f(" + ",".join(extract_params_from_matching(value)) + ")")
    return ",".join(sorted(params))


def build_mermaid_graph(foreground_path: str, name: str) -> Graph:
    """
    Build a mermaid graph from a set of foreground datasets.
    :param foreground_path: the root path of the datasets.
    :param name: name of the root dataset.
    :return: a graph representing the set of foreground datasets and their dependencies.
    """
    if not os.path.exists(foreground_path):
        msg = f"No such directory {foreground_path}"
        logger.error(msg)
        raise ValueError(msg)

    foreground_database = ForegroundDatabase(
        name="",
        path=foreground_path,
    )
    foreground_database.find_activities_on_disk()
    activities = {
        activity.uuid: activity
        for activity in foreground_database.context.serialized_activities
    }
    if len(activities) == 0:
        msg = f"No foreground datasets found at the path {foreground_path}"
        logger.error(msg)
        raise ValueError(msg)

    if name not in activities:
        msg = f"No such foreground dataset with the name {name}"
        logger.error(msg)
        raise ValueError(msg)

    nodes_and_links = []
    activities_to_process = [activities[name]]
    while len(activities_to_process) > 0:
        activity = activities_to_process[0]
        activities_to_process.remove(activity)

        for exchange in activity.exchanges:
            if exchange.input is not None and exchange.input.uuid in activities.keys():
                dependency = activities[exchange.input.uuid]
                activities_to_process.append(dependency)

                params = build_parameters_str(dependency.parameters, exchange)
                link = (
                    activity.uuid
                    + "-->"
                    + ('|"' + params + '"|' if len(params) > 0 else "")
                    + dependency.uuid
                )
                nodes_and_links.append(link)

    graph = Graph(name, "flowchart TD\n" + "\n".join(nodes_and_links))
    return graph
