import typer
import yaml

from appabuild.model.builder import ImpactModelBuilder
from appabuild.setup import project_setup

app = typer.Typer()


@app.command()
def init_build(appalca_config_path: str, lca_config_path: str):
    """
    Initialize a Brightway environment (background and foreground databases).
    Build an impact model and save it to the disk
    """
    init(appalca_config_path)
    build(lca_config_path)


@app.command()
def init(appalca_config_path: str):
    """
    Initialize a Brightway environment (background and foreground databases).
    :param appalca_config_path: generic information required by Appa LCA to be initialized, such
    as location of EcoInvent or name of Brightway project. This config file should
    remain the same for all your LCAs.
    """
    with open(appalca_config_path, "r") as stream:
        appalca_config = yaml.safe_load(stream)

    project_setup(
        project_name=appalca_config["project_name"],
        ecoinvent_name=appalca_config["databases"]["ecoinvent"]["name"],
        ecoinvent_path=appalca_config["databases"]["ecoinvent"]["path"],
        foreground_name=appalca_config["databases"]["foreground"]["name"],
        foreground_path=appalca_config["databases"]["foreground"]["path"],
        fu_name=appalca_config["databases"]["foreground"]["fu_activity"],
        parameters=appalca_config["parameters"],
    )


@app.command()
def build(lca_config_path: str):
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