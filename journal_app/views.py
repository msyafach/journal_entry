from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import JournalEntry, UploadedFile, Project
from .forms import FileUploadForm, JournalEntryForm
from .file_processors import FileProcessor
from .serializers import (
    JournalEntrySerializer, UploadedFileSerializer, 
    ProjectSerializer, ProjectCreateSerializer
)
import magic
import threading

class JournalEntryListView(ListView):
    model = JournalEntry
    template_name = 'journal_app/entry_list.html'
    context_object_name = 'entries'
    paginate_by = 20

def upload_file_view(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.save(commit=False)
            uploaded_file.user = request.user if request.user.is_authenticated else None
            uploaded_file.original_filename = uploaded_file.file.name
            uploaded_file.file_size = uploaded_file.file.size
            
            # Determine file type
            file_content = uploaded_file.file.read(1024)
            uploaded_file.file.seek(0)
            file_type = magic.from_buffer(file_content, mime=True)
            
            if 'pdf' in file_type:
                uploaded_file.file_type = 'pdf'
            elif 'text' in file_type:
                uploaded_file.file_type = 'txt'
            elif 'csv' in file_type or uploaded_file.file.name.endswith('.csv'):
                uploaded_file.file_type = 'csv'
            elif 'excel' in file_type or 'spreadsheet' in file_type:
                uploaded_file.file_type = 'excel'
            
            uploaded_file.save()
            
            # Process file in background
            processor = FileProcessor(uploaded_file)
            thread = threading.Thread(target=processor.process)
            thread.start()
            
            messages.success(request, f'File "{uploaded_file.original_filename}" uploaded successfully! Processing in background.')
            return redirect('upload_file')
    else:
        form = FileUploadForm()
    
    recent_uploads = UploadedFile.objects.all()[:10]
    return render(request, 'journal_app/upload.html', {
        'form': form,
        'recent_uploads': recent_uploads
    })

def file_status_view(request, file_id):
    file_obj = get_object_or_404(UploadedFile, id=file_id)
    return JsonResponse({
        'status': file_obj.status,
        'processed_entries': file_obj.processed_entries_count,
        'error_message': file_obj.error_message,
        'logs': [{'message': log.message, 'level': log.level, 'timestamp': log.timestamp} 
                for log in file_obj.logs.all()[:10]]
    })

# API Views
class ProjectListCreateAPI(generics.ListCreateAPIView):
    queryset = Project.objects.all()
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProjectCreateSerializer
        return ProjectSerializer
    
    def perform_create(self, serializer):
        # Set the owner to the current user if authenticated
        if self.request.user.is_authenticated:
            serializer.save(owner=self.request.user)
        else:
            serializer.save()

class ProjectDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    lookup_field = 'id'

class ProjectEntriesAPI(generics.ListAPIView):
    serializer_class = JournalEntrySerializer
    
    def get_queryset(self):
        project_id = self.kwargs['project_id']
        return JournalEntry.objects.filter(project_id=project_id)

@api_view(['POST'])
def add_team_member_api(request, project_id):
    try:
        project = Project.objects.get(id=project_id)
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=user_id)
            project.team_members.add(user)
            return Response({'message': f'User {user.username} added to project'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            
    except Project.DoesNotExist:
        return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
def remove_team_member_api(request, project_id, user_id):
    try:
        project = Project.objects.get(id=project_id)
        user = User.objects.get(id=user_id)
        project.team_members.remove(user)
        return Response({'message': f'User {user.username} removed from project'}, status=status.HTTP_200_OK)
    except Project.DoesNotExist:
        return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class JournalEntryListCreateAPI(generics.ListCreateAPIView):
    queryset = JournalEntry.objects.all()
    serializer_class = JournalEntrySerializer
    
    def get_queryset(self):
        queryset = JournalEntry.objects.all()
        project_id = self.request.query_params.get('project', None)
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset

class UploadedFileListAPI(generics.ListAPIView):
    queryset = UploadedFile.objects.all()
    serializer_class = UploadedFileSerializer

@api_view(['POST'])
def upload_file_api(request):
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    form = FileUploadForm(request.POST, request.FILES)
    if form.is_valid():
        uploaded_file = form.save(commit=False)
        uploaded_file.user = request.user if request.user.is_authenticated else None
        uploaded_file.original_filename = uploaded_file.file.name
        uploaded_file.file_size = uploaded_file.file.size
        
        # Determine file type
        file_content = uploaded_file.file.read(1024)
        uploaded_file.file.seek(0)
        file_type = magic.from_buffer(file_content, mime=True)
        
        if 'pdf' in file_type:
            uploaded_file.file_type = 'pdf'
        elif 'text' in file_type:
            uploaded_file.file_type = 'txt'
        elif 'csv' in file_type:
            uploaded_file.file_type = 'csv'
        elif 'excel' in file_type or 'spreadsheet' in file_type:
            uploaded_file.file_type = 'excel'
        
        uploaded_file.save()
        
        # Process file in background
        processor = FileProcessor(uploaded_file)
        thread = threading.Thread(target=processor.process)
        thread.start()
        
        return Response(UploadedFileSerializer(uploaded_file).data, status=status.HTTP_201_CREATED)
    
    return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)