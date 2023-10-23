from album.runner.api import setup


def install():
    import subprocess
    import shutil
    from album.runner.api import get_app_path, get_package_path

    get_app_path().mkdir(exist_ok=True, parents=True)

    # copy source files into solution app folder
    shutil.copy(get_package_path().joinpath('build.gradle'), get_app_path())
    shutil.copy(get_package_path().joinpath('gradlew'), get_app_path())
    shutil.copy(get_package_path().joinpath('gradlew.bat'), get_app_path())
    shutil.copytree(get_package_path().joinpath('src'), get_app_path().joinpath('src'))
    shutil.copytree(get_package_path().joinpath('gradle'), get_app_path().joinpath('gradle'))

    subprocess.run([(get_gradle_executable()), 'build', '-Dorg.gradle.internal.http.socketTimeout=300000'],
                   cwd=get_app_path(), check=True)


def get_gradle_executable():
    from sys import platform
    from album.runner.api import get_app_path
    if platform == "win32":
        return str(get_app_path().joinpath('gradlew.bat').absolute())
    return str(get_app_path().joinpath('gradlew').absolute())


def run():
    import subprocess
    from pathlib import Path
    from album.runner.api import get_args, get_app_path
    params = ""
    args = get_args()
    for arg_name in args.__dict__:
        arg_val = args.__dict__[arg_name]
        if arg_val is not None:
            if is_file_arg(arg_name):
                params += "--%s '%s' " % (arg_name, str(Path(arg_val).absolute()))
            else:
                if isinstance(arg_val, bool):
                    if arg_val:
                        params += "--%s " % arg_name
                else:
                    params += "--%s '%s' " % (arg_name, arg_val)
    command = [get_gradle_executable(), 'run', '-q', '--args="%s"' % params]
    subprocess.run(command, cwd=get_app_path())


def is_file_arg(arg_name):
    from album.runner.api import get_active_solution
    solution_args = get_active_solution().setup()['args']
    for arg in solution_args:
        if arg['name'] == arg_name:
            return arg['type'] == 'file' or arg['type'] == 'directory'
    return False


setup(
    group="io.github.betaseg",
    name="cellsketch-add-filament-knossos",
    version="0.1.0",
    solution_creators=["Deborah Schmidt"],
    title="CellSketch: Add KNOSSOS filament",
    description="This solution adds a KNOSSOS filament XML file to an existing CellSketch project.",
    tags=["cellsketch", "segmentation", "annotation"],
    cite=[{
        "text": "A. Müller, D. Schmidt, C. S. Xu, S. Pang, J. V. D’Costa, S. Kretschmar, C. Münster, T. Kurth, F. Jug, M. Weigert, H. F. Hess, M. Solimena; 3D FIB-SEM reconstruction of microtubule–organelle interaction in whole primary mouse β cells. J Cell Biol 1 February 2021; 220 (2): e202010039.",
        "doi": "https://doi.org/10.1083/jcb.202010039"
    }],
    album_api_version="0.5.5",
    args=[{
            "name": "project",
            "type": "directory",
            "required": True,
            "description": "The CellSketch project to be opened (.n5)."
        }, {
            "name": "input",
            "type": "file",
            "required": True,
            "description": "The dataset file (3D)"
        }, {
            "name": "type",
            "type": "string",
            "required": True,
            "description": "Type of the dataset. Possible choices: mask, labelmap, knossos"
        }, {
            "name": "name",
            "type": "string",
            "required": True,
            "description": "The name of the dataset"
        }, {
            "name": "scale_x",
            "type": "float",
            "default": 1,
            "description": "Scale factor X for input dataset"
        }, {
            "name": "scale_y",
            "type": "float",
            "default": 1,
            "description": "Scale factor Y of input dataset"
        }, {
            "name": "scale_z",
            "type": "float",
            "default": 1,
            "description": "Scale factor Z of input dataset"
        }, {
            "name": "color",
            "type": "string",
            "default": "255:255:255:255",
            "description": "Color of dataset in red:green:blue:alpha where all values can be 0-255 (i.e. 255:255:0:255)"
        }, {
            "name": "radius",
            "type": "float",
            "description": "Filaments radius in μm"
        }, {
            "name": "thresholdConnectionFilamentEnds",
            "type": "float",
            "required": False,
            "description": "Threshold to count filament ends as connected in um"
        }],
    install=install,
    run=run,
    dependencies={'environment_file': """channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.9
  - openjdk=11.0.9.1
"""}
)

