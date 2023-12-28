from album.runner.api import get_args, setup, download_if_not_exists


def run():
    from pathlib import Path
    import zipfile
    import shutil

    dl_path = download_if_not_exists(
        "https://syncandshare.desy.de/index.php/s/5SJFRtAckjBg5gx/download/data_granules.zip", "data_granules.zip")

    # extract data_granules.zip
    if not Path(dl_path.parent).joinpath("data_granules").exists():
        with zipfile.ZipFile(dl_path, 'r') as zip_ref:
            zip_ref.extractall(dl_path.parent)

    # copy to target path
    shutil.copytree(dl_path.parent.joinpath("data_granules"), get_args().target_path)


setup(
    group="io.github.betaseg",
    name="download_granules",
    version="0.1.0",
    title="download_granules",
    description="An album solution to download granules from the DESY sync&share.",
    solution_creators=["Jan Philipp Albrecht"],
    cite=[],
    tags=["granules", "dataset"],
    license="MIT",
    album_api_version="0.5.5",
    args=[
        {
            "name": "target_path",
            "description": "target folder to extract data to. Folder should not exist yet.",
            "required": True
        },
    ],
    run=run,
)
