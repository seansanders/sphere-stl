from math import *
import numpy as np
from scipy.spatial.transform import Rotation

x_axis = np.array((1, 0, 0))
y_axis = np.array((0, 1, 0))
z_axis = np.array((0, 0, 1))

# valid sequences of euler angles to construct rotations
validExtrinsics = ["XYX", "XYZ", "XZX", "XZY", "YXY", "YXZ",
                   "YZX", "YZY", "ZXY", "ZXZ", "ZYX", "ZYZ"]
                   
validIntrinsics = ["xyx", "xyz", "xzx", "xzy", "yxy", "yxz",
                   "yzx", "yzy", "zxy", "zxz", "zyx", "zyz"]

def vector_scale(vec, c):
    return [vec[i] * c for i in range(len(vec))]

def length(vec):
    """Returns the length of a vector"""
    
    return sqrt(sum(val*val for val in vec))

def normalize(vec):
    """Normalizes a vector (makes it length 1), aside from 0 length vectors."""
    mag = length(vec)
    return vec if mag == 0 else np.array([val/mag for val in vec])

def cartesian_to_spherical(pt):
    """
    Transforms pt, a length 3 arraylike in cartesian coordinates, to
    spherical coordinates
    """
    radial = length(pt)
    polar = atan2(sqrt(pt[0]**2 + pt[1]**2), pt[2])
    azimuthal = atan2(pt[1], pt[0])
    return (radial, polar, azimuthal)

def spherical_to_cartesian(pt):
    """
    Transforms pt, a length 3 arraylike in spherical coordinates, to
    cartesian coordinates
    """
    temp = sin(pt[1])
    x = pt[0] * temp * cos(pt[2])
    y = pt[0] * temp * sin(pt[2])
    z = pt[0] * cos(pt[1])
    return (x, y, z)

def cartesian_to_equirectangular_map(pt):
    """
    Transforms pt, a length 3 arraylike in cartesian coordinates, to a
    length 2 arraylike (the two angular coordinates in spherical space,
    scaled to image coordinates in the range [0,1]- the latitude
    coord is flipped)
    """
    longitude = atan2(pt[1], pt[0])
    latitude = -atan2(pt[2], sqrt(pt[0]**2 + pt[1]**2))
    return (longitude / (2 * pi) + 0.5, latitude / pi + 0.5)
 
def cartesian_to_cylindrical_map(pt):
    """
    Transforms pt, a length 3 arraylike in cartesian coordinates, to a
    length 2 arraylike (cylindrical projection scaled to [0,1] and with
    latitude coord flipped)
    """
    longitude = atan2(pt[1], pt[0])
    latitude = sin(-atan2(pt[2], sqrt(pt[0]**2 + pt[1]**2)))
    return (longitude / (2 * pi) + 0.5, latitude / 2 + 0.5)

def rotate(pt, rotation):
    """
    Applies rotation matrix to pt and returns the result.
    
    Arguments:
    pt-- length 3 number arraylike
    rotation-- 3x3 array, rotation matrix
    """
    
    return np.transpose(np.matmul(rotation, np.transpose(pt)))

projections = {"equirectangular": cartesian_to_equirectangular_map,
               "cylindrical": cartesian_to_cylindrical_map}
