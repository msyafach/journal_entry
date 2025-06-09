from django.urls import path
from . import views

urlpatterns = [
    path('', views.JournalEntryListView.as_view(), name='entry_list'),
    path('upload/', views.upload_file_view, name='upload_file'),
    path('file-status/<uuid:file_id>/', views.file_status_view, name='file_status'),
    
    # API endpoints - Projects
    path('api/projects/', views.ProjectListCreateAPI.as_view(), name='api_projects'),
    path('api/projects/<uuid:id>/', views.ProjectDetailAPI.as_view(), name='api_project_detail'),
    path('api/projects/<uuid:project_id>/entries/', views.ProjectEntriesAPI.as_view(), name='api_project_entries'),
    path('api/projects/<uuid:project_id>/team/add/', views.add_team_member_api, name='api_add_team_member'),
    path('api/projects/<uuid:project_id>/team/<int:user_id>/remove/', views.remove_team_member_api, name='api_remove_team_member'),
    
    # API endpoints - Journal Entries
    path('api/entries/', views.JournalEntryListCreateAPI.as_view(), name='api_entries'),
    
    # API endpoints - File Uploads
    path('api/upload/', views.upload_file_api, name='api_upload'),
    path('api/files/', views.UploadedFileListAPI.as_view(), name='api_files'),
]