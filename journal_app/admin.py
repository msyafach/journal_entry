from django.contrib import admin
from .models import JournalEntry, UploadedFile, ProcessingLog, Project

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'owner', 'budget', 'start_date', 'end_date', 'created_at']
    list_filter = ['status', 'created_at', 'start_date']
    search_fields = ['name', 'description']
    filter_horizontal = ['team_members']
    readonly_fields = ['total_entries', 'total_debits', 'total_credits', 'net_amount']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'status')
        }),
        ('Financial', {
            'fields': ('budget',)
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date')
        }),
        ('Team', {
            'fields': ('owner', 'team_members')
        }),
        ('Statistics', {
            'fields': ('total_entries', 'total_debits', 'total_credits', 'net_amount'),
            'classes': ('collapse',)
        })
    )

@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'amount', 'entry_type', 'date', 'account_name', 'created_at']
    list_filter = ['entry_type', 'date', 'created_at', 'project']
    search_fields = ['title', 'account_name', 'reference_number', 'project__name']
    date_hierarchy = 'date'
    raw_id_fields = ['project']

@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'file_type', 'status', 'processed_entries_count', 'uploaded_at']
    list_filter = ['file_type', 'status', 'uploaded_at']
    search_fields = ['original_filename']
    readonly_fields = ['file_size', 'processed_entries_count', 'processed_at']

@admin.register(ProcessingLog)
class ProcessingLogAdmin(admin.ModelAdmin):
    list_display = ['uploaded_file', 'level', 'message', 'timestamp']
    list_filter = ['level', 'timestamp']
    search_fields = ['message']