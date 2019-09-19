from PIL import Image
import piexif
import os
import math
import re
from datetime import datetime
import json
import boto3

def lambda_handler(event, context):
  s3 = boto3.resource('s3')

  sizes = os.environ['sizes'].split(',')
  s3_event = event['Records'][0]['s3']
  bucket = s3_event['bucket']['name']
  obj_key = str(s3_event['object']['key'])
  filename = obj_key.split('/')[1]
  
  org_tmp_file = '/tmp/{}.jpg'.format(re.sub(r'[\.:\s-]', '', str(datetime.now())))
  with open(org_tmp_file, 'wb') as data:
    # pull down original
    s3.Bucket(bucket).download_fileobj(obj_key, data)
    
  for size in sizes:
    tw = int(size.split('x')[0].strip())
    th = int(size.split('x')[1].strip())
    tmp_file = '{}{}{}.jpg'.format(org_tmp_file.split('.')[0], tw, th)

    image = Image.open(org_tmp_file)
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
      resized_img.save(tmp_file)

      # crop center for "cover" effect
      left = (resized_w - tw) / 2
      top = (resized_h - th) / 2
      right = resized_w - left
      bottom = resized_h - top
      rect = (math.ceil(left), math.ceil(top), math.ceil(right), math.ceil(bottom))
      crop_img = resized_img.crop(rect)
      crop_img.format = image_format
      crop_img.save(tmp_file)

    else:
      print('requested size is too large')

    # upload smaller image to new bucket
    s3.Bucket(bucket).upload_file(tmp_file, '{}/{}'.format(size.strip(), filename))
     
  return {
      'statusCode': 200,
      'body': 'done'
  }
  
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

