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
    from album.runner.api import get_app_path, get_args
    params = ""
    args = get_args()
    for arg_name in args.__dict__:
        arg_val = args.__dict__[arg_name]
        if arg_val is not None:
            if is_file_arg(arg_name):
                params += "--%s '%s' " % (arg_name, str(Path(arg_val).absolute()))
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
    name="cellsketch-pixel-view",
    version="0.1.0",
    solution_creators=["Deborah Schmidt"],
    title="CellSketch: Display data in BigDataViewer",
    description="This solution displays a CellSketch project in BDV.",
    tags=["bdv", "cellsketch", "segmentation", "annotation"],
    cite=[{
        "text": "A. Müller, D. Schmidt, C. S. Xu, S. Pang, J. V. D’Costa, S. Kretschmar, C. Münster, T. Kurth, F. Jug, M. Weigert, H. F. Hess, M. Solimena; 3D FIB-SEM reconstruction of microtubule–organelle interaction in whole primary mouse β cells. J Cell Biol 1 February 2021; 220 (2): e202010039.",
        "doi": "https://doi.org/10.1083/jcb.202010039"
    }, {
        "text": "Pietzsch, T., Saalfeld, S., Preibisch, S., & Tomancak, P. (2015). BigDataViewer: visualization and processing for large image data sets. Nature Methods, 12(6), 481–483.",
        "doi": "10.1038/nmeth.3392"
    }],
    album_api_version="0.5.3",
    args=[{
            "name": "project",
            "type": "directory",
            "required": True,
            "description": "The CellSketch project to be opened (.n5)."
        }],
    covers=[{
        "description": "TODO",
        "source": "cover.png"
    }],
    install=install,
    run=run,
    dependencies={'parent': {'resolve_solution': 'io.github.betaseg:cellsketch-create:0.1.0'}}
)

