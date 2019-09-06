from PIL import Image
import piexif
import math

def is_big_enough(image, size):
  # Check that the image's size is superior to `size`
  return True if (image.size[0] > size[0]) and (image.size[1] > size[1]) else False
  
def rotate_img(image):
  # rotate samsung images *sigh*
  if ('exif' in image.info):
    exif = piexif.load(image.info['exif'])
    if (('0th' in exif) and len(exif['0th']) and (piexif.ImageIFD.Orientation in exif['0th'])):
      orient = exif['0th'][piexif.ImageIFD.Orientation]
      if (orient == 8):
        image = image.rotate(90)
      elif (orient == 3):
        image = image.rotate(180)
      elif (orient == 6):
        image = image.rotate(270)
    return image

# (200, 200)
tw, th = (200, 200)

image = Image.open('./cat.jpg')
image_format = image.format
image = rotate_img(image)
w, h = image.size
print('Original: {} x {}'.format(w, h))
print('Target: {} x {}'.format(tw, th))

# resize and crop
if (is_big_enough(image, (tw, th))):

  # create copy
  img = image.copy()
  img.format = image_format

  # resize smallest dimension to target dimension while maintaining aspect ratio
  # (largest target/actual)
  ratio = max((tw / w), (th / h))
  resized_w = int(math.ceil(ratio * w))
  resized_h = int(math.ceil(ratio * h))
  print('Resized: {} x {}'.format(resized_w, resized_h))
  resized_img = img.resize((resized_w, resized_h), Image.LANCZOS)
  resized_img.format = image_format
  resized_img.save('./resizedPhoto.jpg')

  # crop center for "cover" effect
  left = (resized_w - tw) / 2
  top = (resized_h - th) / 2
  right = resized_w - left
  bottom = resized_h - top
  rect = (math.ceil(left), math.ceil(top), math.ceil(right), math.ceil(bottom))
  crop_img = resized_img.crop(rect)
  crop_img.format = image_format
  crop_img.save('./thumbnail.jpg')

else:
  # return original image
  print('requested size is too large; returning original')

