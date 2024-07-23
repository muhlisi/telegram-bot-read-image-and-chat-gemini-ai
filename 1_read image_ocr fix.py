from google.oauth2 import service_account
from google.cloud import vision
import re

# create vision client first
credentials = service_account.Credentials.from_service_account_file('client_id_bro_google_vision.json')
client = vision.ImageAnnotatorClient(credentials=credentials)

# open image
file = 'testocr.png'
content = open(file, 'rb').read()

# read text on image
image = vision.Image(content=content)
response = client.text_detection(image=image)
text = response.text_annotations[0].description.strip()

# get lat
lat = re.search(r"^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?)", text)
lon = re.search(r"^[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)", text)

if lat is None or lon is None:
    print('tidak ditemukan lat atau long.')
else:
    print(lat.group())
    print(lon.group())
    print(text)
