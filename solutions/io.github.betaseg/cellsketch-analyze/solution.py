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

    # compile app
    subprocess.run([(get_gradle_executable()), 'build', '-Dorg.gradle.internal.http.socketTimeout=300000'],
                   cwd=get_app_path(), check=True)


def get_gradle_executable():
    from sys import platform
    from album.runner.api import get_app_path
    if platform == "win32":
        return get_app_path().joinpath('gradlew.bat')
    return get_app_path().joinpath('gradlew')


def run():
    import subprocess
    from pathlib import Path
    from album.runner.api import get_args, get_app_path, get_active_solution
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
                    params += "--%s %s " % (arg_name, arg_val)
    # run app via gradle
    subprocess.run([get_gradle_executable(), 'run', '-q', '--args="%s"' % params], cwd=get_app_path())


def is_file_arg(arg_name):
    from album.runner.api import get_active_solution
    solution_args = get_active_solution().setup()['args']
    for arg in solution_args:
        if arg['name'] == arg_name:
            return arg['type'] == 'file' or arg['type'] == 'directory'
    return False


setup(
    group="io.github.betaseg",
    name="cellsketch-analyze",
    version="0.1.0",
    solution_creators=["Deborah Schmidt"],
    title="CellSketch: Run spatial analysis",
    description="This solution performs spatial analysis for all organelles in a CellSketch project.",
    tags=["bdv", "cellsketch", "segmentation", "annotation", "analysis"],
    cite=[{
        "text": "A. Müller, D. Schmidt, C. S. Xu, S. Pang, J. V. D’Costa, S. Kretschmar, C. Münster, T. Kurth, F. Jug, M. Weigert, H. F. Hess, M. Solimena; 3D FIB-SEM reconstruction of microtubule–organelle interaction in whole primary mouse β cells. J Cell Biol 1 February 2021; 220 (2): e202010039.",
        "doi": "https://doi.org/10.1083/jcb.202010039"
    }, {
        "text": "Pietzsch, T., Saalfeld, S., Preibisch, S., & Tomancak, P. (2015). BigDataViewer: visualization and processing for large image data sets. Nature Methods, 12(6), 481–483.",
        "doi": "10.1038/nmeth.3392"
    }],
    album_api_version="0.5.5",
    args=[{
            "name": "project",
            "type": "directory",
            "required": True,
            "description": "The CellSketch project to be opened (.n5)."
        }, {
            "name": "connected_threshold_in_um",
            "type": "float",
            "required": True,
            "description": "Max distance between two connected organelles in μm."
        }, {
            "name": "skip_existing_distance_maps",
            "type": "boolean",
            "default": False,
            "description": "Do not recalculate existing distance transform maps."
        }],
    covers=[{
        "description": "TODO",
        "source": "cover.png"
    }],
    install=install,
    run=run,
    dependencies={'parent': {'resolve_solution': 'io.github.betaseg:cellsketch-create:0.1.0'}}
)

