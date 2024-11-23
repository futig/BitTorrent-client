import click
from presentation.commands import download, distribute

    
@click.group()
def cli():
    """BitTorent"""

@cli.command("download")
@click.argument('torrent_file_path')
def download_cli(torrent_file_path):
    """Downloads torrent content"""
    download(torrent_file_path)
    click.echo("File succsessfully dowloaded")

@cli.command("distribute")
@click.argument('torrent_file_path')
def distribute_cli(torrent_file_path):
    """Distributes torrent content"""
    distribute(torrent_file_path)
    click.echo("File is served now")


if __name__ == "__main__":
    cli()
    
