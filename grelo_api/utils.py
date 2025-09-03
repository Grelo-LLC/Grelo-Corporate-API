import re
import configparser
import hashlib
import random
import requests
from enum import Enum
from types import DynamicClassAttribute
from rest_framework.exceptions import APIException
# from users.models import User
from django.conf import settings
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import base64

config = configparser.ConfigParser()

config.read('grelo_api/messages.env')

class Error(Enum):
    def __init__(self, detail: str):
        self.detail = detail

    INVALID_INPUT = config['messages']['INVALID_INPUT']
    NOT_FOUND = config['messages']['NOT_FOUND']
    INTERNAL_SERVER_ERROR = config['messages']['INTERNAL_SERVER_ERROR']
    NOT_ACCEPTED = config['messages']['NOT_ACCEPTED']
    GATEWAY_TIMEOUT = config['messages']['TIMEOUT']
    ALREADY_EXIST = config['messages']['ALREADY_EXIST']

    @DynamicClassAttribute
    def name(self):
        return super().name.lower()
    
    
class BaseAPIException(APIException):
    def __init__(self, detail: str, status_code: int, code: str = None):
        self.detail = detail
        self.status_code = status_code
        self.code = code


# def email_checker(email):
#     try:
#         user = User.objects.get(email=email)
#         return True
#     except User.DoesNotExist:
#         return False
    

def is_password_valid(password):
    pattern = r"^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}$"
    match = re.match(pattern, password)
    return True if match else False


def is_email_valid(email):
    patterns = r'^(([^<>()\[\]\.,;:\s@\"]+(\.[^<>()\[\]\.,;:\s@\"]+)*)|(\".+\"))@(([^<>()[\]\.,;:\s@\"]+\.)+[^<>()[\]\.,;:\s@\"]{2,})$'
    match = re.match(patterns, email)
    return True if match else False


def generate_password(email):
    conc_string = f'{email}{settings.PASSWORD_SALT}'
    hash_password =  hashlib.sha256(conc_string.encode()).hexdigest()
    return hash_password


def generate_user_otp_token(email):
    return str(random.randint(100000, 999999))


def upload_profile_image_as_base64(profile, image_url):
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            image_io = BytesIO()
            image.save(image_io, format='JPEG')
            base64_image = base64.b64encode(image_io.getvalue()).decode('utf-8')
            profile.profile_image = base64_image
            profile.save()
            return True
        return False
    except Exception as exc:
        return False