"""
Module containing all required classes and methods to create a mermaid graph from a set of foreground datasets.
"""

from typing import Dict, List

import sympy
from mermaid.graph import Graph

from appabuild.database.databases import ForegroundDatabase
from appabuild.database.serialized_data import SerializedActivity


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

    def extract_params_from_matching(matching: str) -> List[str]:
        """
        Extract the parameter of a parameters_matching.
        :param matching: a str representing a parameter matching.
        :return: a list of str.
        """
        exp = sympy.simplify(matching)
        params = exp.atoms(sympy.Symbol)
        return [str(param) for param in params]

    def build_worker(
        parent_activity: SerializedActivity | None,
        activity: SerializedActivity,
        params_matching: Dict[str, str],
    ):
        """
        Worker function use to build the mermaid graph.
        :param parent_activity: a SerializedActivity which depends on activity (can be None if root activity).
        :param activity: a SerializedActivity.
        :param params_matching: parameters matching used by parent_activity for parameters of activity.
        """
        activity_str = ""
        if parent_activity is not None:
            params = []
            for param in activity.parameters:
                if param in params_matching:
                    params.append(
                        param
                        + "=f("
                        + ", ".join(
                            extract_params_from_matching(params_matching[param])
                        )
                        + ")"
                    )
                else:
                    params.append(param)
            params = '|"' + ", ".join(params) + '"|' if len(params) > 0 else ""
            activity_str += (
                activity.uuid + " -->" + params + parent_activity.uuid + "\n"
            )

        for exchange in activity.exchanges:
            params_match = {}
            for match in exchange.parameters_matching:
                params_match[match] = exchange.parameters_matching[match]

            if exchange.input is not None and exchange.input.uuid in activities:
                activity_str += build_worker(
                    activity, activities[exchange.input.uuid], params_match
                )

        return activity_str

    graph_str = "flowchart TD\n" + build_worker(None, activities[name], {})

    graph = Graph(name, graph_str)
    return graph
