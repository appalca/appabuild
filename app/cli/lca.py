from typing import Annotated
from typing import Optional

import typer
import yaml

from appabuild.model.builder import ImpactModelBuilder
from appabuild.setup import project_setup
from docopt import Argument

app = typer.Typer()


@app.command()
def build(lca_config_path: Annotated[str, typer.Argument(help="LCA configuration file")],
          appabuild_config_path: Annotated[Optional[str], typer.Argument(
              help="AppaBuild environment configuration file, required unless --no-init is specified")] = None,
          init: Annotated[bool, typer.Option(help="initialize AppaBuild environment")] = True):
    """
    Build an impact model and save it to the disk.
    An AppaBuild environment is initialized (background and foreground databases), unless --no-init is specified.

    """
    if init is True:
        if not appabuild_config_path:
            print("AppaBuild configuration file and LCA configuration file are required for initialization")
            return
        initialize(appabuild_config_path)

    do_build(lca_config_path)


def initialize(appabuild_config_path: str):
    """
    Initialize a Brightway environment (background and foreground databases).
    :param appabuild_config_path: generic information required by Appa Build to be initialized, such
    as location of EcoInvent or name of Brightway project. This config file should
    remain the same for all your LCAs.
    """
    with open(appabuild_config_path, "r") as stream:
        appabuild_config = yaml.safe_load(stream)

    project_setup(
        project_name=appabuild_config["project_name"],
        ecoinvent_name=appabuild_config["databases"]["ecoinvent"]["name"],
        ecoinvent_path=appabuild_config["databases"]["ecoinvent"]["path"],
        foreground_name=appabuild_config["databases"]["foreground"]["name"],
        foreground_path=appabuild_config["databases"]["foreground"]["path"],
        fu_name=appabuild_config["databases"]["foreground"]["fu_activity"],
        parameters=appabuild_config["parameters"],
    )


def do_build(lca_config_path: str):
    """
    Build an impact model and save it to the disk (to the location configured in the file).
    :param lca_config_path: information about the current LCA, such as functional unit,
    list of methods.
    :return the impact model
    """
    impact_model_builder = ImpactModelBuilder.from_yaml(lca_config_path)

    impact_model = impact_model_builder.build_impact_model()

    impact_model.to_yaml(
        impact_model_builder.output_path,
        impact_model_builder.compile_models
    )

    return impact_model
