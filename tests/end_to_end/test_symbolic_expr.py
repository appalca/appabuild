"""
Some symbolic expressions are not properly recreated after serialization/deserialization.
These tests assert that the fixes are properly
"""

import os

import pytest
import yaml
from apparun.impact_model import ImpactModel
from pydantic import ValidationError
from typer.testing import CliRunner

from appabuild.cli.lca import build
from tests import DATA_DIR

runner = CliRunner()


def test_build_minus_param():
    appaconf_file = os.path.join(DATA_DIR, "cmd_build", "appalca_conf_wo_ei.yaml")
    conf_file = os.path.join(
        DATA_DIR, "cmd_build", "functional_logic_die_manufacturing_lca_conf.yaml"
    )
    build(appaconf_file, conf_file)

    try:
        model = ImpactModel.from_yaml("functional_logic_die_manufacturing.yaml")
        model.get_scores()
    except ValidationError:
        pytest.fail("-param in a symbolic expression is valid")


def test_abs():
    appaconf_file = os.path.join(DATA_DIR, "cmd_build", "appalca_conf_wo_ei.yaml")
    conf_file = os.path.join(DATA_DIR, "cmd_build", "die_shrunk_lca_conf.yaml")
    build(appaconf_file, conf_file)

    try:
        model = ImpactModel.from_yaml("die_shrunk.yaml")
        model.get_scores()
    except ValidationError:
        pytest.fail("Abs() in a symbolic expression is valid")
