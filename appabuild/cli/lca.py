import os
import sys
from typing import Annotated, Optional

import mermaid as md
import typer
import yaml
from pydantic import ValidationError

from appabuild import setup
from appabuild.database.serialized_data import SerializedActivity
from appabuild.exceptions import BwDatabaseError
from appabuild.logger import log_validation_error, logger
from appabuild.model.graph import build_mermaid_graph

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
    try:
        foreground_database = None
        if init:
            if not appabuild_config_path:
                logger.error(
                    "AppaBuild configuration file and LCA config file are required for initialization",
                    exc_info=True,
                )
                raise ValueError()
            foreground_database = setup.initialize(appabuild_config_path)

        setup.build(lca_config_path, foreground_database)
    except (ValueError, ValidationError, BwDatabaseError):
        sys.exit(1)
    except Exception as e:
        logger.exception(str(e))
        sys.exit(1)


@app.command()
def validate_foreground_datasets(
    datasets_root: Annotated[
        str, typer.Argument(help="Root path of a set of foreground datasets.")
    ]
):
    """
    Validates a folder of foreground datasets. Show an error message for each invalid dataset.
    :param datasets_root: Root path of a set of foreground datasets.

    """
    files = os.listdir(datasets_root)
    total = len(files)
    nb_correct = 0

    logger.info("%d datasets at the root %s", total, datasets_root)
    for filename in files:
        logger.info("Validating dataset %s", filename)
        try:
            filepath = os.path.join(datasets_root, filename)
            with open(filepath, "r") as yaml_file:
                dataset = yaml.safe_load(yaml_file)

            dataset.update({"database": "", "uuid": ""})
            SerializedActivity.model_validate(dataset)

            nb_correct += 1
        except ValidationError as e:
            log_validation_error(e)
            logger.error("Dataset %s invalid", filename)
        else:
            logger.info("Dataset %s valid", filename)
    if nb_correct == total:
        logger.info("All the datasets have been validated")
    else:
        logger.info("%d/%s foreground datasets validated", nb_correct, total)


def validate_type(type: str) -> str:
    if type not in ["png", "svg"]:
        raise typer.BadParameter(f"Expected png or svg, got {type}")
    return type


def validate_size(size: int) -> int:
    if size <= 0:
        raise typer.BadParameter(f"Value expected to be superior to zero, got {size}")
    return size


@app.command()
def graph(
    path: Annotated[str, typer.Argument(help="Root path of foreground datasets")],
    fu_name: Annotated[
        str,
        typer.Argument(help="Name of the root dataset (without its file extension)"),
    ],
    type: Annotated[
        str,
        typer.Option(
            help="Type of the output image, can only be png or svg, the default type is png",
            callback=validate_type,
        ),
    ] = "png",
    width: Annotated[
        int, typer.Option(help="Width of the output image", callback=validate_size)
    ] = 750,
    height: Annotated[
        int, typer.Option(help="Height of the output image", callback=validate_size)
    ] = 750,
    sensitive: Annotated[
        bool, typer.Option(help="If the data used to build the graph are sensitive")
    ] = True,
):
    """
    Generate a mermaid graph from a set of foreground datasets and export it in an image file (PNG or SVG format).
    :param path: root path of the foreground datasets used to build the graph.
    :param fu_name: name of the dataset that will be the root of the graph.
    :param type: type of the output image, can only be png or svg.
    :param width: width of the output image.
    :param height: height of the output image.
    :param sensitive: if true, ask with a prompt if the data used to build the graph are sensitive.

    """
    try:
        if sensitive:
            agree = typer.confirm(
                "The data used to build the graph will be sent to a distant API, do you want to continue ?\n If you don't want to see this prompt, use the option --no-sensitive "
            )
            if not agree:
                exit(0)

        mermaid_graph = build_mermaid_graph(path, fu_name)
        render = md.Mermaid(mermaid_graph, width=width, height=height)
        if type == "svg":
            render.to_svg(fu_name + ".svg")
        elif type == "png":
            render.to_png(fu_name + ".png")
    except ValueError:
        exit(1)
    except Exception as e:
        logger.error(str(e))
        exit(1)
