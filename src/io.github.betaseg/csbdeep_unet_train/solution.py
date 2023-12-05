from album.runner.api import get_args, setup
import sys

env_file = """name:  csbdeep_unet_train
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
    env_file = """name:  csbdeep_unet_train
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


def get_data(root, subset, norm_mi_ma, nfiles=None, inds=None, shuffle=True):
    import numpy as np
    from tifffile import imread
    from csbdeep.utils import Path, normalize_mi_ma
    from tqdm import tqdm

    src = root / subset
    fx = sorted((src / "images").glob("*.tif"))
    fy = sorted((src / "masks").glob("*.tif"))
    assert len(fx) == len(fy)

    for f1, f2 in zip(fx, fy):
        print(f"{Path(f1).name}")
        print(f"{Path(f2).name}")

    if shuffle:
        np.random.seed(42)
        inds0 = np.arange(len(fx))
        np.random.shuffle(inds0)
        fx = np.array(fx)[inds0]
        fy = np.array(fy)[inds0]

    if inds is not None:
        fx = np.array(fx)[inds]
        fy = np.array(fy)[inds]
    else:
        fx = fx[:nfiles]
        fy = fy[:nfiles]

    def crop(x):
        return x[tuple(slice(0, (s // 8) * 8) for s in x.shape)]

    def _norm(x):
        if norm_mi_ma is None: 
            mi, ma = np.percentile(x[::4,::4,::4], (1, 99.8))
        else: 
            mi, ma = norm_mi_ma
        print(f'normalizing with mi,ma = {mi}, {ma}')
        return normalize_mi_ma(x, mi, ma, dtype=np.float32)
    
    X = tuple(_norm(crop(imread(str(f)))) for f in tqdm(fx))

    Y = tuple((crop(imread(str(f)).astype(np.uint8))>0).astype(np.float32) for f in tqdm(fy))

    X = tuple(np.expand_dims(x,-1) for x in X)
    Y = tuple(np.expand_dims(x,-1) for x in Y)
    
    return X, Y


def run():
    args = get_args()

    import numpy as np
    import time
    import webbrowser
    import os
    from datetime import datetime
    from csbdeep.utils import Path
    from csbdeep.utils.tf import limit_gpu_memory
    limit_gpu_memory(fraction=0.8, total_memory=args.limit_gpu_memory)
    from augmend import Augmend, Elastic, Identity, FlipRot90, AdditiveNoise, IntensityScaleShift, IsotropicScale
    from model import UNetConfig, UNet
    from subprocess import Popen
    np.random.seed(42)

    # process args:
    root = Path(args.root)
    unet_pool_size = tuple(int(x) for x in args.unet_pool_size.split(","))
    train_class_weight = tuple(float(x) for x in args.train_class_weight.split(","))
    patch_size = tuple(int(x) for x in args.patch_size.split(","))
    num_workers = 0 if os.name == 'nt' else args.num_workers

    try:
        norm_mi_ma = tuple(float(x) for x in args.normalize_mi_ma.split(","))
    except: 
        print('No normalization values given, using default percentile normalizion...')
        norm_mi_ma = None 
        
    X, Y = get_data(root, "train", norm_mi_ma)
    Xv, Yv = get_data(root, "val", norm_mi_ma)


    if len(X)==0:
        raise ValueError(f"No data found in {root}/train")
    else: 
        print(f"Found {len(X)} training images")
        
    if len(Xv)==0:
        raise ValueError(f"No data found in {root}/val")
    else: 
        print(f"Found {len(Xv)} validation images")
        
    if args.use_augmentation:
        aug = Augmend()
        aug.add([FlipRot90(axis=(-2, -3)), FlipRot90(axis=(-2, -3))])
        aug.add(
            [
                Elastic(grid=5, amount=5, order=0, use_gpu=args.use_gpu_for_aug, axis=(-2, -3)),
                Elastic(grid=5, amount=5, order=0, use_gpu=args.use_gpu_for_aug, axis=(-2, -3))
            ], probability=.5)
        # aug.add([IsotropicScale(amount=(.8, 1.2), axis=(0,1,2)[:n_dim], order=1, use_gpu=args.use_gpu_for_aug), 
        #          IsotropicScale(amount=(.8, 1.2), axis=(0,1,2)[:n_dim], order=1, use_gpu=args.use_gpu_for_aug)], probability=.3)
        aug.add([AdditiveNoise(sigma=(0, 0.05)), Identity()], probability=.3)
        aug.add([IntensityScaleShift(scale=(.7, 1.2), shift=(-0.1, 0.1)), Identity()])
    else:
        aug = Identity()

    
    conf = UNetConfig(
        n_dim=3,
        n_channel_in=1,
        n_channel_out=1,
        unet_n_depth=args.unet_n_depth,
        unet_pool_size=unet_pool_size,
        patch_size=patch_size,
        train_loss='dice_bce',
        train_batch_size=args.batch_size,
        train_reduce_lr={
            'factor': args.train_reduce_lr_factor,
            'patience': args.train_reduce_lr_patience,
            'min_delta': 0
        },
        train_class_weight=train_class_weight
    )
    
    print('\n--- Args ---\n')
    print(args)
    print('\n--- UNetConfig ---\n')
    print(conf) 
    print('\n--- Augmentation ---\n')
    print(aug)
    
    
    timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
    name = f"{timestamp}_unet" if not args.dry else None
    model = UNet(conf, name=name, basedir="models")

    if not args.dry:
        p = Popen(["tensorboard",  "--logdir", "./models", "--reload_interval", "60"])
        time.sleep(5)
        webbrowser.open("http://localhost:6006", new=1)

    if args.epochs>0:
        model.train(X,Y,Xv,Yv,augmenter=aug, epochs=args.epochs,steps_per_epoch=args.steps_per_epoch, num_workers=num_workers)


setup(
    group="io.github.betaseg",
    name="csbdeep_unet_train",
    version="0.1.0",
    title="CSBDeep Unet Train",
    description="An album solution to train a Unet with CSBDeep.",
    covers=[{
        "description": "CSBDeep Unet Train Cover Image",
        "source": "cover.jpg"
    }],
    solution_creators=["Martin Weigert", "Jan Philipp Albrecht"],
    tags=["machine learning", "dataset", "CSBDeep", "Unet", "training"],
    license="MIT",
    album_api_version="0.5.5",
    cite=[{
        "text": "Weigert, Martin, et al. \"Content-aware image restoration: pushing the limits of fluorescence microscopy.\" Nature methods 15.12 (2018): 1090-1097.",
        "doi": "15.12 (2018): 1090-1097."
    }],
    documentation=["README.md"],
    args=[
        {
            "name": "root",
            "description": "root folder of your data. Data structure must be provided as specified in documentation!",
            "type": "string",
            "required": True
        },
        {
            "name": "use_augmentation",
            "description": "Whether to use augmentation or not. If enabled the data is probabilistically flipped, "
                           "rotated, elastic deformed, intensity scaled and additionally noised.",
            "default": True,
            "type": "boolean",
            "required": False
        },
        {
            "name": "limit_gpu_memory",
            "description": "The absolute number of bytes to allocate for GPU memory.",
            "default": 12000,
            "type": "integer",
            "required": False
        },
        {
            "name": "patch_size",
            "description": "Patch size of each training instance.  Must be given as a string separated by \",\".",
            "default": "48,128,128",
            "type": "string",
            "required": False
        },
        {
            "name": "unet_n_depth",
            "description": "The depth of the network. Default: 3",
            "default": 4,
            "type": "integer",
            "required": False
        },
        {
            "name": "batch_size",
            "description": "batch size to be used during training",
            "default": "2",
            "type": "integer",
            "required": False
        },
        {
            "name": "normalize_mi_ma",
            "description": "min and max to use for normalization, if not given use 1st and 99.8th percentile of each image",
            "default": "",
            "type": "string",
            "required": False
        },
        {
            "name": "unet_pool_size",
            "description": "The pool size of the network. Must be given as a string separated by \",\". Should be as many numbers as unet is deep.",
            "default": "2,2,2",
            "type": "string",
            "required": False
        },
        {
            "name": "train_class_weight",
            "description": "The weights for the binary cross entropy loss part. First weight for negative class. Must be given as a string separated by \",\".",
            "default": "1,1",
            "type": "string",
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
            "default": 512,
            "type": "integer",
            "required": False
        },
        {
            "name": "train_reduce_lr_factor",
            "description": "Factor to reduce learn rate over time.",
            "default": 0.5,
            "type": "float",
            "required": False
        },
        {
            "name": "train_reduce_lr_patience",
            "description": "Patience after which to start learn rate reduction.",
            "default": 50,
            "type": "integer",
            "required": False
        },
        {
            "name": "use_gpu_for_aug",
            "type": "boolean",
            "description": "Whether to use gpu for augmentations. Only enable if you have a GPU available that is compatible with"
                           " tensorflow 2.0.",
            "default": True,
            "required": False
        },
        {
            "name": "dry",
            "type": "boolean",
            "description": "dry run (dont create any output files/folders)",
            "default": False,
            "required": False
        },
        {
            "name": "num_workers",
            "type": "integer",
            "description": "Number of threads to use for training. On Windows, multiprocessing will be deactivated. Default: 4",
            "default": 4,
            "required": False
        }
    ],
    run=run,
    dependencies={"environment_file": env_file},
)
