# Overview

This program takes in a depthmap image (or multiple depthmap images, with weights) and constructs a 3D geometry, producing one or more STL files. The geometry may just be a rectangular prism, output in one file; or a sphere, sliced into triangular and quadrilateral faces and output in multiple files. Optionally, further images specifying the location of holes through the geometry and color may be used (it should be noted that color is not a standard part of the STL format and may not be interpreted consistently between programs).

Warning: STL files are uncompressed and inefficient! High-resolution files will take many minutes to export and take up hundreds of megabytes.

# Usage and prerequisites

This program requires Python 3 (to be safe, use 3.12 or later, but it's doubtful I wrote anything that won't work in older versions) and the [numpy](https://numpy.org/install/), [scipy](https://scipy.org/install/), and [Pillow](https://pillow.readthedocs.io/en/stable/installation/basic-installation.html) packages.
Make sure all the files from this repository are present in the same directory, edit params.json to your liking, and you're good to go. Then run:

    python3 sstl_main.py

(or an equivalent command)

# Specifying spherical faces

The polygonal faces used to slice the sphere may be user-specified or chosen from a set of standard polyhedra. A user-specified list of faces must use the following json format:

    {
        "normalize": true,
        "pts": [
                [0, 0, 0],
                [0, 0, 0],
                [0, 0, 0],
                [0, 0, 0]
            ],
        "quads": [
                [0, 1, 2],
                [1, 2, 3]
            ],
        "tris": [
                [0, 1, 2],
                [1, 2, 3],
            ]
    }

* "normalize" specifies whether each point in "pts" will be normalized to a distance of 1 from the origin or not (when true, this ensures the sphere will actually use the specified radii).
* The numbers specifying a quadrilateral or triangle are indices into the "pts" array.
* Quadrilaterals are defined using only three points, so must be parallelograms (otherwise, they might not necessarily be flat...)

# Other notes on usage

* Output files treat Z as the vertical axis and have no intended units (numbers given by the user to control geometry size translate directly to the geometry in the files.)
* The depthmap may be a color file, but it will simply be converted to grayscale and treated normally.
* The alpha channel in the depthmap images will be used to place holes through the geometry together with "holeImage". An alpha value less than half the maximum (of the weighted total) will generate a hole.
* Any point below the "lowCutoff" surface for spheres and below a height of 0 for prisms will become a hole.
* For prisms, minAltitude may be less than 0.
* For spheres, radius parameters determine the distance from the center to the corner points of each face, and not necessarily.
* "minAltitude" and "maxAltitude" correspond to the minimum and maximum value the depthmap images are able to store, not that they actually store.
* For spheres, the scale is applied after the rotation.
* For spheres, "rotation" must be a three-character string representing the three rotation axes for [Euler angles](https://en.wikipedia.org/wiki/Euler_angles). The characters must be all uppercase (extrinsic rotation) or all lowercase (intrinsic rotation). Valid values are "XYX", "XYZ", "XZX", "XZY", "YXY", "YXZ", "YZX", "YZY", "ZXY", "ZXZ", "ZYX", "ZYZ", and lowercase equivalents.
* Scale parameters (each value in "scale" for spheres and "width" and "height" for prisms) have their absolute values taken, as otherwise the mesh normals may become reversed (probably problematic). To mirror your geometry, please mirror your input files.
* Other constraints on parameters are given in the comments of the params.json file itself. Let me know if I've left anything unclear...

# Special Thanks
Chris Maiwald ([https://papas-best.com/](https://papas-best.com/)) for assistance with color format and for creating [Papa's Best STL Viewer](https://papas-best.com/stlviewer_en), which was used for validation during the development of this program.
