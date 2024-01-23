# Launch-ilastik Album Solution

## Introduction
Launch-ilastik is a solution designed to streamline the usage of [ilastik](https://www.ilastik.org/documentation/) for image analysis tasks. ilastik is a powerful tool for image classification, segmentation, and more, making it suitable for various applications, including bioimage analysis.

## Installation
Ensure that the Album framework is installed by following the instructions available [here](https://album.solutions/). Add the catalog to your Album installation to access and install solutions.

Install the Launch-ilastik solution using the graphical user interface (GUI) of Album or run the following command in the terminal:
```bash
album install segmentation:ilastik-launcher:0.1.0
```

## How to use
### launch-ilastik
To start ilastik, launch the solution using the GUI of album or run the following command in the terminal:
```bash
album run segmentation:ilastik-launcher:0.1.0
```

## Hardware requirements
ilastik requires a 64-bit operating system and at least 8GB of RAM. For more information, please refer to the [ilastik documentation](https://www.ilastik.org/documentation/basics/installation#requirements).

## Citation & License
This solution is is under GNU General Public License version 2 or later with exception to allow non-GPL extensions. For more information, please refer to the [ilastik documentation](https://www.ilastik.org/license).

If you use this solution, please cite the following paper: 
```
text: Berg, S., Kutra, D., Kroeger, T. et al. ilastik: interactive machine learning for (bio)image analysis. Nat Methods 16, 1226–1232 (2019).
doi: 10.1038/s41592-019-0582-9
```
