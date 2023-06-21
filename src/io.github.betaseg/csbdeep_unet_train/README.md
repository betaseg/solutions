# CSBDeep unet train album solution

This album solution uses the CSBDeep toolbox to train a UNET model from the command line.

## How to run

use `album install` to install the solution.
use `album info` to view the parameters of the solution.
use `album run` to run the solution.

## documentation

The extensive documentation of CSBDeep can be found at http://csbdeep.bioimagecomputing.com/doc/.

The following explains the parameters of the solution:

| Name                      | Type    | Description                                                                                                                                                                 | Default | Required |
|---------------------------|---------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------|----------|
| root                      | string  | Root folder of your data. Data structure must be provided as specified in documentation!                                                                                     | -       | True     |
| use_augmentation          | boolean | Whether to use augmentation or not. If enabled, the data is probabilistically flipped, rotated, elastic deformed, intensity scaled, and additionally noised. Default: True | True    | False    |
| limit_gpu_memory          | integer | The absolute number of bytes to allocate for GPU memory. Default: 12000                                                                                                     | 12000   | False    |
| patch_size                | integer | Patch size of each training instance. Must be given as a string separated by ",". Default: "48,128,128"                                                                    | 12000   | False    |
| unet_n_depth              | integer | The depth of the network. Default: 3                                                                                                                                        | 3       | False    |
| unet_pool_size            | string  | The pool size of the network. Must be given as a string separated by ",". Should be as many numbers as unet is deep. Default: "2,4,4"                                      | 2,4,4   | False    |
| train_class_weight        | string  | The weights for the binary cross entropy dice loss. First weight for negative class. Must be given as a string separated by ",". Default: "1,5"                            | 1,5     | False    |
| epochs                    | integer | Number of epochs to train for.                                                                                                                                              | 300     | False    |
| steps_per_epoch           | integer | Number of steps per epoch.                                                                                                                                                  | 512     | False    |
| train_reduce_lr_factor    | float   | Factor to reduce the learning rate over time.                                                                                                                               | 0.5     | False    |
| train_reduce_lr_patience  | integer | Patience after which to start learn rate reduction.                                                                                                                         | 50      | False    |


## Example: 3D segmentation of golgi aparatus with 3D U-Net

![](golgi.png)

This demonstrates how to use the solution to train a 3D U-Net model to perform semantic segmentation of the golgi aparatus from 3D FIB-SEM data 
The procedure is described in the paper:

Müller, Andreas, et al. "3D FIB-SEM reconstruction of microtubule–organelle interaction in whole primary mouse β cells." Journal of Cell Biology 220.2 (2021).

Download the example data (or adapt your own data into the same format)

wget https://syncandshare.desy.de/index.php/s/FikPy4k2FHS5L4F/download/data_golgi.zip
unzip data_golgi.zip
which should result in the following folder structure:

data_golgi
├── train
│   ├── images
│   └── masks
└── val
    ├── images
    └── masks

Call the solution by only providing the root folder of the data to reproduce the results of the paper.