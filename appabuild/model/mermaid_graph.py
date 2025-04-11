"""
Module containing all required classes and methods to create a mermaid graph from impact models.
"""

import re
from typing import Dict

import yaml
from apparun.impact_model import ImpactModel
from apparun.impact_tree import ImpactTreeNode
from mermaid.graph import Graph

from appabuild.database.databases import ForegroundDatabase


def build_mermaid_graph(foreground_path: str, name: str):
    foreground_database = ForegroundDatabase(
        name="",
        path=foreground_path,
    )
    foreground_database.find_activities_on_disk()
    activities = {
        activity.uuid: activity
        for activity in foreground_database.context.serialized_activities
    }

    def build_worker(parent_activity, activity, params_matching):
        activity_str = ""
        if parent_activity is not None:
            params = []
            for param in activity.parameters:
                if param in params_matching:
                    regex = "[a-zA-Z_]+"
                    params.append(
                        param
                        + "=f("
                        + ", ".join(re.findall(regex, params_matching[param]))
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
