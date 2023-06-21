from album.runner.api import setup

env_file = """name: cellsketch-ilastik-launcher
channels:
  - pytorch
  - ilastik-forge
  - conda-forge
  - nodefaults
dependencies:
  - python
  - ilastik=1.4.0b29
"""


def run():
    import subprocess

    subprocess.run(["ilastik"])


setup(
    group="io.github.betaseg",
    name="cellsketch-ilastik-launcher",
    version="0.1.0",
    title="ilastik-Launcher",
    description="An album solution to run ilastik",
    solution_creators=["Dominik Kutra", "Lucas Rieckert"],
    cite=[{"text": "Berg, S., Kutra, D., Kroeger, T. et al. ilastik: interactive machine learning for (bio)image analysis. Nat Methods 16, 1226–1232 (2019).",
           "url": "https://doi.org/10.1038/s41592-019-0582-9"}],
    covers=[{
        "description": "Logo of the ilastik suite.",
        "source": "cover.jpg"
    }],
    documentation=["README.md"],
    tags=["ilastik", "machine learning", "interactive", "open source", "image segmentation", "imaging", "python", "qt"],
    license="unlicense",
    album_api_version="0.5.5",
    args=[],
    run=run,
    dependencies={"environment_file": env_file},
)
