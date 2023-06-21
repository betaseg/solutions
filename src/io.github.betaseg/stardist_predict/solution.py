from album.runner.api import get_args, setup, get_environment_path

env_file = """name:  stardist_train
channels:
  - conda-forge
  - defaults
  - nvidia
dependencies:
  - python=3.8
  - cudatoolkit=11.0.3 
  - cudnn=8.0.*
  - pip
  - pip:
    - stardist
    - git+https://github.com/stardist/augmend.git
    - tensorflow==2.4.*
    - gputools
"""


def run():
    from csbdeep.utils.tf import limit_gpu_memory
    limit_gpu_memory(fraction=0.8, total_memory=12000)
    from csbdeep.utils import Path
    from tifffile import imread, imsave
    import numpy as np
    from stardist.models import StarDist3D

    # parse arguments
    args = get_args()

    # options
    fname = args.fname_input
    model_name = args.model_name
    outdir = args.output_dir
    basedir = args.model_basedir

    # load file
    x0 = imread(fname)

    # compute n_tiles
    n_tiles = tuple(int(np.ceil(s / 160)) for s in x0.shape)
    print(f"using {n_tiles} tiles")

    # load model and apply it to the stack
    model = StarDist3D(None, name=model_name, basedir=basedir)

    # normalize
    print("normalizing...")
    x = x0.astype(np.float32) / 255

    # predict
    y, polys = model.predict_instances(x, n_tiles=n_tiles)
    rays = polys["rays"]
    polys["rays_vertices"] = rays.vertices
    polys["rays_faces"] = rays.faces

    # save output
    out = Path(outdir)
    out.mkdir(exist_ok=True, parents=True)
    imsave(out / f"{Path(fname).stem}.stardist.tif", y)
    np.savez(out / f"{Path(fname).stem}.stardist.npz", **polys)


setup(
    group="io.github.betaseg",
    name="stardist_predict",
    version="0.1.0",
    title="stardist_predict",
    description="An album solution to run stardist to predict 3D segmentation masks.",
    solution_creators=["Jan Philipp Albrecht"],
    cite=[],
    tags=["stardist_train", "machine learning"],
    license="unlicense",
    album_api_version="0.5.5",
    args=[
        {
            "name": "fname_input",
            "description": "Input file",
            "required": True
        },
        {
            "name": "model_name",
            "description": "Input model",
            "required": True
        },
        {
            "name": "model_basedir",
            "description": "Path to the model directory",
            "required": True
        },
        {
            "name": "output_dir",
            "description": "Path to the output directory",
            "required": True
        },
        {
            "name": "n_tiles",
            "type": "string",
            "default": "None",
            "description": "Number of tiles per dimension. ",
            "required": False
        }
    ],
    run=run,
    dependencies={"environment_file": env_file},
)
