# StarDist train album solution

This album solution can be used to train a StarDist model from the command line.

## How to run

use `album install` to install the solution.
use `album info` to view the parameters of the solution.
use `album run` to run the solution.

## documentation

The extensive documentation of StarDist can be found at https://github.com/stardist/stardist.

The following explains the parameters of the solution:

| Name              | Type    | Description                                                                                                                         | Default           | Required |
|-------------------|---------|-------------------------------------------------------------------------------------------------------------------------------------|-------------------|----------|
| root              | string  | Root folder of your data. The data structure must be provided as specified in the documentation!                                     | -                 | True     |
| out               | string  | Output folder                                                                                                                       | -                 | True     |
| total_memory      | integer | Total memory of the GPU to use at maximum.                                                                                           | 12000             | False    |
| grid              | string  | Grid of the model. It must be given as a string separated by "\\".                                                                   | 2,2,2             | False    |
| rays              | integer | Number of rays of the model.                                                                                                        | 96                | False    |
| use_gpu           | boolean | Whether to use GPU or not. Only enable if you have a compatible GPU available that supports TensorFlow 2.0.                         | False             | False    |
| n_channel_in      | integer | Number of input channels                                                                                                            | 1                 | False    |
| backbone          | string  | Backbone of the model. Please refer to [this link](https://github.com/stardist/stardist) for more details.                        | unet              | False    |
| unet_n_depth      | integer | Depth of the UNet model                                                                                                             | 3                 | False    |
| train_patch_size  | string  | Patch size of the training. Each of the three dimensions should be provided as a string, separated by commas.                      | 160,160,160       | False    |
| train_batch_size  | integer | Batch size used for training                                                                                                        | 1                 | False    |
| train_loss_weights| string  | Weights for the losses related to (probability, distance). Please provide them as a string, separated by commas.                    | 1,0.1             | False    |
| use_augmentation  | boolean | Whether to use data augmentation or not. If enabled, the data will be probabilistically flipped, rotated, elastic deformed, intensity scaled, and additionally noised. | True              | False    |


## Example: 3D segmentation of secretory granules with 3D stardist

![](granules.png)

This demonstrates how to use this solution to train a Stardist model to segment secretory granules from 3D FIB-SEM data.
The procedure is described in the paper:

Müller, Andreas, et al. "3D FIB-SEM reconstruction of microtubule–organelle interaction in whole primary mouse β cells." Journal of Cell Biology 220.2 (2021).

Download the example data (or adapt your own data into the same format)

wget https://syncandshare.desy.de/index.php/s/5SJFRtAckjBg5gx/download/data_granules.zip
unzip data_granules.zip
which should result in the following folder structure:

data_granules
├── train
│   ├── images
│   └── masks
└── val
    ├── images
    └── masks

Start the solution by only providing the root folder of the data (argument named "root")
and the output folder (argument named "out") to reproduce the results of the paper. 
This way the solution trains a 3D stardist model for 100 epochs.

