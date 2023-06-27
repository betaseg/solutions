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
    args = get_args()

    from csbdeep.utils.tf import limit_gpu_memory
    limit_gpu_memory(fraction=0.8, total_memory=args.total_memory)
    from csbdeep.utils import Path, normalize
    from tifffile import imread
    from tqdm import tqdm
    from glob import glob
    from datetime import datetime
    import numpy as np
    from stardist import fill_label_holes, calculate_extents
    from stardist.models import Config3D, StarDist3D
    from augmend import Augmend, FlipRot90, Elastic, Identity, \
        IntensityScaleShift, AdditiveNoise

    # options:
    basedir = Path(args.out)
    basedir.mkdir(exist_ok=True, parents=True)
    timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
    name = f'{timestamp}_stardist'

    def get_data(root, subfolder="train", n=None, normalize_img=True):
        """ load data from """
        src = Path(root).joinpath(subfolder)
        fx = sorted(tuple((src / "images").glob("*.tif")))[:n]
        fy = sorted(tuple((src / "masks").glob("*.tif")))[:n]

        X = tuple(imread(str(f)) for f in tqdm(fx))
        Y = tuple(fill_label_holes(imread(str(f))) for f in tqdm(fy))

        if any(_X.dtype == np.intc or _X.dtype == np.uintc for _X in X):
            X = tuple(_X.astype(np.uint32) for _X in X)
        Y = tuple(_Y.astype(np.uint8) for _Y in Y)

        if normalize_img:
            X = tuple(_X.astype(np.float32) / 255 for _X in X)

        return X, Y

    def simple_augmenter(x, y):
        return aug([x, y])

    X, Y = get_data(args.root, "train")

    extents = calculate_extents(Y)
    anisotropy = tuple(np.max(extents) / extents)

    grid = [int(x) for x in args.grid.split(",")]
    train_patch_size = [int(x) for x in args.train_patch_size.split(",")]
    train_loss_weights = [float(x) for x in args.train_loss_weights.split(",")]

    print(f"empirical anisotropy of labeled objects = {anisotropy}")
    print(f"using grid = {grid}")

    # create train configuration
    conf = Config3D(
        rays=args.rays,
        grid=grid,
        anisotropy=anisotropy,
        use_gpu=args.use_gpu,
        n_channel_in=args.n_channel_in,
        backbone=args.backbone,
        unet_n_depth=args.unet_n_depth,
        train_patch_size=train_patch_size,
        train_batch_size=args.train_batch_size,
        train_loss_weights=train_loss_weights,
        train_steps_per_epoch=args.train_steps_per_epoch,
    )
    print(conf)
    vars(conf)

    # Augmentation pipeline
    aug = Augmend()
    if args.use_augmentation:
        aug.add([FlipRot90(axis=(0, 1, 2)), FlipRot90(axis=(0, 1, 2))])
        aug.add([
            Elastic(axis=(0, 1, 2), amount=5, grid=6, order=0, use_gpu=args.use_gpu),
            Elastic(axis=(0, 1, 2), amount=5, grid=6, order=0, use_gpu=args.use_gpu)
        ], probability=.7
        )
        aug.add([AdditiveNoise(sigma=0.05), Identity()], probability=.5)
        aug.add([IntensityScaleShift(scale=(.8, 1.2), shift=(-.1, .1)), Identity()], probability=.5)

    # create the Stardist Model and train
    model = StarDist3D(conf, name=name, basedir=str(basedir))
    model.train(
        X,
        Y,
        validation_data=(X, Y),
        augmenter=simple_augmenter,
        epochs=args.epochs
    )

    model.optimize_thresholds(X, Y, nms_threshs=[0.1, 0.2, 0.3])


setup(
    group="io.github.betaseg",
    name="stardist_train",
    version="0.1.0",
    title="StarDist Train",
    description="An album solution to train a stardist model",
    solution_creators=["Martin Weigert", "Jan Philipp Albrecht", "Lucas Rieckert"],
    documentation=["README.md"],
    cite=[{
        "text": "Uwe Schmidt and Martin Weigert and Coleman Broaddus and Gene Myers, Cell Detection with Star-Convex Polygons, International Conference on Medical Image Computing and Computer-Assisted Intervention (MICCAI), Granada, Spain, September 2018",
        "doi": "10.1007/978-3-030-00934-2_30"
    }, {
        "text": "Martin Weigert and Uwe Schmidt and Robert Haase and Ko Sugawara and Gene Myers, Star-convex Polyhedra for 3D Object Detection and Segmentation in Microscopy, IEEE Winter Conference on Applications of Computer Vision (WACV), March 2020",
        "doi": "10.1109/WACV45572.2020.9093435"
    }],
    covers=[{
        "description": "StarDist Train Cover Image",
        "source": "cover.jpg"
    }],
    tags=["StarDist", "machine learning"],
    license="MIT",
    album_api_version="0.5.5",
    args=[
        {
            "name": "root",
            "description": "Root folder of your data. Data structure must be provided as specified in documentation!",
            "type": "string",
            "required": True
        },
        {
            "name": "out",
            "type": "string",
            "description": "output folder",
            "required": True
        },
        {
            "name": "total_memory",
            "type": "integer",
            "description": "Total memory of the gpu to use at max.",
            "default": 12000,
            "required": False
        },
        {
            "name": "epochs",
            "description": "Number of epochs to train for.",
            "default": 300,
            "type": "integer",
            "required": False
        },
        {
            "name": "steps_per_epoch",
            "description": "Number of steps per epochs.",
            "default": 100,
            "type": "integer",
            "required": False
        },
        {
            "name": "grid",
            "type": "string",
            "description": "Grid of the model. Must be given as a string separated by \",\".",
            "default": "2,2,2",
            "required": False
        },
        {
            "name": "rays",
            "type": "integer",
            "description": "Rays of the model.",
            "default": 96,
            "required": False
        },
        {
            "name": "use_gpu",
            "type": "boolean",
            "description": "Whether to use gpu or not. Only enable if you have a GPU available that is compatible with"
                           " tensorflow 2.0.",
            "default": True,
            "required": False
        },
        {
            "name": "n_channel_in",
            "type": "integer",
            "description": "Number of input channels",
            "default": 1,
            "required": False
        },
        {
            "name": "backbone",
            "type": "string",
            "description": "Backbone of the model. See https://github.com/stardist/stardist for more details.",
            "default": "unet",
            "required": False
        },
        {
            "name": "unet_n_depth",
            "type": "integer",
            "description": "Depth of the unet.",
            "default": 3,
            "required": False
        },
        {
            "name": "train_patch_size",
            "type": "string",
            "description": "Patch size of the training. Each of the 3 dimensions given as string, separated by comma.",
            "default": "160,160,160",
            "required": False
        },
        {
            "name": "train_batch_size",
            "type": "integer",
            "description": "Batch size of the training.",
            "default": 1,
            "required": False
        },
        {
            "name": "train_loss_weights",
            "type": "string",
            "description": "Weights for losses relating to (probability, distance)."
                           " Given as string, separated by comma.",
            "default": "1,0.1",
            "required": False
        },
        {
            "name": "use_augmentation",
            "description": "Whether to use augmentation or not. If enabled the data is probabilistically flipped, "
                           "rotated, elastic deformed, intensity scaled and additionally noised.",
            "type": "boolean",
            "default": True,
            "required": False
        },
    ],
    run=run,
    dependencies={"environment_file": env_file},
)
