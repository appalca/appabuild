from typing import Annotated
from typing import Optional

import typer

from appabuild.setup import initialize, do_build

app = typer.Typer()


@app.command()
def build(appabuild_config_path: Annotated[Optional[str], typer.Argument(
    help="AppaBuild environment configuration file, required unless --no-init is specified")],
          lca_config_path: Annotated[str, typer.Argument(help="LCA configuration file")],
          init: Annotated[bool, typer.Option(help="initialize AppaBuild environment")] = True):
    """
    Build an impact model and save it to the disk.
    An AppaBuild environment is initialized (background and foreground databases), unless --no-init is specified.

    """
    user_database = None
    if init is True:
        if not appabuild_config_path:
            print("AppaBuild configuration file and LCA configuration file are required for initialization")
            return
        user_database = initialize(appabuild_config_path)

    do_build(lca_config_path, user_database)
