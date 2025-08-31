import os
import sys
import json
from sstl_math import *
from sstl_image import *
from sstl_shapes import *
from sstl_stl import *

def get_param(params, key):
    if key in params:
        return params[key]
    else:
        sys.exit("parameter " + str(key) + " missing from params.json")

def create_stls():
    try:
        paramsFile = open("params.json", 'r')
    except:
        sys.exit("Could not open parameter file params.json")

    params = json.load(paramsFile)
    paramsFile.close()

    path = os.path.expanduser(get_param(params, "outputPath"))
    name = get_param(params, "fileName")

    if (len(get_param(params, "depthImages"))
            != len(get_param(params, "depthImageWeights"))):
       sys.exit("depthImages and depthImageWeights are different lengths")

    if (len(get_param(params, "depthImages")) > 1):
        img = StackedImageWrapper(get_param(params, "depthImages"),
            get_param(params, "depthImageWeights"),
            get_param(params, "holeImage"),
            get_param(params, "colorImage"))
       
    else:
        img = ImageWrapper(get_param(params, "depthImages")[0],
            get_param(params, "holeImage"), get_param(params, "colorImage"))

    if params["solid"] == "sphere":
        solidParams = get_param(params, "sphereParams")
        
        if get_param(solidParams, "projection") not in projections:
            sys.exit("sphere projection was neither 'equirectangular' nor" + \
                     " 'cylindrical'")
        
        faces = get_param(solidParams, "faces")
        
        if isinstance(faces, str) and (faces in faceShapes):
            faces = faceShapes[faces]
            
        elif not isinstance(faces, dict):
            sys.exit("faces is not a built-in polyhedron or properly" + \
                     " formatted object")
        
        assembledFaces = []
        normalizeFaceVertices = True
        
        try:
            normalizeFaceVertices = faces["normalize"]
            
            for i in range(len(faces["pts"])):
               faces["pts"] = [tuple(pt) for pt in faces["pts"]]
           
            for quad in faces["quads"]:
                assembledFaces.append( \
                    QuadFace([faces["pts"][i] for i in quad],
                    get_param(solidParams, "resolution1"),
                    get_param(solidParams, "resolution2"),
                    get_param(solidParams, "flatBottomFaces"),
                    get_param(solidParams, "flatTopFaces")))
                
            for tri in faces["tris"]:
                assembledFaces.append(TriFace([faces["pts"][i] for i in tri],
                    get_param(solidParams, "resolution1"),
                    get_param(solidParams, "flatBottomFaces"),
                    get_param(solidParams, "flatTopFaces")))
        except:
            sys.exit("faces is not a properly formatted object")
            
        rotation = get_param(solidParams, "rotation")
        
        rotationMode = get_param(solidParams, "rotationMode")
        
        if (rotationMode not in validExtrinsics) and \
                (rotationMode not in validIntrinsics):
            sys.exit("rotationMode was not a valid triple of axes")
        
        if isinstance(rotation, list) and (len(rotation) == 3):
            rotation = Rotation.from_euler(rotationMode, rotation,
                True).as_matrix()
        elif rotation != None:
            sys.exit("rotation was not an array of 3 numbers" + \
                " (euler angles) nor null")
        
        scale = get_param(solidParams, "scale")
        
        if not (isinstance(scale, list) and (len(scale) == 3)) \
                and (scale != None):
            sys.exit("scale was not an array of 3 numbers (euler angles)" + \
                " nor null")
        
        solid = Sphere(img, projections[get_param(solidParams, "projection")],
            assembledFaces, normalizeFaceVertices,
            get_param(solidParams, "minAltitude"),
            get_param(solidParams, "maxAltitude"),
            get_param(solidParams, "lowCutoff"), rotation,
            get_param(solidParams, "scale"))
        
    elif params["solid"] == "prism":
        solidParams = get_param(params, "prismParams")
        solid = Prism(img, get_param(solidParams, "width"),
            get_params(solidParams, "height"),
            get_param(solidParams, "resolutionX"),
            get_param(solidParams, "resolutionY"),
            get_param(solidParams, "minAltitude"),
            get_param(solidParams, "maxAltitude"))
       
    else:
        sys.exit("solid was not a valid value (either 'sphere' or 'prism')")

    try:
       os.mkdir(path)
    except FileExistsError:
       if not os.path.isdir(path):
           sys.exit("Specified output path was a file, not a path")
    except FileNotFoundError:
       sys.exit("Could not create output path" + \
                " (parent directory does not exist)")
    except:
       sys.exit("Could not create output path")

    colorMode = get_param(params, "colorMode")

    if get_param(params, "colorImage") == None:
        colorMode = None

    if isinstance(solid, Sphere):
        for faceNum in range(len(solid.faces)):
            face = solid.faces[faceNum]
            print("writing sphere face " + str(faceNum))
           
            stl = STLFileWrapper(os.path.join(path, name + "_" + \
                str(faceNum) + ".stl"), colorMode)
            write_mesh_tris(solid, stl, face)
            
            stl.close()
            faceNum += 1
            
    elif isinstance(solid, Prism):
        stl = STLFileWrapper(os.path.join(path, name + ".stl"))
        write_mesh_tris(solid, stl)
        stl.close()

if __name__ == "__main__":
    create_stls()
