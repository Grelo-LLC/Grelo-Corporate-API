from rest_framework import serializers
from users.models import BusinessUser, BusinessUserProfile
import base64
from django.core.files.base import ContentFile
import uuid
from PIL import Image
from io import BytesIO


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            file_name = f"{uuid.uuid4()}.{ext}"
            data = ContentFile(base64.b64decode(imgstr), name=file_name)
        return super().to_internal_value(data)


class BusinessUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessUser
        fields = '__all__'
    
    

class BusinessUserProfileSerializer(serializers.ModelSerializer):
    profile_image = serializers.CharField(required=False, allow_blank=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = BusinessUserProfile
        fields = [
            'user', 'profile_image', 'phone', 'country', 'state', 'city', 'address_line1', 'address_line2', 'zip_code',
        ]
    
    def resize_image(self, image_field, size, max_size_mb=1):
        if not image_field:
            return None
        try:
            if hasattr(image_field, 'read'):
                raw_data = image_field.read()
            elif isinstance(image_field, str):
                if "," in image_field:
                    image_field = image_field.split(",")[1]
                raw_data = base64.b64decode(image_field)
            else:
                return None

            img = Image.open(BytesIO(raw_data))
            img = img.convert("RGB")
            img.thumbnail(size)

            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            buffer_size = buffer.tell()

            if buffer_size > max_size_mb * 1024 * 1024:
                quality = int(85 * (max_size_mb * 1024 * 1024 / buffer_size))
                quality = max(20, min(quality, 85))
                buffer = BytesIO()
                img.save(buffer, format="JPEG", quality=quality)

            buffer.seek(0)
            return f"{base64.b64encode(buffer.read()).decode('utf-8')}"

        except Exception as e:
            print("Resize error:", e)
            return None
    
    def validate_profile_image(self, value):
        return self.resize_image(value, (600, 600))