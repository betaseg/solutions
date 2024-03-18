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
    import os
    from album.runner.api import get_app_path
    if platform == "win32":
        return str(get_app_path().joinpath('gradlew.bat').absolute())
    gradle_executable = str(get_app_path().joinpath('gradlew').absolute())
    os.chmod(gradle_executable, 0o755)
    return gradle_executable


def run():
    import subprocess
    from pathlib import Path
    from album.runner.api import get_args, get_app_path

    project = Path(get_args().project)
    skip_existing_distance_maps = get_args().skip_existing_distance_maps
    num_threads = get_args().num_threads

    calculate_edt(project, skip_existing_distance_maps, num_threads)

    # parsing album arguments to gradle arguments. this should become a utility method.
    # setting skip_existing_distance_maps by default because this solution is calculating the EDTs in Python and
    # therefore they don't have to be recalculated in Java
    params = "--skip_existing_distance_maps "
    args = get_args()
    for arg_name in args.__dict__:
        arg_val = args.__dict__[arg_name]
        if arg_val is not None:
            if arg_name == "skip_existing_distance_maps" or arg_name == "num_threads":
                continue
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


def calculate_edt(project, skip_existing_distance_maps, num_threads):
    import edt
    import z5py
    from pathlib import Path
    import numpy as np
    import shutil
    import os

    project_file = z5py.File(str(project))
    project_name = Path(project).name.rstrip(".n5")
    masks = {}
    labelmaps = {}
    filaments = {}
    cell_bounds = {}
    if 'labelmaps' in project_file.attrs:
        labelmaps = project_file.attrs['labelmaps']
    if 'masks' in project_file.attrs:
        masks = project_file.attrs['masks']
    if 'filaments' in project_file.attrs:
        filaments = project_file.attrs['filaments']
    if 'cell_bounds' in project_file.attrs:
        cell_bounds = project_file.attrs['cellbounds']
    to_be_processed = []
    to_be_processed_inverted = []

    for mask in masks:
        to_be_processed.append(masks[mask])
    for labelmap in labelmaps:
        to_be_processed.append(labelmaps[labelmap])
    for filament in filaments:
        to_be_processed.append(filaments[filament])
    for cell_bound in cell_bounds:
        to_be_processed_inverted.append(cell_bounds[cell_bound])

    analysis_group_name = 'analysis'
    # Check if group exists
    try:
        analysis_group = project_file[analysis_group_name]
    except KeyError:
        # If not, create the group
        analysis_group = project_file.create_group(analysis_group_name)

    for item in to_be_processed:
        edt_result_file = item.lstrip(os.sep) + "_distance_map"
        # Check if the dataset exists
        if edt_result_file in analysis_group:
            if skip_existing_distance_maps:
                continue
            dataset_path = os.path.join(project, analysis_group_name, edt_result_file)

            # Delete the dataset folder
            shutil.rmtree(dataset_path)

        mask = load_as_mask(project_file, item)
        dt = edt.edt(
            np.ascontiguousarray(mask),
            parallel=num_threads  # number of threads, <= 0 sets to num cpu
        )

        analysis_group.create_dataset(edt_result_file, data=dt, chunks=(64, 64, 64), dtype='float32')

    for item in to_be_processed_inverted:
        edt_result_file = item.lstrip(os.sep) + "_distance_map"
        # Check if the dataset exists
        if edt_result_file in analysis_group:
            if skip_existing_distance_maps:
                continue
            dataset_path = os.path.join(project, analysis_group_name, edt_result_file)

            # Delete the dataset folder
            shutil.rmtree(dataset_path)

        mask = load_as_mask(project_file, item, background_is_data=False)
        dt = edt.edt(
            np.ascontiguousarray(mask),
            parallel=num_threads  # number of threads, <= 0 sets to num cpu
        )

        analysis_group.create_dataset(edt_result_file, data=dt, chunks=(64, 64, 64), dtype='float32')


def load_as_mask(project, item, background_is_data=True):
    import numpy as np
    import os
    item = item.lstrip(os.sep)
    print("Loading dataset from %s.." % item)
    project_item = project[item]
    data = np.array(project_item)
    # the edt used here calculates the distance of label pixels to the background - we need the opposite
    if background_is_data:
        data = data == 0
    else:
        data = data != 0
    return data


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
    version="0.2.2",
    solution_creators=["Deborah Schmidt"],
    title="CellSketch: Run spatial analysis",
    description="This solution performs spatial analysis for all organelles in a CellSketch project.",
    tags=["bdv", "cellsketch", "segmentation", "annotation", "analysis"],
    cite=[{
        "text": "A. Müller, D. Schmidt, C. S. Xu, S. Pang, J. V. D'Costa, S. Kretschmar, C. Münster, T. Kurth, F. Jug, M. Weigert, H. F. Hess, M. Solimena; 3D FIB-SEM reconstruction of microtubule-organelle interaction in whole primary mouse β cells. J Cell Biol 1 February 2021; 220 (2): e202010039.",
        "doi": "https://doi.org/10.1083/jcb.202010039"
    }, {
        "text": "Pietzsch, T., Saalfeld, S., Preibisch, S., & Tomancak, P. (2015). BigDataViewer: visualization and processing for large image data sets. Nature Methods, 12(6), 481-483.",
        "doi": "10.1038/nmeth.3392"
    }, {
        "text": "Pape, C. (2019). constantinpape/z5",
        "doi": "10.5281/ZENODO.3585752"
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
        }, {
            "name": "num_threads",
            "type": "integer",
            "default": 4,
            "description": "Threads to use to calculate the distance transform maps."
        }],
    covers=[{
        "description": "TODO",
        "source": "cover.png"
    }],
    install=install,
    run=run,
    dependencies={'environment_file': """channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.9
  - openjdk=11.0.9.1
  - z5py=2.0.16
  - edt=2.3.0
"""}
)

