from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class CustomBusinessUserManager(BaseUserManager):
    def create_user(self, business_email, password=None, **extra_fields):
        if not business_email:
            raise ValueError('The Business Email field must be set')
        business_email = self.normalize_email(business_email)
        user = self.model(business_email=business_email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, business_email, password=None, **extra_fields):
        extra_fields.setdefault('is_confirmed', True)
        extra_fields.setdefault('is_blocked', False)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('country', 'Unknown')
        return self.create_user(business_email, password, **extra_fields)


class BusinessUser(AbstractBaseUser, PermissionsMixin):
    business_email = models.EmailField(max_length=50, unique=True, db_index=True)
    business_name = models.CharField(max_length=100)
    tax_id = models.CharField(max_length=15, unique=True, verbose_name="VÖEN")
    password = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    is_confirmed = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    active_session_key = models.CharField(max_length=255, null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    groups = models.ManyToManyField('auth.Group', related_name='businessuser_set', blank=True)
    user_permissions = models.ManyToManyField('auth.Permission', related_name='businessuser_permissions', blank=True)

    USERNAME_FIELD = 'tax_id'
    REQUIRED_FIELDS = ['business_name']

    objects = CustomBusinessUserManager()

    def __str__(self):
        return self.business_name

    class Meta:
        verbose_name = 'Biznes İstifadəçisi'
        verbose_name_plural = 'Biznes İstifadəçiləri'


class BusinessUserProfile(models.Model):
    user = models.OneToOneField(BusinessUser, on_delete=models.CASCADE, related_name='profile')
    profile_image = models.TextField(null=True, blank=True)
    phone = models.CharField(max_length=20, verbose_name="Telefon Nömrəsi", null=True, blank=True)
    country = models.CharField(max_length=50, verbose_name="Ölkə", null=True, blank=True)
    state = models.CharField(max_length=50, verbose_name="Əyalət / Bölgə", null=True, blank=True)
    city = models.CharField(max_length=50, verbose_name="Şəhər", null=True, blank=True)
    address_line1 = models.CharField(max_length=255, verbose_name="Ünvan 1", null=True, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True, verbose_name="Ünvan 2 (istəyə bağlı)")
    zip_code = models.CharField(max_length=15, verbose_name="Poçt Kodu", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Əlavə olunma tarixi")

    def __str__(self):
        return self.user.business_email

    class Meta:
        verbose_name = 'Biznes İstifadəçi Profili'
        verbose_name_plural = 'Biznes İstifadəçi Profilləri'
        
        
class OTPToken(models.Model):
    user = models.ForeignKey(BusinessUser, on_delete=models.CASCADE, related_name='otp_tokens')
    otp = models.CharField(max_length=250)
    created_time = models.DateTimeField(auto_now_add=True)
    is_expired = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    
    def __str__(self):
        return f"OTP for {self.user.business_email} - {self.otp}"
    
    class Meta:
        verbose_name = 'OTP Token'
        verbose_name_plural = 'OTP Tokens'