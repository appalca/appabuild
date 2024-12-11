import database
import lca
import typer

app = typer.Typer()
app.add_typer(database.app, name="database")
app.add_typer(lca.app, name="lca")


if __name__ == "__main__":
    app()
