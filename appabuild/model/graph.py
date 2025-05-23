"""
Module containing all required classes and methods to create a mermaid graph from a set of foreground datasets.
"""

from typing import List

import sympy
from mermaid.graph import Graph

from appabuild.database.databases import ForegroundDatabase


def extract_params_from_matching(matching: str) -> List[str]:
    """
    Extract the list of parameters from a parameter matching.
    A parameter matching is an expression used to replace a parameter,
    for example energy: time * power.
    :param matching: a parameter matching.
    """
    exp = sympy.simplify(matching)
    params = exp.atoms(sympy.Symbol)
    return [str(param) for param in params]


def build_mermaid_graph(foreground_path: str, name: str) -> Graph:
    """
    Build a mermaid graph from a set of foreground datasets.
    :param foreground_path: the root path of the datasets.
    :param name: name of the root dataset.
    :return: a graph representing the set of foreground datasets and their dependencies.
    """
    foreground_database = ForegroundDatabase(
        name="",
        path=foreground_path,
    )
    foreground_database.find_activities_on_disk()
    activities = {
        activity.uuid: activity
        for activity in foreground_database.context.serialized_activities
    }

    nodes_and_links = []
    activities_to_process = [activities[name]]
    while len(activities_to_process) > 0:
        activity = activities_to_process[0]
        activities_to_process.remove(activity)

        for exchange in activity.exchanges:
            if exchange.input is not None and exchange.input.uuid in activities.keys():
                dependency = activities[exchange.input.uuid]
                activities_to_process.append(dependency)

                params = []
                for param in dependency.parameters:
                    if param in exchange.parameters_matching.keys():
                        matching = extract_params_from_matching(
                            exchange.parameters_matching[param]
                        )
                        params.append(param + "=f(" + ", ".join(matching) + ")")
                    else:
                        params.append(param)

                link = (
                    dependency.uuid
                    + "-->"
                    + ('|"' + ",".join(params) + '"|' if len(params) > 0 else "")
                    + activity.uuid
                )
                nodes_and_links.append(link)

    graph = Graph(name, "flowchart TD\n" + "\n".join(nodes_and_links))
    return graph
