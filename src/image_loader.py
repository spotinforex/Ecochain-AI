import io
from PIL import Image
import requests
import logging

logging.basicConfig(level = logging.INFO)


def image_reader(image_path:str):
    """
    Function for converting a GCS path (gs://...) into a PIL image.

    Args:
        image_path (str): Path to image (gs://bucket/file.png)

    Returns:
        PIL.Image object or None if failed
    """
    try:
      logging.info("Converting Image In Progress")

      url = image_path
      parts  = url.replace("gs://","").split("/",1)
      bucket_name = parts[0]
      path_to_image = parts[1]

      public_url = f"https://storage.googleapis.com/{bucket_name}/{path_to_image}"
      logging.info(f"Connecting to image URL: {public_url}")
      response = requests.get(public_url)
      image = Image.open(io.BytesIO(response.content))
      logging.info("Image Retrieved Successfully")

      return image

    except requests.exceptions.RequestException as e:
        logging.error(f"Network error while retrieving image: {e}")
        return None

    except UnidentifiedImageError:
        logging.error("The retrieved content is not a valid image")
        return None

    except Exception as e:
        logging.exception(f"Unexpected error: {e}")
        return None

