from album.runner.api import get_args, setup, get_environment_path
import sys

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

# catch MACOSX
if sys.platform == "darwin":
    env_file = """name:  stardist_train
channels:
  - conda-forge
  - defaults
  - nvidia
dependencies:
  - python=3.8
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

    def predict_tif(f, model, outdir, x0):
        # compute n_tiles
        n_tiles = tuple(int(np.ceil(s / 160)) for s in x0.shape)
        print(f"using {n_tiles} tiles")

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
        imsave(out / f"{Path(f).stem}.stardist.tif", y)
        np.savez(out / f"{Path(f).stem}.stardist.npz", **polys)

    # parse arguments
    args = get_args()

    # options
    model_name = args.model_name
    outdir = args.output_dir
    basedir = args.model_basedir

    # load model and apply it to the stack
    model = StarDist3D(None, name=model_name, basedir=basedir)

    # load files
    input_path = Path(args.fname_input)
    if input_path.is_dir():
        for f in input_path.iterdir():
            if f.suffix == ".tif":
                x0 = imread(f)
                predict_tif(f, model, outdir, x0)
    else:
        x0 = imread(input_path)
        predict_tif(input_path, model, outdir, x0)


setup(
    group="io.github.betaseg",
    name="stardist_predict",
    version="0.1.0",
    title="StarDist Predict",
    description="An album solution to run stardist to predict 3D segmentation masks.",
    solution_creators=["Martin Weigert", "Jan Philipp Albrecht"],
    cite=[{
        "text": "Uwe Schmidt and Martin Weigert and Coleman Broaddus and Gene Myers, Cell Detection with Star-Convex Polygons, International Conference on Medical Image Computing and Computer-Assisted Intervention (MICCAI), Granada, Spain, September 2018",
        "doi": "10.1007/978-3-030-00934-2_30"
    }, {
        "text": "Martin Weigert and Uwe Schmidt and Robert Haase and Ko Sugawara and Gene Myers, Star-convex Polyhedra for 3D Object Detection and Segmentation in Microscopy, IEEE Winter Conference on Applications of Computer Vision (WACV), March 2020",
        "doi": "10.1109/WACV45572.2020.9093435"
    }],
    tags=["StarDist", "machine learning"],
    license="MIT",
    album_api_version="0.5.5",
    covers=[{
        "description": "StarDist Predict Cover Image",
        "source": "cover.jpg"
    }],
    documentation=["README.md"],
    args=[
        {
            "name": "fname_input",
            "description": "Path to the input tif file or folder of tif images.",
            "required": True
        },
        {
            "name": "model_name",
            "description": "Path to the input model.",
            "required": True
        },
        {
            "name": "model_basedir",
            "description": "Path to the model directory.",
            "required": True
        },
        {
            "name": "output_dir",
            "description": "Path to the output directory.",
            "required": True
        },
        {
            "name": "n_tiles",
            "type": "string",
            "default": "None",
            "description": "Number of tiles per dimension.",
            "required": False
        }
    ],
    run=run,
    dependencies={"environment_file": env_file},
)
