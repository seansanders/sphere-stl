from sstl_math import *
from sstl_image import *

class TriFace():
    """A triange face for a Sphere, defined by its three points"""
    
    def __init__(self, pts, resolution, flatBottom=False, flatTop=False):
        """
        pts -- int arraylike, length 3, cartesian points
        resolution -- int number of mesh intervals along the sides of the
                      triangle touching pts[0]
        flatBottom -- bool whether the bottom surface of the face should be
                      the flat triangle formed by pts, or otherwise follow the
                      sphere (default False)
        flatTop -- bool whether the top surface of the face should be the flat
                   triangle formed by pts, or otherwise follow the sphere
                   (default False)
        """
        
        self.pts = pts
        self.resolution = resolution
        self.flatTop = flatTop and flatBottom
        self.flatBottom = flatBottom
    
    def make_rotated_copy(self, rotation):
        """
        Returns a new TriFace with all points rotated by the 3x3
        matrix rotation and all other properties unchanged.
        """
        
        rotatedPts = [rotate(pt, rotation) for pt in self.pts]
        return TriFace(rotatedPts, self.resolution, self.flatBottom,
                       self.flatTop)

class QuadFace():
    """
    A parallelogram face for a Sphere, defined by a corner point and
    its two neighbors
    """
    
    def __init__(self, pts, resolution1, resolution2,
                 flatBottom=False, flatTop=False):
        """
        Arguments:
        pts -- float arraylike, length 3, cartesian points (the last point,
               opposite pts[0], implied by symmetry)
        resolution1 -- int number of mesh intervals along the first axis
                       (pts[0] to pts[1])
        resolution2 -- int number of mesh intervals along the second axis
                       (pts[0] to pts[2])
        flatBottom -- bool whether the bottom surface of the face should be
                      the flat parallelogram formed by pts, or otherwise follow
                      the sphere (default False)
        flatTop -- bool whether the top surface of the face should be the flat
                   parallelogram formed by pts, or otherwise follow the sphere
                   (default False)
        """
        
        # Only 3 points should be specified, and fourth calculated from them
        # (using point 0 to 1 and point 0 to 2 as axes)
        # This means that quads can only be parallelograms
        self.pts = pts 
        self.resolution1 = resolution1
        self.resolution2 = resolution2
        self.flatTop = flatTop and flatBottom
        self.flatBottom = flatBottom
        
    def make_rotated_copy(self, rotation):
        """
        Returns a new QuadFace with all points rotated by the 3x3
        matrix rotation and all other properties unchanged.
        """
        
        rotatedPts = [rotate(pt, rotation) for pt in self.pts]
        return QuadFace(rotatedPts, self.resolution1, self.resolution2,
                        self.flatBottom, self.flatTop)

class MeshTri():
    """Triangle to be written to an STL file."""
    
    def __init__(self, pts, color=(0,0,0)):
        """
        stores pts (float arraylike, length 3) and sets normal from pts.
        Assumes points are defined CCW, as per STL format
        """
        self.pts = pts
        self.normal = normalize(np.cross(self.pts[1] - self.pts[0],
                                         self.pts[2] - self.pts[0]))
        self.color = color

class Sphere():
    """
    Sphere (better yet, spherical shell) to be sliced into TriFace or
    QuadFaces with depth map applied
    """
    
    def __init__(self, img, proj, faces, normalizeFaceVertices, minAltitude,
                 maxAltitude, lowCutoff, rotation, scale):
        """
        img -- an ImageWrapper or interface-equivalent object containing
               depth map data
        proj -- a function mapping a cartesian point (float arraylike,
                length 3, sphere center at origin)
                to a point on img (arraylike of 2 nums in range [0, 1])
        faces -- list of TriFace or QuadFace faces to project depth map onto
        normalizeFaceVertices -- boolean, whether the distance of the corner
                                 points of each face in faces should be
                                 normalized to a distance of 1 from the
                                 origin before being scaled by scale and the
                                 appropriate radius
        minAltitude -- radius corresponding to depth values of 0 from img
        maxAltitude -- radius corresponding to depth values of 1 from img
        lowCutoff -- radius the bottom side of each face lies on. Not
                     recommended to be 0
        rotation -- rotation matrix to apply to points of faces (3x3 np.array
                    or list of lists of numbers), or None
        scale -- float arraylike, length 3, scale factors on X, Y, and Z,
                 respectively. Values may be negative but the absolute
                 value is taken. May be None
        """
        
        if lowCutoff >= maxAltitude:
            sys.exit("""Error: lowCutoff radius cannot be greater than the
                        maxAltitude radius""")
        
        if lowCutoff == 0:
            print("""Warning: a low cutoff radius of 0 may result in
                     extraneous/degenerate geometry if depth map has finely
                     detailed holes""")
        
        self.img = img
        self.proj = proj
        self.rotation = rotation
        
        if scale is None:
            self.scale = np.array((1, 1, 1))
        else:
            self.scale = np.absolute(scale)
        
        if rotation is None:
            self.faces = faces
        else:
            self.faces = [face.make_rotated_copy(rotation) for face in faces]
        
        self.normalizeFaceVertices = normalizeFaceVertices
        
        self.minAltitude = minAltitude
        self.maxAltitude = maxAltitude
        self.lowCutoff = lowCutoff
        
    def height_at_pt(self, pt):
        """
        Arguments:
        pt -- float arraylike, length 3, cartesian point to project into
              spherical and check depth value at
        
        Return -- float distance from sphere center (origin) to pt
        """
        
        loc = self.proj(pt)
        return self.img.height_at_loc(loc) * (self.maxAltitude
               - self.minAltitude) + self.minAltitude
    
    def hole_at_pt(self, pt):
        """
        Arguments:
        pt -- float arraylike, length 3, cartesian point to project into
              spherical and check hole status at
        
        Return -- Whether the depth map has a hole at pt
        """
        
        loc = self.proj(pt)
        return self.img.hole_at_loc(loc)
    
    def color_at_pt(self, pt):
        """
        Arguments:
        pt -- float arraylike, length 3, cartesian point to project into
              spherical and check hole status at
        
        Return -- Color of the image at pt (if there is a color image)
        """
        
        loc = self.proj(pt)
        return self.img.color_at_loc(loc)
            
# the cutoff is at 0- negative minAltitude will result in holes
# resolutions are 1 less than the number of points along their given axis,
# so that the total length along the axis is resultion_ units
class Prism():
    """Rectangular prism to apply depth map to"""
    
    def __init__(self, img, w, h, resolutionX, resolutionY, minAltitude,
                 maxAltitude):
        """
        img -- an ImageWrapper or interface-equivalent object containing
               depth map data
        w -- float width of prism
        h -- float length of the prism (not height/thickness)
        resolutionX -- int number of mesh intervals along the width of
                       the prism
        resolutionY -- int number of mesh intervals along the length of
                       the prism
        minAltitude -- height corresponding to depth values of 0 from img,
                       may be negative.
        maxAltitude -- height corresponding to depth values of 1 from img,
                       must be positive and > minAltitude.
        """
        
        if minAltitude < 0:
            print("""minAltitude for prism is less than 0- the final geometry
                     will only include points with an altitude above 0""")
            
        if maxAltitude <= 0:
            sys.exit("Error: maxAltitude for a prism cannot be 0 or less")
        
        if maxAltitude < minAltitude:
            sys.exit("""Error: maxAltitude for a prism cannot be less than
                        minAltitude""")
        
        self.img = img
        self.w = w
        self.h = h
        self.resolutionX = resolutionX
        self.resolutionY = resolutionY
        self.minAltitude = minAltitude
        self.maxAltitude = maxAltitude
        
    def height_at_pt(self, pt):
        """
        Arguments:
        pt -- float arraylike, length 2, positions on prism along w and h,
              respectively (in range 0 to 1)
        
        Return -- float distance from sphere center (origin) to pt
        """
        
        return self.img.height_at_loc(pt) * (self.maxAltitude \
               - self.minAltitude) + self.minAltitude
        
    def hole_at_pt(self, pt):
        """
        Arguments:
        pt -- float arraylike, length 2, positions on prism along w and h,
              respectively (in range 0 to 1)
        
        Return -- Whether the depth map has a hole at pt
        """
        
        return self.img.hole_at_loc(pt)
    
    def color_at_pt(self, pt):
        """
        Arguments:
        pt -- float arraylike, length 2, positions on prism along w and h,
              respectively (in range 0 to 1)
        
        Return -- RGB color at pt, or None if there is no color image
        """
        
        return self.img.color_at_loc(loc)

# unrotatedIcosaPts = [(0, -1, -phi), (0, -1, phi), (0, 1, -phi), (0, 1, phi),
#                      (-1, -phi, 0), (-1, phi, 0), (1, -phi, 0), (1, phi, 0),
#                      (-phi, 0, -1), (phi, 0, -1), (-phi, 0, 1), (phi, 0, 1)]

icosaPts = [(0, -1.70130161670408, -0.85065080835204),
            (0, 0.0, 1.9021130325903073),
            (0, 0.0, -1.9021130325903073),
            (0, 1.70130161670408, 0.85065080835204),
            (-1, -1.3763819204711736, 0.85065080835204),
            (-1, 1.3763819204711736, -0.85065080835204),
            (1, -1.3763819204711736, 0.85065080835204),
            (1, 1.3763819204711736, -0.85065080835204),
            (-1.618033988749895, -0.5257311121191336, -0.85065080835204),
            (1.618033988749895, -0.5257311121191336, -0.85065080835204),
            (-1.618033988749895, 0.5257311121191336, 0.85065080835204),
            (1.618033988749895, 0.5257311121191336, 0.85065080835204)]

icosaFaces = [(1,4,6), (1,6,11), (1,11,3), (1,3,10), (1,10,4),
              (0,6,4), (6,0,9), (9,11,6), (11,9,7), (7,3,11),
              (3,7,5), (5,10,3), (10,5,8), (8,4,10), (4,8,0),
              (2,0,8), (2,9,0), (2,7,9), (2,5,7), (2,8,5)]

octaPts = [(1, 0, 0), (-1, 0, 0), (0, 1, 0),
           (0, -1, 0), (0, 0, 1), (0, 0, -1)]
octaFaces = [(4, 1, 3), (4, 3, 0), (4, 0, 2), (4, 2, 1),
             (5, 3, 1), (5, 0, 3), (5, 2, 0), (5, 1, 2)]

cubePts = [(1, 1, 1), (1, 1, -1), (1, -1, 1), (1, -1, -1),
           (-1, 1, 1), (-1, 1, -1), (-1, -1, 1), (-1, -1, -1)]
cubeFaces = [(4, 6, 0), (6, 7, 2), (2, 3, 0),
             (0, 1, 4), (4, 5, 6), (7, 5, 3)]

rhombPts = [(1 + sqrt(2), 1, 1), (1 + sqrt(2), 1, -1), (1 + sqrt(2), -1, 1),
            (1 + sqrt(2), -1, -1), (-1 - sqrt(2), 1, 1), (-1 - sqrt(2), 1, -1),
            (-1 - sqrt(2), -1, 1), (-1 - sqrt(2), -1, -1), (1, 1 + sqrt(2), 1),
            (1, 1 + sqrt(2), -1), (-1, 1 + sqrt(2), 1), (-1, 1 + sqrt(2), -1),
            (1, -1 - sqrt(2), 1), (1, -1 - sqrt(2), -1), (-1, -1 - sqrt(2), 1),
            (-1, -1 - sqrt(2), -1), (1, 1, 1 + sqrt(2)), (1, -1, 1 + sqrt(2)),
            (-1, 1, 1 + sqrt(2)), (-1, -1, 1 + sqrt(2)), (1, 1, -1 - sqrt(2)),
            (1, -1, -1 - sqrt(2)), (-1, 1, -1 - sqrt(2)),
            (-1, -1, -1 - sqrt(2))]

rhombSquareFaces = [(18, 19, 16), (19, 14, 17), (17, 2, 16), (16, 8, 18),
                    (18, 4, 19), (14, 15, 12), (12, 13, 2), (2, 3, 0),
                    (0, 1, 8), (8, 9, 10), (10, 11, 4), (4, 5, 6),
                    (6, 7, 14), (15, 23, 13), (3, 21, 1), (9, 20, 11),
                    (5, 22, 7), (23, 22, 21)]
rhombTriFaces    = [(19, 6, 14), (17, 12, 2), (16, 0, 8), (18, 10, 4),
                    (23, 15, 7), (21, 3, 13), (20, 9, 1), (22, 5, 11)]

cube = {"normalize": True,
    "pts": cubePts, "quads": cubeFaces, "tris": []}
octahedron = {"normalize": True,
    "pts": octaPts, "quads": [], "tris": octaFaces}
rhomb = {"normalize": True,
    "pts": rhombPts, "quads": rhombSquareFaces, "tris": rhombTriFaces}
icosahedron = {"normalize": True,
    "pts": icosaPts, "quads": [], "tris": icosaFaces}

faceShapes = {"cube": cube, "octahedron": octahedron, "rhomb": rhomb,
    "icosahedron": icosahedron}
