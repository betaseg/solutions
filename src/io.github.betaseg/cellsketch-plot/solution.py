import shutil

from album.runner.api import setup


def install():
    from git import Repo
    from album.runner.api import get_app_path
    clone_url = "https://github.com/betaseg/protocol-notebooks"
    to = get_app_path().joinpath("protocol-notebooks")
    Repo.clone_from(clone_url, to)
    assert (to.exists())


def run():
    from album.runner.api import get_args, get_app_path
    import papermill as pm
    from pathlib import Path
    import os
    import subprocess
    args = get_args()
    project = args.project
    to = get_app_path().joinpath("protocol-notebooks")
    notebook_path = to.joinpath('plots', 'run_plots.ipynb')
    cell_lib_path = to.joinpath('plots', 'cell.py')
    parent_path = notebook_path.parent
    output_path = args.output
    assert (notebook_path.exists())
    os.chdir(parent_path)
    Path(output_path).mkdir(exist_ok=True, parents=True)
    print("Saving plots to %s" % output_path)
    output_notebook = Path(output_path).joinpath("plots.ipynb")
    output_cell_lib = Path(output_path).joinpath("cell.py")

    if not output_notebook.exists():
        try:
            shutil.copyfile(cell_lib_path, output_cell_lib)
            pm.execute_notebook(notebook_path, str(output_notebook),
                                parameters=dict(project=str(project), output=str(output_path)))
        except pm.exceptions.PapermillExecutionError:
            pass
    subprocess.run(["jupyter", "notebook"], cwd=str(output_path))


setup(
    group="io.github.betaseg",
    name="cellsketch-plot",
    version="0.1.0",
    solution_creators=["Deborah Schmidt"],
    title="CellSketch: Plot analysis results",
    description="This solution plots exemplary spatial analysis results of a CellSketch project.",
    tags=["plots", "cellsketch"],
    cite=[{
        "text": "A. Müller, D. Schmidt, C. S. Xu, S. Pang, J. V. D'Costa, S. Kretschmar, C. Münster, T. Kurth, F. Jug, M. Weigert, H. F. Hess, M. Solimena; 3D FIB-SEM reconstruction of microtubule-organelle interaction in whole primary mouse β cells. J Cell Biol 1 February 2021; 220 (2): e202010039.",
        "doi": "https://doi.org/10.1083/jcb.202010039"
    }],
    album_api_version="0.5.1",
    args=[{
        "name": "project",
        "type": "directory",
        "required": True,
        "description": "The CellSketch project to be opened (.n5)."
    }, {
        "name": "output",
        "type": "directory",
        "required": True,
        "description": "Output directory where the plots will be saved to."
    }],
    covers=[{
        "description": "Plots generated by this solution.",
        "source": "cover.png"
    }],
    run=run,
    install=install,
    dependencies={'environment_file': """channels:
- conda-forge
- defaults
dependencies:
- python=3.9
- scikit-image=0.19.1
- papermill=2.3.4
- notebook=6.5.2
- z5py=2.0.16
- matplotlib=3.7.0
- tifffile=2023.2.27
- seaborn=0.12.2
- pandas=1.5.3
- numpy=1.24.2
- git=2.39.2
- gitpython=3.1.31
"""}
)
