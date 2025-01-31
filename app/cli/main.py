from app.cli.database import app as database_app
from app.cli.lca import app as lca_app
import typer


cli_app = typer.Typer()
cli_app.add_typer(database_app, name="database")
cli_app.add_typer(lca_app, name="lca")


if __name__ == "__main__":
    cli_app()
