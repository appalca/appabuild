from typing import Annotated, Optional

import mermaid as md
import typer

from appabuild import setup
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


def validate_type(type: str) -> str:
    if type not in ["png", "svg"]:
        raise typer.BadParameter("Only png or svg allowed")
    return type


def validate_size(size: int) -> int:
    if size <= 0:
        raise typer.BadParameter("must be superior to 0")
    return size


@app.command()
def graph(
    path: Annotated[str, typer.Argument(help="Root path of foreground datasets")],
    fu_name: Annotated[
        str,
        typer.Argument(help="Name of the root dataset (without its file extension)"),
    ],
    type: Annotated[
        str, typer.Option(help="Output an image in PNG format", callback=validate_type)
    ] = "png",
    width: Annotated[
        int, typer.Option(help="Width of the output image", callback=validate_size)
    ] = 750,
    height: Annotated[
        int, typer.Option(help="Height of the output image", callback=validate_size)
    ] = 750,
):
    """
    Generate a mermaid graph from a set of foreground datasets and export it in an image file (SVG format).
    :param path: root path of the foreground datasets used to build the graph.
    :param fu_name: name of the dataset that will be the root of the graph.
    :param type: type of the output image, can only be png or svg, the default value is png.
    :param width: width of the output image.
    :param height: height of the output image.

    """
    mermaid_graph = build_mermaid_graph(path, fu_name)
    render = md.Mermaid(mermaid_graph, width=width, height=height)
    if type == "svg":
        render.to_svg(fu_name + ".svg")
    elif type == "png":
        render.to_png(fu_name + ".png")
