from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('incoming/', views.incoming_list, name='incoming_list'),
    path('create/', views.create_document, name='create_document'),
    path('incoming/<int:pk>/', views.document_detail, name='document_detail'),

    path('incoming/<int:pk>/add_comment/', views.add_comment, name='add_comment'),
    path('incoming/<int:pk>/update_status/', views.update_status, name='update_status'),
    path('incoming/<int:pk>/update_department/', views.update_department, name='update_department'),
    path('incoming/<int:pk>/close/', views.close_document, name='close_document'),

    path('document/<int:pk>/files/', views.document_files, name='document_files'),
    path('document/<int:pk>/files/upload/', views.upload_file, name='upload_file'),
    path('document/file/<int:pk>/delete/', views.delete_file, name='delete_file'),
    
]