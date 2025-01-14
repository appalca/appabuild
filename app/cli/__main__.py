from .database import app as database_app
from .lca import app as lca_app
import typer

app = typer.Typer()
app.add_typer(database_app, name="database")
app.add_typer(lca_app, name="lca")


if __name__ == "__main__":
    typer.run(app)
