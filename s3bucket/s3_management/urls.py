from django.urls import path
from . import views

urlpatterns = [
    # URL for creating a bucket
    path('', views.create_bucket, name='create_bucket'),

    # URL for listing buckets
    path('list_buckets/', views.list_buckets, name='list_buckets'),

    # URL for deleting a bucket (passing the bucket name as a parameter)
    path('delete_bucket/', views.delete_bucket, name='delete_bucket'),

    #URL for uploading a file to a bucket
    path('upload_file/',views.upload_file, name='upload_file'),

    path('delete_files/',views.delete_files,name='delete_files'),

    path('list_files/',views.list_files,name='list_files'),

    path('copy_files/',views.copy_files,name='copy_files'),

    path('move_files/',views.move_files,name='move_files'),

    path('create_folder/',views.create_folder,name='create_folder')
]