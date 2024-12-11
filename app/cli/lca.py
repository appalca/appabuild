import os

import typer
import yaml

from appabuild.model.builder import ImpactModelBuilder
from appabuild.setup import project_setup

app = typer.Typer()


@app.command()
def build(appabuild_config_path: str, lca_config_path: str):
    """
    Build an impact model and save it to the disk.
    :param appabuild_config_path: generic information required by Appa Build to run, such
    as location of EcoInvent or name of Brightway project. This config file should
    remain the same for all your LCAs.
    :param lca_config_path: information about the current LCA, such as functional unit,
    list of methods or parameters.
    :return:
    """
    with open(appabuild_config_path, "r") as stream:
        appabuild_config = yaml.safe_load(stream)
    with open(lca_config_path, "r") as stream:
        lca_config = yaml.safe_load(stream)
    project_setup(
        project_name=appabuild_config["project_name"],
        ecoinvent_name=appabuild_config["databases"]["ecoinvent"]["name"],
        ecoinvent_path=appabuild_config["databases"]["ecoinvent"]["path"],
        foreground_name=appabuild_config["databases"]["foreground"]["name"],
        foreground_path=appabuild_config["databases"]["foreground"]["path"],
        fu_name=lca_config["scope"]["fu"]["name"],
        parameters=lca_config["outputs"]["model"]["parameters"],
    )
    impact_model_builder = ImpactModelBuilder(
        database_name=lca_config["scope"]["fu"]["database"]
    )
    impact_model = impact_model_builder.build_impact_model(
        functional_unit=lca_config["scope"]["fu"]["name"],
        methods=lca_config["scope"]["methods"],
        metadata=lca_config["outputs"]["model"]["metadata"],
    )
    impact_model.to_yaml(
        os.path.join(
            lca_config["outputs"]["model"]["path"],
            f"{lca_config['outputs']['model']['name']}.yaml",
        ),
        compile_models=lca_config["outputs"]["model"]["compile"],
    )
    return impact_model
