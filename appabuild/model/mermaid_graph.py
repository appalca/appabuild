"""
Module containing all required classes and methods to create a mermaid graph from impact models.
"""

from typing import Dict

import yaml
from apparun.impact_model import ImpactModel
from apparun.impact_tree import ImpactTreeNode
from mermaid.graph import Graph


def build_worker(tree_node: ImpactTreeNode):
    print(tree_node.name)
    print("Models: ", tree_node.models)
    print("Direct impact: ", tree_node.direct_impacts)
    print("=" * 10)
    node_str = ""
    for sub_tree_node in tree_node.children:
        node_str += sub_tree_node.name + " -->|test|" + tree_node.name + "\n"
        node_str += build_worker(sub_tree_node)
    return node_str


def build_mermaid_graph(foreground_path: str, name: str):
    def build_worker(database_uuid: str):
        build_str = ""
        try:
            with open(foreground_path + database_uuid + ".yaml", "r") as stream:
                foreground = yaml.safe_load(stream)

            for database in foreground["exchanges"]:
                if "input" in database:
                    uuid = database["input"]["uuid"]

                    if uuid[0] != "(":
                        params = ",".join(foreground["parameters"])
                        if len(params) > 0:
                            params = "|" + params + "|"

                        build_str += uuid + " -->" + params + " " + database_uuid + "\n"
                        build_str += build_worker(uuid) + "\n"
        except FileNotFoundError:
            pass
        return build_str

    graph_str = "flowchart TD\n" + build_worker(name)

    print(graph_str)
    graph = Graph(name, graph_str)
    return graph
