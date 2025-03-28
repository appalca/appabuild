import os
from typing import Annotated, Optional

import mermaid as md
import typer
import yaml
from apparun.impact_tree import ImpactTreeNode

from appabuild import setup
from appabuild.model.builder import ImpactModelBuilder
from appabuild.model.mermaid_graph import build_mermaid_graph

app = typer.Typer()


@app.command()
def build(
    appabuild_config_path: Annotated[
        Optional[str],
        typer.Argument(
            help="AppaBuild environment configuration file, required unless --no-init is specified"
        ),
    ],
    lca_config_path: Annotated[str, typer.Argument(help="LCA configuration file")],
    init: Annotated[bool, typer.Option(help="initialize AppaBuild environment")] = True,
):
    """
    Build an impact model and save it to the disk.
    An AppaBuild environment is initialized (background and foreground databases), unless --no-init is specified.

    """
    foreground_database = None
    if init:
        if not appabuild_config_path:
            print(
                "AppaBuild configuration file and LCA configuration file are required for initialization"
            )
            return
        foreground_database = setup.initialize(appabuild_config_path)

    setup.build(lca_config_path, foreground_database)


@app.command()
def mermaid(
    appabuild_config_path: Annotated[
        Optional[str],
        typer.Argument(
            help="AppaBuild environment configuration file, required unless --no-init is specified"
        ),
    ],
    name: str,
):
    """
    Generates a mermaid graph.

    """
    if not appabuild_config_path:
        print(
            "AppaBuild configuration file and LCA configuration file are required for initialization"
        )
        return
    graph = build_mermaid_graph(appabuild_config_path, name)
    render = md.Mermaid(graph)
    render.to_png("mermaid_graph.png")
