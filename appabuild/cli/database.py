import os

import typer
import yaml

from appabuild.database.generator.eime import EimeV6Generator

app = typer.Typer()


@app.command()
def generate_eime_v6(
    eime_v6_impacts_export_path: str, datasets_description_path: str, output_path: str
):
    """
    Generate yaml datasets readily usable by Appa Build from config file and
    Eime V6 impact exports. To generate the adequate export file, create a new Eime V6
    project, add a single phase (no particular phase name required), and add a copy of
    every dataset you want to export. Then, go to analysis page, tick all required PEF
    impact assessment method, and export the result as a xlsx file.
    Configuration file should contain all other information of the datasets you want
    to generate. Common fields across all datasets can be set once in a "default"
    dict. Specific fields can be provided as a list in a "datasets" dict. Each dataset
    should have a "name_in_export" key, which value is the name of the corresponding
    dataset in Eime V6 export.
    :param eime_v6_impacts_export_path: Eime V6 impact exports
    :param datasets_description_path: should contain all other information of the
    datasets you want to generate
    :param output_path: directory to save yaml files.
    :return:
    """
    with open(datasets_description_path, mode="r") as stream:
        datasets_description = yaml.safe_load(stream)
    generator = EimeV6Generator()
    generated_datasets = generator.generate_datasets(
        eime_v6_impacts_export_path, datasets_description
    )
    generator.save_datasets(generated_datasets, output_path)
