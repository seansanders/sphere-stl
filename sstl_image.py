import sys
from PIL import Image
from sstl_math import *

Image.MAX_IMAGE_PIXELS = 268435456

IMAGE_MODES_TO_CONVERT = ('P', 'CMYK, YcbCr, LAB, HSV')
IMAGE_MODES_TO_CONVERT_ALPHA = ('PA')
PIXEL_MAXES = {'1': 1, 'L': 255, 'LA': 255, 'RGB': 255, 'RGBA': 255}

def rgb_to_luma(rgb):
    """
    Converts rgb tuple to luma value based on PIL calculation here: 
    https://pillow.readthedocs.io/en/stable/reference/Image.html
    """
    
    return (rgb[0] * 299 + rgb[1] * 587 + rgb[2] * 114) / 1000

class ImageWrapper():
    """
    Contains a height map image, and optionally, an image to act as an
    "alpha channel" (determines where there are holes all the way through
    the mesh) If the base image contains an alpha channel, it will also
    determine hole positions (in logical AND with the "alpha" image).
    The threshold for holes is < 0.5 (of maximum alpha for the base image,
    and of maximum luma for the "alpha" image).
    
    Color images are not converted to monochrome in order to maintain full
    precision, though using a color image as a height map is
    kind of confusing...
    """
    
    def __init__(self, imgPath, alphaPath=None, colorPath=None):
        """
        Opens and prepares images to be used for height map
        
        Arguments:
        imgPath -- Path to the base heightmap image. The image must be of PIL
                   type 1, L, LA, RGB, RGBA, P, PA, CMYK, YcbCr, LAB, or HSV,
                   and if it is a type with an alpha channel, it will
                   contribute to hole placement.
        alphaPath -- Path to image that must be one of the same allowable types
                     as for imgPath. Determines hole locations (if luma under
                     half the image maximum at a point, it is a hole). If this
                     image has an alpha channel, it is ignored ("alpha" is 
                     only sourced from image luma.)
        """
        
        try:
            self.img = Image.open(imgPath)
        except:
            print("Error: failed to open image at " + imgPath)
        
        if self.img.mode in IMAGE_MODES_TO_CONVERT:
            self.img = self.img.convert('RGB')
        elif self.img.mode in IMAGE_MODES_TO_CONVERT_ALPHA:
            self.img = self.img.convert('RGBA')
        
        if not (self.img.mode in PIXEL_MAXES):
            sys.exit("Error: image at " + imgPath + "is an unsupported mode, "
                     + self.img.mode)
        
        self.alpha = None
        
        if alphaPath is not None:
            try:
                self.alpha = Image.open(alphaPath)
            except:
                print("Error: failed to open image at " + alphaPath)
            
            self.alpha = self.alpha.convert('L')
        
        self.color = None
        
        if colorPath is not None:
            try:
                self.color = Image.open(colorPath)
            except:
                print("Error: failed to open image at " + colorPath)
            
            self.color = self.color.convert('RGB')
    
    def depth_luma_at_pixel(self, loc):
        """Returns the luma value at the pixel coordinates in loc."""
        
        if self.img.mode == 'RGB' or self.img.mode == 'RGBA':
            return rgb_to_luma(self.img.getpixel(loc)) \
                / PIXEL_MAXES[self.img.mode]
        elif self.images[img].mode == 'LA':
            return self.img.getpixel(loc)[0] / PIXEL_MAXES[self.img.mode]
        else: #L
            return self.img.getpixel(loc) / PIXEL_MAXES[self.img.mode]
    
    def height_at_loc(self, loc):
        """
        Returns the height (luma value) at the coordinates in loc
        (range [0, 1])
        """
        
        size = self.img.size
        x = floor(loc[0] * size[0]) % size[0]
        y = min(floor(loc[1] * size[1]), nextafter(size[1], -inf))
        return self.depth_luma_at_pixel((x, y))
    
    def hole_at_loc(self, loc):
        """
        Returns whether there is a hole at the coordinates in loc
        (range [0, 1]), determined by the alpha channel in self.img
        and the luma in alphaImg, if present (if either is below 0.5
        times its maximum value.)
        """
        
        alphaImgAlpha = 1
        baseImgAlpha = 1
        
        size = self.img.size
        x = floor(loc[0] * size[0]) % size[0]
        y = min(floor(loc[1] * size[1]), nextafter(size[1], -inf))
        
        if self.img.mode == 'LA':
            baseImgAlpha = self.img.getpixel((x,y))[1] \
                           / PIXEL_MAXES[self.img.mode]
        elif self.img.mode == 'RGBA':
            baseImgAlpha = self.img.getpixel((x,y))[3]  \
                           / PIXEL_MAXES[self.img.mode]
        
        if self.alpha is not None:
            size = self.alpha.size
            x = floor(loc[0] * size[0]) % size[0]
            y = min(floor(loc[1] * size[1]), nextafter(size[1], -inf))
            
            alphaImgAlpha = self.alpha.getpixel((x,y)) \
                            / PIXEL_MAXES[self.alpha.mode] 
        
        return alphaImgAlpha < 0.5 or baseImgAlpha < 0.5
    
    def color_at_loc(self, loc):
        if self.color == None:
            return None
        else:
            size = self.color.size
            x = floor(loc[0] * size[0]) % size[0]
            y = min(floor(loc[1] * size[1]), nextafter(size[1], -inf))
            return self.color.getpixel((x,y))
             
class StackedImageWrapper(ImageWrapper):
    """
    Works the same as ImageWrapper, but with height values as a weighted
    average of multiple images' lumas (allowing greater precision
    from standard 8-bit images).
    """
    
    def __init__(self, imgPaths, weights, alphaPath=None, colorPath=None):
        """
        Opens and prepares images to be used for height map
        
        Arguments:
        imgPaths -- Paths to the base heightmap images. The images must be of
                    the same allowable PIL types as for imgPath
                    in ImageWrapper.
        weights -- Float list which must be the same length as imgPaths.
                   Each element is the relative contribution of each image from
                   imgPaths to the heightmap.
        alphaPath -- Path to image that must be one of the same allowable types
                     as for imgPaths. Determines hole locations (if luma under
                     half the image maximum at a point, it is a hole). If this
                     image has an alpha channel, it is ignored ("alpha" is
                     only sourced from image luma.)
        """
        
        if len(imgPaths) != len(weights):
            sys.exit("""Error: imgPaths and weights for StackedImageWrapper
                        are different lenghths""")
        
        self.images = []
        self.weights = weights
        self.totalWeight = sum(weights)
        
        for imgPath in imgPaths:
            try:
                img = Image.open(imgPath)
            except:
                print("Error: failed to open image at " + imgPath)
            
            if img.mode in IMAGE_MODES_TO_CONVERT:
                img = img.convert('RGB')
            elif img.mode in IMAGE_MODES_TO_CONVERT_ALPHA:
                img = img.convert('RGBA')
            
            if img.mode in PIXEL_MAXES:
                self.images.append(img)
            else:
                sys.exit("Error: image at " + imgPath
                         + "is an unsupported mode, " + img.mode)
        
        self.alpha = None
        
        if alphaPath is not None:
            try:
                self.alpha = Image.open(alphaPath)
            except:
                print("Error: failed to open image at " + alphaPath)
            
            self.alpha = self.alpha.convert('L')
        
        self.color = None
        
        if colorPath is not None:
            try:
                self.color = Image.open(colorPath)
            except:
                print("Error: failed to open image at " + colorPath)
            
            self.color = self.color.convert('RGB')
        
    def depth_luma_at_pixel(self, loc, img):
        """
        Returns the luma value at the pixel coordinates in loc in
        the image at index img in self.images.
        """
        
        if self.images[img].mode == 'RGB' or self.images[img].mode == 'RGBA':
            return rgb_to_luma(self.images[img].getpixel(loc)) \
                   / PIXEL_MAXES[self.images[img].mode]
        elif self.images[img].mode == 'LA':
            return self.images[img].getpixel(loc)[0] \
                   / PIXEL_MAXES[self.images[img].mode]
        else: # L
            return self.images[img].getpixel(loc) \
                   / PIXEL_MAXES[self.images[img].mode]    
    
    def height_at_loc(self, loc):
        """
        Returns the height (luma value from the weighted sum of images) at
        the coordinates in loc (range [0, 1])
        """
        
        height = 0
        
        for i in range(len(self.images)):
            size = self.images[i].size
            x = floor(loc[0] * size[0]) % size[0]
            y = min(floor(loc[1] * size[1]), nextafter(size[1], -inf))
            height += self.depth_luma_at_pixel((x, y), i) * self.weights[i]
        
        return height / self.totalWeight
    
    def hole_at_loc(self, loc):
        """
        Returns whether there is a hole at the coordinates in loc
        (range [0, 1]), determined by a weighted average of the the alpha
        channels in self.images and the luma in alphaImg, if present (if
        either is below 0.5 times its maximum value.)
        """
        
        alphaImgAlpha = 1
        baseImgsAlpha = 0
        
        if self.alpha is not None:
            size = self.alpha.size
            x = floor(loc[0] * size[0]) % size[0]
            y = min(floor(loc[1] * size[1]), nextafter(size[1], -inf))
            
            alphaImgAlpha = self.alpha.getpixel((x,y)) \
            / PIXEL_MAXES[self.alpha.mode] 
        
        for i in range(len(self.images)):
            img = self.images[i]
            
            size = img.size
            x = floor(loc[0] * size[0]) % size[0]
            y = min(floor(loc[1] * size[1]), nextafter(size[1], -inf))
            
            if img.mode == 'LA':
                baseImgsAlpha += img.getpixel((x,y))[1] * self.weights[i] \
                / PIXEL_MAXES[img.mode]
            elif img.mode == 'RGBA':
                baseImgsAlpha += img.getpixel((x,y))[3] \
                * self.weights[i] / PIXEL_MAXES[img.mode]
            else:
                baseImgsAlpha += self.weights[i]
        
        return alphaImgAlpha < 0.5 or baseImgsAlpha / self.totalWeight < 0.5
