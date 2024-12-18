import os
from filecmp import cmpfiles

import brightway2 as bw
from bw2data.tests import bw2test
from lca_algebraic import setForeground

from app.cli import lca


@bw2test
def test_build():
    """
    bw2package databases can be imported and edited in a Activity Browser project (already setup with Biosphere3).
    """
    bw.projects.set_current("test_project")

    bw.bw2setup()

    print('Importing technosphere database')
    bw.BW2Package.import_file(os.path.join(os.path.realpath(''), 'data/background_database', 'technosphere.bw2package'))

    print('Importing user database')
    bw.BW2Package.import_file(
        os.path.join(os.path.realpath(''), 'data/user_database', 'user_database_no_proxy.bw2package'))
    setForeground("user_database")

    lca.do_build("data/nvidia_ai_gpu_chip_test.yaml")

    (same_files, diff_files, irregular_names) = cmpfiles("data/output/expected", "data/output/actual",
                                                         ["nvidia_ai_gpu_chip.yaml"], shallow=False)

    print(f"same {same_files}")
    print(f"diff {diff_files}")
    print(f"filename {irregular_names}")

    assert (len(same_files) == 1)
