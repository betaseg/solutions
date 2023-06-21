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
