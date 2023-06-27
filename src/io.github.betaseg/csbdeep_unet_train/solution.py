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


def batch_generator(X, Y, patch_size, batch_size=4, shuffle=True):
    import numpy as np
    from csbdeep.data.generate import sample_patches_from_multiple_stacks

    if len(X) != len(Y):
        raise ValueError("len(X) != len(Y)")

    if len(X) < batch_size:
        raise ValueError("len(X) < batch_size")

    inds = np.arange(len(X))

    if shuffle:
        np.random.shuffle(inds)

    count = 0
    while True:
        b = tuple(
            sample_patches_from_multiple_stacks([X[i], Y[i]], patch_size=patch_size, n_samples=1) for i in
            inds[:batch_size]
        )
        X_batch, Y_batch = zip(*b)
        X_batch = np.stack(X_batch)[:, 0]
        Y_batch = np.stack(Y_batch)[:, 0]

        yield X_batch, Y_batch

        count += batch_size
        if count + batch_size >= len(X) and shuffle:
            np.random.shuffle(inds)
        inds = np.roll(inds, -batch_size)
        count = count % len(X)


def get_data(root, subset="train", nfiles=None, inds=None, shuffle=True):
    import numpy as np
    from tifffile import imread
    from csbdeep.utils import Path
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

    X = [crop(imread(str(f))).astype(np.float32) / 255. for f in tqdm(fx)]

    Y = [crop(imread(str(f)).astype(np.uint8)) for f in tqdm(fy)]

    return X, Y


def run():
    args = get_args()

    import numpy as np

    from datetime import datetime
    from csbdeep.utils import Path, normalize
    from csbdeep.utils.tf import CARETensorBoard, limit_gpu_memory
    limit_gpu_memory(fraction=0.8, total_memory=args.limit_gpu_memory)
    from augmend import Augmend, BaseTransform, Elastic, Identity, FlipRot90, AdditiveNoise, CutOut, GaussianBlur, \
        IntensityScaleShift
    from model import UNetConfig, UNet
    np.random.seed(42)

    # process args:
    root = Path(args.root)
    unet_pool_size = [int(x) for x in args.unet_pool_size.split(",")]
    train_class_weight = [int(x) for x in args.train_class_weight.split(",")]
    patch_size = [int(x) for x in args.patch_size.split(",")]

    X, Y = get_data(root, "train")
    Xv, Yv = get_data(root, "val")

    if args.use_augmentation:
        aug = Augmend()
        aug.add([FlipRot90(axis=(1, 2)), FlipRot90(axis=(1, 2))])
        aug.add(
            [
                Elastic(grid=5, amount=5, order=0, use_gpu=args.use_gpu, axis=(0, 1, 2)),
                Elastic(grid=5, amount=5, order=0, use_gpu=args.use_gpu, axis=(0, 1, 2))
            ], probability=.8
        )
        aug.add([AdditiveNoise(sigma=(0, 0.05)), Identity()], probability=.5)
        aug.add([IntensityScaleShift(scale=(.7, 1.2), shift=(-0.1, 0.1), axis=(0, 1, 2)), Identity()])
    else:
        aug = Identity()

    def proc_image(x, y, augment=0):
        """create border mask etc"""
        if augment > 0:
            x, y = aug([x, y])
        y = (y > 0).astype(np.float32)[..., np.newaxis]
        x = x[..., np.newaxis]
        return x, y

    def class_generator(gen, augment=0):
        for x, y in gen:
            a, b = tuple(zip(*tuple(proc_image(_x, _y, augment) for _x, _y in zip(x, y))))
            yield np.stack(a), np.stack(b)

    gen = class_generator(batch_generator(X, Y, patch_size=patch_size, batch_size=min(1, len(X))), augment=1)
    gen_val = class_generator(
        batch_generator(Xv, Yv, batch_size=min(3, len(Xv)), patch_size=patch_size, shuffle=False), augment=0
    )
    conf = UNetConfig(
        axes="ZYX",
        unet_n_depth=args.unet_n_depth,
        unet_pool_size=unet_pool_size,
        train_reduce_lr={
            'factor': args.train_reduce_lr_factor,
            'patience': args.train_reduce_lr_patience,
            'min_delta': 0
        },
        train_class_weight=train_class_weight
    )

    timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
    model = UNet(conf, name=f"{timestamp}_unet", basedir="models")

    Xvv, Yvv = next(gen_val)

    # data given via generator object, X,Y stay None
    model.train(
        X=None, Y=None, data_gen=gen, validation_data=[Xvv, Yvv], epochs=args.epochs,
        steps_per_epoch=args.steps_per_epoch
    )


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
        "doi": "15.12 (2018): 1090–1097."
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
            "default": 3,
            "type": "integer",
            "required": False
        },
        {
            "name": "unet_pool_size",
            "description": "The pool size of the network. Must be given as a string separated by \",\". Should be as many numbers as unet is deep.",
            "default": "2,4,4",
            "type": "string",
            "required": False
        },
        {
            "name": "train_class_weight",
            "description": "The weights for the binary cross entropy dice loss. First weight for negative class. Must be given as a string separated by \",\".",
            "default": "1,5",
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
            "name": "use_gpu",
            "type": "boolean",
            "description": "Whether to use gpu or not. Only enable if you have a GPU available that is compatible with"
                           " tensorflow 2.0.",
            "default": True,
            "required": False
        },
    ],
    run=run,
    dependencies={"environment_file": env_file},
)
