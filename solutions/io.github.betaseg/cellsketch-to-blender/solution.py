from album.runner.api import setup
path_download_macos = "https://download.blender.org/release/Blender3.3/blender-3.3.1-macos-x64.dmg"
path_download_linux = "https://download.blender.org/release/Blender3.3/blender-3.3.1-linux-x64.tar.xz"
path_download_windows = "https://download.blender.org/release/Blender3.3/blender-3.3.1-windows-x64.zip"
download_name_linux = "blender-3.3.1-linux-x64.tar.xz"
download_name_windows = "blender-3.3.1-windows-x64.zip"
download_name_macos = "blender-3.3.1-macos-x64.dmg"
path_run_linux = "blender-3.3.1-linux-x64/blender"
path_run_windows = "blender-3.3.1-windows-x64\\blender.exe"
path_run_macos = "Contents/MacOS/Blender"


def install():
    from album.runner.api import get_cache_path
    import sys
    get_cache_path().mkdir(exist_ok=True, parents=True)
    operation_system = sys.platform
    if operation_system == "linux":
        __install_linux()
    elif operation_system == "darwin":
        __install_macos()
    else:
        __install_windows()
    # list_files(str(get_app_path()))


def __install_linux():
    from album.runner.api import get_cache_path, extract_tar, get_app_path
    download_target = get_cache_path().joinpath(download_name_linux)
    download(path_download_linux, download_target)
    extract_tar(download_target, get_app_path())


def __install_macos():
    import dmglib
    from distutils.dir_util import copy_tree
    import os
    from album.runner.api import get_cache_path, get_app_path
    get_app_path().mkdir(exist_ok=True, parents=True)
    download_target = get_cache_path().joinpath(download_name_macos)
    download(path_download_macos, download_target)
    dmg = dmglib.DiskImage(download_target)

    if dmg.has_license_agreement():
        print('Cannot attach disk image.')
        return

    for mount_point in dmg.attach():
        for entry in os.listdir(mount_point):
            print('{} -- {}'.format(mount_point, entry))
        copy_tree(mount_point + os.sep + 'Blender.app', str(get_app_path()))

    dmg.detach()


def __install_windows():
    from album.runner.api import get_cache_path, get_app_path
    download_target = get_cache_path().joinpath(download_name_windows)
    download(path_download_windows, download_target)
    extract_zip(download_target, get_app_path())


def extract_zip(in_zip, out_dir):
    from pathlib import Path
    import zipfile
    from album.runner.album_logging import get_active_logger
    out_path = Path(out_dir)

    if not out_path.exists():
        out_path.mkdir(parents=True)

    get_active_logger().info(f"Extracting {in_zip} to {out_dir}...")

    with zipfile.ZipFile(in_zip, 'r') as zip_ref:
        zip_ref.extractall(out_dir)


def _get_session():
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3 import Retry
    s = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)

    adapter = HTTPAdapter(max_retries=retry)

    s.mount("http://", adapter)
    s.mount("https://", adapter)

    return s


def _request_get(url):
    """Get a response from a request to a resource url."""
    from album.ci.utils.zenodo_api import ResponseStatus
    with _get_session() as s:
        r = s.get(url, allow_redirects=True, stream=True)

        if r.status_code != ResponseStatus.OK.value:
            raise ConnectionError("Could not connect to resource %s!" % url)

        return r


def download(str_input, output):
    with _get_session() as s:
        r = s.get(str_input, allow_redirects=True, stream=True)
        with open(output, "wb") as out:
            out.write(r.content)


def _get_blender_executable():

    import sys
    operation_system = sys.platform
    if operation_system == "linux":
        return path_run_linux
    elif operation_system == "darwin":
        return path_run_macos
    else:
        return path_run_windows


def list_files(startpath):
    import os
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        print('{}{}/'.format(indent, os.path.basename(root)))
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print('{}{}'.format(subindent, f))


def run_blender_script(script, *params):
    import subprocess
    from album.runner.api import get_app_path, get_args
    blender_path = str(get_app_path().joinpath(_get_blender_executable()))

    if get_args().headless:
        args = [blender_path, "-b", "-d", "-noaudio", "--debug-gpu-force-workarounds", "-P", script, "--"]
    else:
        args = [blender_path, "-d", "-noaudio", "--debug-gpu-force-workarounds", "-P", script, "--"]
    args.extend(params)
    subprocess.run(args)


def run():
    from pathlib import Path
    from album.runner.api import get_args, get_package_path

    project = Path(get_args().project)
    include = None
    exclude = None
    if get_args().include:
        include = get_args().include
    if get_args().exclude:
        exclude = get_args().exclude
    output_path = project.joinpath("export", "meshes")

    decimate_ratio = get_args().decimate_ratio
    resolution_percentage = get_args().resolution_percentage
    output_rendering = get_args().output_rendering
    output_blend = Path(get_args().output_blend).absolute()
    if output_rendering:
        Path(output_rendering).parent.mkdir(exist_ok=True, parents=True)
    Path(output_blend).parent.mkdir(exist_ok=True, parents=True)
    run_blender_script(str(Path(get_package_path()).joinpath("blender_script.py").absolute()), str(decimate_ratio),
                       str(resolution_percentage), str(output_path), str(output_blend), str(output_rendering), str(include), str(exclude))


setup(
    group="io.github.betaseg",
    name="cellsketch-to-blender",
    version="0.1.0",
    album_api_version="0.5.3",
    solution_creators=['Deborah Schmidt'],
    cite=[{
        "text": "Blender Online Community: Blender - a 3D modelling and rendering package (2018). Stichting Blender Foundation, Amsterdam.",
        "url": "http://www.blender.org"
    }],
    title="CellSketch: Generate Blender scene from mesh files",
    description="This solution imports STL files from a CellSketch project into the same scene, optionally reducing their mesh complexity and rendering the scene.",
    covers=[{
        "description": "This rendering was generated based on data from the following publication: Andreas Müller, Deborah Schmidt, C. Shan Xu, Song Pang, Joyson Verner D’Costa, Susanne Kretschmar, Carla Münster, Thomas Kurth, Florian Jug, Martin Weigert, Harald F. Hess, Michele Solimena; 3D FIB-SEM reconstruction of microtubule–organelle interaction in whole primary mouse β cells. J Cell Biol 1 February 2021; 220 (2): e202010039. doi: https://doi.org/10.1083/jcb.202010039",
        "source": "cover.png"
    }],
    run=run,
    install=install,
    args=[{
        "name": "project",
        "type": "directory",
        "description": "The CellSketch project (ends with .n5)",
        "required": True
    }, {
        "name": "output_rendering",
        "type": "file",
        "required": False,
        "description": "Path for storing the rendering (file name should end with .png or .jpg)",
    }, {
        "name": "output_blend",
        "type": "file",
        "description": "Path for storing the Blender project for rendering (file name should end with .blend)",
        "required": True
    }, {
        "name": "resolution_percentage",
        "default": 100,
        "type": "integer",
        "description": "Resolution of rendering (integer value from 1 - 100)"
    }, {
        "name": "decimate_ratio",
        "default": 1.0,
        "type": "float",
        "description": "Decimation ratio of the mesh (float, 0-1)"
    }, {
        "name": "headless",
        "default": False,
        "type": "boolean",
        "description": "Run Blender in the background or open the window (default)."
    }, {
        "name": "include",
        "type": "string",
        "description": "List of names of elements which should be loaded, comma separated",
        "required": False
    }, {
        "name": "exclude",
        "type": "string",
        "description": "List of names of elements which should not be loaded, comma separated",
        "required": False
    }],
    dependencies={'environment_file': """channels:
  - defaults
dependencies:
  - python=3.9
  - pip
  - requests
  - pip:
    - dmglib
"""}
)
