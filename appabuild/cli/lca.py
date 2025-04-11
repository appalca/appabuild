from typing import Annotated, Optional

import mermaid as md
import typer

from appabuild import setup
from appabuild.logger import logger
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
def mermaid_graph(
    foreground_datasets_root: Annotated[
        str, typer.Argument(help="Root path of foreground datasets")
    ],
    name: Annotated[
        str,
        typer.Argument(help="Name of the root dataset (without its file extension)"),
    ],
):
    """
    Generate a mermaid graph from a set of foreground datasets and export it in an image file (SVG format).

    """
    graph = build_mermaid_graph(foreground_datasets_root, name)
    render = md.Mermaid(graph)
    render.to_svg(name + ".svg")
