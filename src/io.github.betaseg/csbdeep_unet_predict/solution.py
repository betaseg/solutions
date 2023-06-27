from album.runner.api import get_args, setup
import sys

env_file = """name:  csbdeep_unet_predict
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
    - csbdeep
    - tqdm
    - git+https://github.com/stardist/augmend.git
    - tensorflow==2.4.*
    - gputools
"""

# catch MACOSX
if sys.platform == "darwin":
    env_file = """name:  csbdeep_unet_predict
channels:
  - conda-forge
  - defaults
  - nvidia
dependencies:
  - python=3.8
  - pip
  - pip:
    - csbdeep
    - tqdm
    - git+https://github.com/stardist/augmend.git
    - tensorflow==2.4.*
    - gputools
"""


def run():
    import numpy as np
    from tifffile import imread, imwrite
    from model import UNet
    from pathlib import Path

    args = get_args()

    def apply(model, x0):
        x = x0.astype(np.float32) / 255.
        n_tiles = tuple(int(np.ceil(s / 196)) for s in x0.shape)
        y_full = model.predict(x, axes="ZYX", normalizer=None, n_tiles=n_tiles)

        y = y_full >= 0.5

        return y

    model = UNet(None, args.model_name, basedir=args.root)

    out = Path(args.outdir)
    out.mkdir(exist_ok=True, parents=True)

    # load file(s)
    input_path = Path(args.fname_input)
    if input_path.is_dir():
        for f in input_path.iterdir():
            if f.suffix == ".tif":
                x0 = imread(f)
                y = apply(model, x0)

                imwrite(out / f"{f.stem}.unet.tif", y.astype(np.uint16))
    else:
        x0 = imread(input_path)
        y = apply(model, x0)

        imwrite(out / f"{input_path.stem}.unet.tif", y.astype(np.uint16))


setup(
    group="io.github.betaseg",
    name="csbdeep_unet_predict",
    version="0.1.0",
    title="CSBDeep Unet Predict",
    description="An album solution to predict your image from a Unet with the csbdeep_unet_train solution.",
    covers=[{
        "description": "CSBDeep Unet Predict Cover Image",
        "source": "cover.jpg"
    }],
    documentation=["README.md"],
    solution_creators=["Martin Weigert", "Jan Philipp Albrecht"],
    tags=["machine learning", "dataset", "CSBDeep", "Unet", "predcit"],
    license="MIT",
    album_api_version="0.5.5",
    cite=[{
        "text": "Weigert, Martin, et al. \"Content-aware image restoration: pushing the limits of fluorescence microscopy.\" Nature methods 15.12 (2018): 1090-1097.",
        "doi": "15.12 (2018): 1090–1097."
    }],
    args=[
        {
            "name": "root",
            "description": "root folder of your models.",
            "type": "string",
            "required": True
        },
        {
            "name": "model_name",
            "description": "Folder name in which the model is stored.",
            "type": "string",
            "required": True
        },
        {
            "name": "fname_input",
            "description": "file path to your input image or folder. Should be tif file(s).",
            "type": "string",
            "required": True
        },
        {
            "name": "outdir",
            "description": "output folder",
            "type": "string",
            "required": True
        },

    ],
    run=run,
    dependencies={"environment_file": env_file},
)
