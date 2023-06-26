# StarDist train album solution

This album solution can be used to use a StarDist already trained model for inference from the command line.

## documentation

The extensive documentation of StarDist can be found at https://github.com/stardist/stardist.

## Example: 3D segmentation of secretory granules with 3D stardist

![](granules.png)

This code in the solution was used predict from aStardist model to segment secretory granules from 3D FIB-SEM data as
described in the paper:

Müller, Andreas, et al. "3D FIB-SEM reconstruction of microtubule–organelle interaction in whole primary mouse β cells."
Journal of Cell Biology 220.2 (2021).

Download the example data (or adapt your own data into the same format)

wget https://syncandshare.desy.de/index.php/s/5SJFRtAckjBg5gx/download/data_granules.zip
unzip data_granules.zip
which should result in the following folder structure:

data_granules
├── train
│ ├── images
│ └── masks
└── val
├── images
└── masks

The model must be received by calling the StarDist train album solution first.

# todo: reproducable call
