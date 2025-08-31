import os
import struct
from sstl_math import *
from sstl_shapes import *

class STLFileWrapper():
    """Contains an STL file and allows writing triangles to it"""
    
    def __init__(self, path, colormode):
        """create new file at the given path and write (empty) STL header"""
        
        self.f = open(path, "x")
        self.f.close()
        self.f = open(path, "wb")
        
        self.colormode = colormode
        
        if colormode == "RGB":
            self.f.write(b'Created by 3DBrowser (www.mootools.com)\x00')
            self.f.write(bytes(44))
        elif colormode == "BGR":
            self.f.write(b'AutoCAD solid\x00')
            self.f.write(bytes(70))
        else:
            self.f.write(bytes(84))
        
        self.tris = 0
        self.open = True
    
    def write_tri(self, tri):
        """Write triangle (MeshTri) to the file"""
        
        if (self.open):
            self.f.write(struct.pack('<f', tri.normal[0]))
            self.f.write(struct.pack('<f', tri.normal[1]))
            self.f.write(struct.pack('<f', tri.normal[2]))
            self.f.write(struct.pack('<f', tri.pts[0][0]))
            self.f.write(struct.pack('<f', tri.pts[0][1]))
            self.f.write(struct.pack('<f', tri.pts[0][2]))
            self.f.write(struct.pack('<f', tri.pts[1][0]))
            self.f.write(struct.pack('<f', tri.pts[1][1]))
            self.f.write(struct.pack('<f', tri.pts[1][2]))
            self.f.write(struct.pack('<f', tri.pts[2][0]))
            self.f.write(struct.pack('<f', tri.pts[2][1]))
            self.f.write(struct.pack('<f', tri.pts[2][2]))
            
            if self.colormode == "BGR":
                r = tri.color[0]
                g = tri.color[1]
                b = tri.color[2]
                color = ((b >> 3) << 10) | ((g >> 3) << 5) | (r >> 3)
                self.f.write((color).to_bytes(2, "little"))
            elif self.colormode == "RGB":
                r = tri.color[0]
                g = tri.color[1]
                b = tri.color[2]
                color = ((r >> 3) << 10) | ((g >> 3) << 5) | (b >> 3) \
                    | (1 << 15)
                
                self.f.write((color).to_bytes(2, "little"))
            else:
                self.f.write(bytes(2))
            
            self.tris += 1
        else:
            sys.exit("Error: tried to write to closed file...")
    
    def close(self):
        """Write the triangle count to the file and then close the file"""
        
        self.f.seek(80, os.SEEK_SET)
        self.f.write((self.tris).to_bytes(4, byteorder='little', signed=False))
        self.f.close()

def write_mesh_tris(solid, stl, face=None):
    """
    Writes mesh triangles making up a portion of solid defined by face (if
    solid is a Sphere) or the solid itself (if Prism) with data from the
    height map in solid.
    The height map controls height/altitude at each mesh point and also
    presence of holes all the way through the geometry at points.
    
    Arguments:
    solid -- The Sphere or Prism containing the height map and base dimensions
              used to construct mesh
    stl -- The STLFileWrapper to write mesh data to
    face -- The TriFace or QuadFace determining the portion of solid to create
            mesh in the shape of if the Solid is a sphere
    """
    
    pts = []
    basePts = []
    
    if isinstance(solid, Prism):
        for i in range(solid.resolutionY + 1):
            y = i / solid.resolutionY
            
            pts.append([])
            basePts.append([])
            
            if len(pts) > 2:
                pts.pop(0)
                basePts.pop(0)
                
            for j in range(solid.resolutionX + 1):
                x = j / solid.resolutionX
                
                pt = np.array((x, y))
                height = solid.height_at_pt(pt)
                isHole = solid.hole_at_pt(pt)
                pt = np.array((x * solid.w, -y * solid.h, height))
                
                basePts[-1].append(np.array((x * solid.w, -y * solid.h, 0)))
                
                if height > 0 and not isHole:
                    pts[-1].append(pt)
                else:
                    pts[-1].append(None)
                    
            if len(pts) == 2:
                for col in range(solid.resolutionX):
                    pt1 = pts[-2][col]
                    pt2 = pts[-1][col]
                    pt3 = pts[-1][col + 1]
                    pt4 = pts[-2][col + 1]
                    
                    base1 = basePts[-2][col]
                    base2 = basePts[-1][col]
                    base3 = basePts[-1][col + 1]
                    base4 = basePts[-2][col + 1]
                    
                    missing = 0
                    
                    if pt1 is None:
                        missing += 1
                        pt1 = base1
                        
                    if pt2 is None:
                        missing += 1
                        pt2 = base2
                        
                    if pt4 is None:
                        missing += 1
                        pt4 = base4
                 
                    if missing < 3:
                        color = solid.color_at_pt((pt1 + pt2 + pt4) / 3)
                        stl.write_tri(MeshTri([pt1, pt2, pt4], color)) # top
                        stl.write_tri(MeshTri([base1, base4, base2]), \
                                      color) # under
                        
                    pt2 = pts[-1][col]
                    pt4 = pts[-2][col + 1]
                    missing = 0
                    
                    if pt2 is None:
                        missing += 1
                        pt2 = base2
                        
                    if pt3 is None:
                        missing += 1
                        pt3 = base3
                        
                    if pt4 is None:
                        missing += 1
                        pt4 = base4
                    
                    if missing < 3:
                        color = solid.color_at_pt((pt4 + pt2 + pt3) / 3)
                        stl.write_tri(MeshTri([pt4, pt2, pt3]), color) # top
                        stl.write_tri(MeshTri([base4, base3, base2], \
                                      color)) # under
                
                # create the edge triangles on either side of this row
                pt1 = pts[-2][0]
                pt2 = pts[-1][0]
                pt3 = pts[-2][-1]
                pt4 = pts[-1][-1]
                base1 = basePts[-2][0]
                base2 = basePts[-1][0]
                base3 = basePts[-2][-1]
                base4 = basePts[-1][-1]
                
                if pt1 is None:
                    if pt2 is not None:
                        color = solid.color_at_pt(pt2)
                        stl.write_tri(MeshTri([pt2, base1, base2], color))
                elif pt2 is None:
                    color = solid.color_at_pt(pt1)
                    stl.write_tri(MeshTri([pt1, base1, base2], color))
                else:
                    color = solid.color_at_pt(pt2)
                    stl.write_tri(MeshTri([pt1, base1, pt2], color))
                    stl.write_tri(MeshTri([pt2, base1, base2], color))
                if pt3 is None:
                    if pt4 is not None:
                        color = solid.color_at_pt(pt4)
                        stl.write_tri(MeshTri([pt4, base4, base3], color))
                elif pt4 is None:
                    color = solid.color_at_pt(pt3)
                    stl.write_tri(MeshTri([pt3, base4, base3], color))
                else:
                    color = solid.color_at_pt(pt4)
                    stl.write_tri(MeshTri([pt3, pt4, base3], color))
                    stl.write_tri(MeshTri([pt4, base4, base3], color))
             
            # create the edge triangles along the top row
            if i == 0:
                for col in range(len(pts[-1]) - 1):
                    pt1 = pts[0][col]
                    pt2 = pts[0][col + 1]
                    base1 = basePts[0][col]
                    base2 = basePts[0][col + 1]
                    
                    if pt1 is None:
                        if pt2 is not None:
                            color = solid.color_at_pt(pt2)
                            stl.write_tri(MeshTri([pt2, base2, base1], color))
                    elif pt2 is None:
                        color = solid.color_at_pt(pt1)
                        stl.write_tri(MeshTri([pt1, base2, base1], color))
                    else:
                        color = solid.color_at_pt(pt2)
                        stl.write_tri(MeshTri([pt1, pt2, base1], color))
                        stl.write_tri(MeshTri([pt2, base2, base1], color))
            
            # create the edge triangles along the bottom row
            if i == solid.resolutionY:
                for col in range(len(pts[-1]) - 1):
                    pt1 = pts[-1][col]
                    pt2 = pts[-1][col + 1]
                    base1 = basePts[-1][col]
                    base2 = basePts[-1][col + 1]
                    
                    if pt1 is None:
                        if pt2 is not None:
                            color = solid.color_at_pt(pt2)
                            stl.write_tri(MeshTri([pt2, base1, base2], color))
                    elif pt2 is None:
                        color = solid.color_at_pt(pt1)
                        stl.write_tri(MeshTri([pt1, base1, base2], color))
                    else:
                        color = solid.color_at_pt(pt2)
                        stl.write_tri(MeshTri([pt1, base1, pt2], color))
                        stl.write_tri(MeshTri([pt2, base1, base2], color))
    
    elif isinstance(solid, Sphere):
        if solid.normalizeFaceVertices:
            corners = [normalize(pt) for pt in face.pts]
        else:
            corners = face.pts
        
        scaledCorners = [np.multiply(pt, solid.scale) for pt in corners]
        
        vertexColors = []
        centerColors = []
        
        # storing the unrotated base points for a row from one iteration
        # to the next is necessary to calculate the centers of each mesh
        # triangle and thus the location to sample the colors of each triangle
        unrotatedPrevBasePts = []
        
        if face is None:
            print("""Error: no face specified with Sphere solid in
                     write_mesh_tris""")
        
        if isinstance(face, TriFace):
            center = sum(corners) / 3
            
            # first loop: calculate points
            for i in range(face.resolution + 1):
                c1 = i / face.resolution
                pts.append([])
                basePts.append([])
                vertexColors.append([])
                centerColors.clear()
                
                if len(pts) > 2:
                    pts.pop(0)
                    basePts.pop(0)
                    vertexColors.pop(0)
                
                # determine height of all points in this row (unless holes)
                for j in range(i + 1):
                    c2 = j / max(i, 1)
                    d1 = ((corners[1] - corners[0]) * c1) + corners[0]
                    d2 = ((corners[2] - corners[0]) * c1) + corners[0]
                    pt = ((d2 - d1) * c2) + d1
                    
                    height = solid.height_at_pt(pt)
                    isHole = solid.hole_at_pt(pt)
                    
                    if face.flatBottom:
                        baseHeight = length(pt) * solid.lowCutoff
                        basePts[-1].append(pt * solid.lowCutoff)
                        
                        if face.flatTop:
                            if (height * length(pt) <= baseHeight) or isHole:
                                pts[-1].append(None)
                            else:
                                pts[-1].append(pt * height)
                        else:
                            if (height <= baseHeight) or isHole:
                                pts[-1].append(None)
                            else:
                                pts[-1].append(normalize(pt) * height)
                            
                    else:
                        pt = normalize(pt)
                        basePts[-1].append(pt * solid.lowCutoff)
                        
                        if (height <= solid.lowCutoff) or isHole:
                            pts[-1].append(None)
                        else:
                            pts[-1].append(pt * height)
                
                # store colors at all necessary points in the mesh
                if i == face.resolution:
                    for col in range(i + 1):
                      vertexColors[-1].append(solid.color_at_pt( \
                          basePts[-1][col]))
                else:
                    vertexColors[-1].append(solid.color_at_pt(basePts[-1][0]))
                    vertexColors[-1].append(solid.color_at_pt(basePts[-1][-1]))
                    
                if i > 0:
                    for col in range(len(pts[-2]) * 2 - 1):
                        if (col % 2) == 0:
                            centerColors.append(
                                solid.color_at_pt( \
                                (unrotatedPrevBasePts[col // 2] + \
                                basePts[-1][col // 2] + \
                                basePts[-1][col // 2 + 1]) / 3))
                        else:
                            centerColors.append(solid.color_at_pt( \
                                (basePts[-1][(col + 1) // 2] + \
                                unrotatedPrevBasePts[(col + 1) // 2] + \
                                unrotatedPrevBasePts[(col - 1) // 2]) / 3))
                
                unrotatedPrevBasePts.clear()
                
                # scale, then rotate and translate the points so the piece is
                # flat to the xy plane
                R = Rotation.align_vectors([x_axis, z_axis],
                    [scaledCorners[1] - scaledCorners[0],
                     np.cross(scaledCorners[1] - scaledCorners[0],
                              scaledCorners[2] - \
                              scaledCorners[0])])[0].as_matrix()
                
                origin = scaledCorners[0] * solid.lowCutoff
                
                for col in range(len(pts[-1])):
                    unrotatedPrevBasePts.append(basePts[-1][col])
                    basePts[-1][col] = rotate(R, \
                        np.multiply(basePts[-1][col], solid.scale) - origin)
                    
                    if pts[-1][col] is not None:
                        pts[-1][col] = rotate(R, \
                            np.multiply(pts[-1][col], solid.scale) - origin)
                
                bottomFaceDegenerate = solid.lowCutoff == 0
                
                if len(pts) == 2:
                    # create the mesh triangles for the height geometery (top)
                    # and underside of the piece
                    for col in range(len(pts[-2]) * 2 - 1):
                        # mesh triangles with points facing towards corners[0]
                        if (col % 2) == 0:
                            pt1 = pts[-2][col // 2]
                            pt2 = pts[-1][col // 2]
                            pt3 = pts[-1][col // 2 + 1]
                            base1 = basePts[-2][col // 2]
                            base2 = basePts[-1][col // 2]
                            base3 = basePts[-1][col // 2 + 1]
                            
                        # mesh tris with points facing away from corners[0]
                        else:
                            pt1 = pts[-1][(col + 1) // 2]
                            pt2 = pts[-2][(col + 1) // 2]
                            pt3 = pts[-2][(col - 1) // 2]
                            base1 = basePts[-1][(col + 1) // 2]
                            base2 = basePts[-2][(col + 1) // 2]
                            base3 = basePts[-2][(col - 1) // 2]
                        
                        missing = 0
                        
                        if pt1 is None:
                            missing += 1
                            pt1 = base1
                            
                        if pt2 is None:
                            missing += 1
                            pt2 = base2
                            
                        if pt3 is None:
                            missing += 1
                            pt3 = base3
                        
                        if missing < 3:
                            if not (missing > 1 and bottomFaceDegenerate):
                                stl.write_tri(MeshTri([pt1, pt2, pt3], \
                                              centerColors[col])) # top
                            
                            # don't make base triangles when underside is
                            # a single point...
                            if not bottomFaceDegenerate:
                                stl.write_tri(MeshTri([base1, base3, base2], \
                                              centerColors[col])) # bottom
                    
                    # create the edge triangles on either side of this row
                    pt1 = pts[-2][0]
                    pt2 = pts[-1][0]
                    pt3 = pts[-2][-1]
                    pt4 = pts[-1][-1]
                    base1 = basePts[-2][0]
                    base2 = basePts[-1][0]
                    base3 = basePts[-2][-1]
                    base4 = basePts[-1][-1]
                    color1 = vertexColors[-2][0]
                    color2 = vertexColors[-1][0]
                    color3 = vertexColors[-2][-1]
                    color4 = vertexColors[-1][-1]
                    
                    if bottomFaceDegenerate:
                        if pt1 is not None and pt2 is not None:
                            stl.write_tri(MeshTri([pt1, base1, pt2], color1))
                        
                        if pt3 is not None and pt4 is not None:
                            stl.write_tri(MeshTri([pt3, pt4, base1], color3))
                    else:
                        if pt1 is None:
                            if pt2 is not None:
                                stl.write_tri(MeshTri([pt2, base1, base2], \
                                              color2))
                        elif pt2 is None:
                            stl.write_tri(MeshTri([pt1, base1, base2], color1))
                        else:
                            stl.write_tri(MeshTri([pt1, base1, pt2], color2))
                            stl.write_tri(MeshTri([pt2, base1, base2], color2))
                        if pt3 is None:
                            if pt4 is not None:
                                stl.write_tri(MeshTri([pt4, base4, base3], \
                                              color4))
                        elif pt4 is None:
                            stl.write_tri(MeshTri([pt3, base4, base3], color3))
                        else:
                            stl.write_tri(MeshTri([pt3, pt4, base3], color4))
                            stl.write_tri(MeshTri([pt4, base4, base3], color4))
                
                # create the edge triangles along the bottom row
                if i == face.resolution:
                    for col in range(len(pts[-1]) - 1):
                        pt1 = pts[-1][col]
                        pt2 = pts[-1][col + 1]
                        base1 = basePts[-1][col]
                        base2 = basePts[-1][col + 1]
                        color1 = vertexColors[-1][col]
                        color2 = vertexColors[-1][col + 1]
                        
                        if bottomFaceDegenerate:
                            if (pt1 is not None and pt2 is not None):
                                stl.write_tri(MeshTri([pt1, base1, pt2], \
                                              color1))
                        else:
                            if pt1 is None:
                                if pt2 is not None:
                                    stl.write_tri(MeshTri([pt2, base1, \
                                                  base2], color2))
                            elif pt2 is None:
                                stl.write_tri(MeshTri([pt1, base1, base2], \
                                              color1))
                            else:
                                stl.write_tri(MeshTri([pt1, base1, pt2], \
                                              color2))
                                stl.write_tri(MeshTri([pt2, base1, base2], \
                                              color2))
                
        elif isinstance(face, QuadFace):
            center = (corners[1] + corners[2]) / 2
            
            # first loop: calculate points
            for i in range(face.resolution1 + 1):
                c1 = i / face.resolution1
                d1 = (corners[1] - corners[0]) * c1
                pts.append([])
                basePts.append([])
                vertexColors.append([])
                centerColors.clear()
                
                if len(pts) > 2:
                    pts.pop(0)
                    basePts.pop(0)
                    vertexColors.pop(0)
                
                for j in range(face.resolution2 + 1):
                    c2 = j / face.resolution2
                    d2 = (corners[2] - corners[0]) * c2
                    pt = d1 + d2 + corners[0]
                    
                    height = solid.height_at_pt(pt)
                    isHole = solid.hole_at_pt(pt)
                    
                    if face.flatBottom:
                        baseHeight = length(pt) * solid.lowCutoff
                        basePts[-1].append(pt * solid.lowCutoff)
                        
                        if face.flatTop:
                            if (height * length(pt) <= baseHeight) or isHole:
                                pts[-1].append(None)
                            else:
                                pts[-1].append(pt * height)
                        else:
                            if (height <= baseHeight) or isHole:
                                pts[-1].append(None)
                            else:
                                pts[-1].append(normalize(pt) * height)
                            
                    else:
                        pt = normalize(pt)
                        basePts[-1].append(pt * solid.lowCutoff)
                        
                        if (height <= solid.lowCutoff) or isHole:
                            pts[-1].append(None)
                        else:
                            pts[-1].append(pt * height)
                
                # store colors at all necessary points in the mesh
                if (i == 0) or (i == face.resolution1):
                    for col in range(face.resolution2 + 1):
                        vertexColors[-1].append(solid.color_at_pt( \
                            basePts[-1][col]))
                else:
                    vertexColors[-1].append(solid.color_at_pt(basePts[-1][0]))
                    vertexColors[-1].append(solid.color_at_pt(basePts[-1][-1]))
                    
                if i > 0:
                    for col in range(face.resolution2):
                        centerColors.append(solid.color_at_pt(( \
                            unrotatedPrevBasePts[col] + basePts[-1][col] + \
                            unrotatedPrevBasePts[col + 1]) / 3))
                        centerColors.append(solid.color_at_pt(( \
                            unrotatedPrevBasePts[col + 1] + \
                            basePts[-1][col] + \
                            basePts[-1][col + 1]) / 3))
                
                unrotatedPrevBasePts.clear()
                
                # scale, then rotate and translate the points so the piece is
                # flat to the xy plane
                R = Rotation.align_vectors([x_axis, z_axis],
                    [scaledCorners[1] - scaledCorners[0],
                     np.cross(scaledCorners[1] - scaledCorners[0],
                              scaledCorners[2] - \
                              scaledCorners[0])])[0].as_matrix()
                
                origin = scaledCorners[0] * solid.lowCutoff
                
                for col in range(len(pts[-1])):
                    unrotatedPrevBasePts.append(basePts[-1][col])
                    basePts[-1][col] = rotate(R, \
                        np.multiply(basePts[-1][col], solid.scale) - origin)
                    
                    if pts[-1][col] is not None:
                        pts[-1][col] = rotate(R, \
                            np.multiply(pts[-1][col], solid.scale) - origin)
                
                bottomFaceDegenerate = solid.lowCutoff == 0
                
                # create the mesh triangles for the height geometery (top) and
                # for quad faces, obviously the mesh subdivides into quads
                # which then must be subdivided into 2 triangles
                if len(pts) == 2:
                    for col in range(face.resolution2):
                        # begin first triangle in unit quad
                        pt1 = pts[-2][col]
                        pt2 = pts[-1][col]
                        pt3 = pts[-1][col + 1]
                        pt4 = pts[-2][col + 1]
                        base1 = basePts[-2][col]
                        base2 = basePts[-1][col]
                        base3 = basePts[-1][col + 1]
                        base4 = basePts[-2][col + 1]
                        
                        missing = 0
                        
                        if pt1 is None:
                            missing += 1
                            pt1 = base1
                            
                        if pt2 is None:
                            missing += 1
                            pt2 = base2
                            
                        if pt4 is None:
                            missing += 1
                            pt4 = base4
                        
                        if missing < 3:
                            color = centerColors[col * 2]
                            
                            if not (missing > 1 and bottomFaceDegenerate):
                                stl.write_tri(MeshTri([pt1, pt2, pt4], \
                                              color)) # top
                            
                            # don't make base triangles when underside is
                            # a single point
                            if not bottomFaceDegenerate:
                                stl.write_tri(MeshTri([base1, base4, base2], \
                                              color)) # bottom
                        
                        # begin second triangle in unit quad
                        pt2 = pts[-1][col]
                        pt4 = pts[-2][col + 1]
                        missing = 0
                        
                        if pt2 is None:
                            missing += 1
                            pt2 = base2
                            
                        if pt3 is None:
                            missing += 1
                            pt3 = base3
                            
                        if pt4 is None:
                            missing += 1
                            pt4 = base4
                        
                        if missing < 3:
                            color = centerColors[col * 2 + 1]
                            
                            if not (missing > 1 and bottomFaceDegenerate):
                                stl.write_tri(MeshTri([pt4, pt2, pt3], \
                                              color)) # top
                            
                            # don't make base triangles when underside is
                            # a single point
                            if not bottomFaceDegenerate:
                                stl.write_tri(MeshTri([base4, base3, base2], \
                                              color)) # bottom
                    
                    # create the edge triangles on either side of this row
                    pt1 = pts[-2][0]
                    pt2 = pts[-1][0]
                    pt3 = pts[-2][-1]
                    pt4 = pts[-1][-1]
                    base1 = basePts[-2][0]
                    base2 = basePts[-1][0]
                    base3 = basePts[-2][-1]
                    base4 = basePts[-1][-1]
                    color1 = vertexColors[-2][0]
                    color2 = vertexColors[-1][0]
                    color3 = vertexColors[-2][-1]
                    color4 = vertexColors[-1][-1]
                    
                    if bottomFaceDegenerate:
                        if pt1 is not None and pt2 is not None:
                            stl.write_tri(MeshTri([pt1, base1, pt2], color1))
                        
                        if pt3 is not None and pt4 is not None:
                            stl.write_tri(MeshTri([pt3, pt4, base1], color3))
                    else:
                        if pt1 is None:
                            if pt2 is not None:
                                stl.write_tri(MeshTri([pt2, base1, base2], \
                                              color2))
                        elif pt2 is None:
                            stl.write_tri(MeshTri([pt1, base1, base2], \
                                          color1))
                        else:
                            stl.write_tri(MeshTri([pt1, base1, pt2], color2))
                            stl.write_tri(MeshTri([pt2, base1, base2], color2))
                        if pt3 is None:
                            if pt4 is not None:
                                stl.write_tri(MeshTri([pt4, base4, base3], \
                                              color4))
                        elif pt4 is None:
                            stl.write_tri(MeshTri([pt3, base4, base3], color3))
                        else:
                            stl.write_tri(MeshTri([pt3, pt4, base3], color4))
                            stl.write_tri(MeshTri([pt4, base4, base3], color4))
                
                # create the edge triangles along the top row
                if i == 0:
                    for col in range(len(pts[-1]) - 1):
                        pt1 = pts[0][col]
                        pt2 = pts[0][col + 1]
                        base1 = basePts[0][col]
                        base2 = basePts[0][col + 1]
                        color1 = vertexColors[0][col]
                        color2 = vertexColors[0][col + 1]
                        
                        if bottomFaceDegenerate:
                            if (pt1 is not None and pt2 is not None):
                                stl.write_tri(MeshTri([pt1, pt2, base1], \
                                              color1))
                        else:
                            if pt1 is None:
                                if pt2 is not None:
                                    stl.write_tri(MeshTri([pt2, base2, \
                                                  base1], color2))
                            elif pt2 is None:
                                stl.write_tri(MeshTri([pt1, base2, base1], \
                                              color1))
                            else:
                                stl.write_tri(MeshTri([pt1, pt2, base1], \
                                              color2))
                                stl.write_tri(MeshTri([pt2, base2, base1], \
                                              color2))
                
                # create the edge triangles along the bottom row
                if i == face.resolution1:
                    for col in range(len(pts[-1]) - 1):
                        pt1 = pts[-1][col]
                        pt2 = pts[-1][col + 1]
                        base1 = basePts[-1][col]
                        base2 = basePts[-1][col + 1]
                        color1 = vertexColors[-1][col]
                        color2 = vertexColors[-1][col + 1]
                        
                        if bottomFaceDegenerate:
                            if pt1 is not None and pt2 is not None:
                                stl.write_tri(MeshTri([pt1, base1, pt2], \
                                              color1))
                        else:
                            if pt1 is None:
                                if pt2 is not None:
                                    stl.write_tri(MeshTri([pt2, base1, \
                                                  base2], color2))
                            elif pt2 is None:
                                stl.write_tri(MeshTri([pt1, base1, base2], \
                                              color1))
                            else:
                                stl.write_tri(MeshTri([pt1, base1, pt2], \
                                              color2))
                                stl.write_tri(MeshTri([pt2, base1, base2], \
                                              color2))
