# documents/admin.py
from django.contrib import admin
from .models import Department, Document

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'full_name', 'created_at', 'status', 'department')
    list_filter = ('status', 'department', 'channel', 'request_type')
    search_fields = ('identifier', 'full_name')
    date_hierarchy = 'created_at'