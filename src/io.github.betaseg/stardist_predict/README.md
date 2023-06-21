# StarDist train album solution

This album solution can be used to use a StarDist already trained model for inference from the command line.

## How to run

use `album install` to install the solution.
use `album info` to view the parameters of the solution.
use `album run` to run the solution.

## documentation

The extensive documentation of StarDist can be found at https://github.com/stardist/stardist.

The following explains the parameters of the solution:

| Name           | Type   | Description                            | Default | Required |
|----------------|--------|----------------------------------------|---------|----------|
| fname_input    | string | Input file                             | -       | True     |
| model_name     | string | Input model                            | -       | True     |
| model_basedir  | string | Path to the model directory            | -       | True     |
| output_dir     | string | Path to the output directory           | -       | True     |
| n_tiles        | string | Number of tiles per dimension          | None    | False    |


## Example: 3D segmentation of secretory granules with 3D stardist

![](granules.png)

This code in the solution was used predict from aStardist model to segment secretory granules from 3D FIB-SEM data as described in the paper:

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

The model must be received by calling the StarDist train album solution first.

