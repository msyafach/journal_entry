from rest_framework import serializers
from django.contrib.auth.models import User
from .models import JournalEntry, UploadedFile, Project

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class ProjectSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    team_members = UserSerializer(many=True, read_only=True)
    total_entries = serializers.ReadOnlyField()
    total_debits = serializers.ReadOnlyField()
    total_credits = serializers.ReadOnlyField()
    net_amount = serializers.ReadOnlyField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'status', 'budget', 
            'start_date', 'end_date', 'owner', 'team_members',
            'total_entries', 'total_debits', 'total_credits', 'net_amount',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ProjectCreateSerializer(serializers.ModelSerializer):
    team_member_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = Project
        fields = [
            'name', 'description', 'status', 'budget', 
            'start_date', 'end_date', 'team_member_ids'
        ]
    
    def create(self, validated_data):
        team_member_ids = validated_data.pop('team_member_ids', [])
        project = Project.objects.create(**validated_data)
        
        if team_member_ids:
            team_members = User.objects.filter(id__in=team_member_ids)
            project.team_members.set(team_members)
        
        return project

class JournalEntrySerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = JournalEntry
        fields = [
            'id', 'project', 'project_name', 'user', 'title', 'description', 
            'entry_type', 'amount', 'date', 'account_name', 'reference_number',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = '__all__'
        read_only_fields = ['id', 'file_type', 'file_size', 'status', 'processed_entries_count']