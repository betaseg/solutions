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
    from csbdeep.utils import normalize_mi_ma 
    from model import UNet
    from pathlib import Path

    args = get_args()
    
    try:
        norm_mi_ma = tuple(float(x) for x in args.normalize_mi_ma.split(","))
    except: 
        print('No normalization values given, using default percentile normalizion (ensure that this is the same as during training!)')
        norm_mi_ma = None 
    
    try:
        n_tiles = tuple(int(n) for n in args.n_tiles.split(","))
    except: 
        n_tiles = None 


    def apply(model, x, norm_mi_ma):
        if norm_mi_ma is None: 
            mi, ma = np.percentile(x[::4,::4,::4], (1, 99.8))
        else: 
            mi, ma = norm_mi_ma
        print(f'normalizing with mi,ma = {mi}, {ma}')
        x = normalize_mi_ma(x, mi, ma, dtype=np.float32)
    
        if n_tiles is None:    
            _n_tiles = tuple(int(np.ceil(s / 128)) for s in x0.shape)
            
        print(f'predicting with n_tiles = {_n_tiles}')
        y_full = model.predict(x, axes="ZYX", normalizer=None, n_tiles=_n_tiles)

        y = y_full >= 0.5

        return y

    model = UNet(None, '.', basedir=args.model)

    out = Path(args.outdir)
    out.mkdir(exist_ok=True, parents=True)

    # load file(s)
    input_path = Path(args.input)
    if input_path.is_dir():
        fnames = sorted(input_path.glob("*.tif"))
    else: 
        fnames = [input_path]
        
    for f in fnames:
        x0 = imread(f)
        y = apply(model, x0, norm_mi_ma)
        imwrite(out / f"{f.stem}.unet.tif", y.astype(np.uint16))


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
            "name": "model",
            "description": "Folder name in which the model is stored.",
            "type": "string",
            "required": True
        },
        {
            "name": "normalize_mi_ma",
            "description": "min and max to use for normalization, if not given use 1st and 99.8th percentile of each image",
            "default": "",
            "type": "string",
            "required": False
        },
        
        {
            "name": "input",
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
        {
            "name": "n_tiles",
            "description": "number of tiles per dimension to use for prediction (will be estimated by default)",
            "type": "string",
            "default": "",
            "required": False
        },

    ],
    run=run,
    dependencies={"environment_file": env_file},
)
