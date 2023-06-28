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
    from album.runner.api import get_cache_path, get_app_path
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


def run_blender_script(*params):
    import subprocess
    from album.runner.api import get_app_path, get_args
    blender_path = str(get_app_path().joinpath(_get_blender_executable()))
    args = [blender_path, "-d"]
    args.extend(params)
    subprocess.run(args)


def run():
    from pathlib import Path
    from album.runner.api import get_args
    input_blend = get_args().input
    output_rendering = get_args().output_rendering
    args = []
    if input_blend:
        input_blend = str(Path(input_blend).absolute())
        args.append(input_blend)
    if output_rendering:
        args.append('-b')
        args.append('-o')
        args.append(output_rendering)
        args.append('-f')
        args.append('0')
        # args.append('-a')
    run_blender_script(*args)


setup(
    group="io.github.betaseg",
    name="launch-blender",
    version="0.1.0",
    album_api_version="0.5.5",
    solution_creators=['Deborah Schmidt'],
    cite=[{
        "text": "Blender Online Community: Blender - a 3D modelling and rendering package (2018). Stichting Blender Foundation, Amsterdam.",
        "url": "http://www.blender.org"
    }],
    title="Launch Blender 3.3.1",
    description="This solution launches Blender, optionally with a specific .blend file as input.",
    covers=[{
       "description": "",
        "source": "cover.png"
    }],
    install=install,
    run=run,
    args=[{
        "name": "input",
        "type": "file",
        "description": "Path to input .blend file",
        "required": False
    }, {
        "name": "output_rendering",
        "type": "file",
        "required": False,
        "description": "If provided, Blender is launched in headless mode and the first frame is rendered to this path."
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
