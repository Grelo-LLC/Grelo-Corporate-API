from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import BusinessUser, BusinessUserProfile, OTPToken


@admin.register(BusinessUserProfile)
class BusinessUserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'country', 'city', 'zip_code')
    search_fields = [
        'user__business_email', 'user__business_name',
        'phone', 'country', 'state', 'city',
        'address_line1', 'address_line2', 'zip_code'
    ]


@admin.register(BusinessUser)
class BusinessUserAdmin(BaseUserAdmin):
    ordering = ('-created_date',)
    list_display = ('business_email', 'business_name', 'tax_id', 'is_active', 'is_superuser')
    search_fields = ('business_email', 'business_name', 'country', 'tax_id')
    list_filter = ()

    fieldsets = (
        (None, {'fields': ('business_name', 'business_email', 'tax_id', 'password', 'country')}),
        (_('Status'), {'fields': ('is_confirmed', 'is_blocked')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'business_name', 'business_email', 'tax_id',
                'password1', 'password2',
                'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'
            ),
        }),
    )
    
    
@admin.register(OTPToken)
class OTPTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp', 'is_expired', 'is_approved')
    search_fields = ('user__business_email', 'otp')