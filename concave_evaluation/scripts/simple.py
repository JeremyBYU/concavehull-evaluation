import click


@click.group()
def cli():
    """Generates data and run benchmarks for concave algorithms"""

@cli.command()
def generate_fixtures():
    print("Hello")

if __name__ == "__main__":
    cli()
