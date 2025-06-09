from django import forms
from .models import UploadedFile, JournalEntry
import magic

class FileUploadForm(forms.ModelForm):
    class Meta:
        model = UploadedFile
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.txt,.csv,.xlsx,.xls'
            })
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if not file:
            raise forms.ValidationError("No file selected.")
        
        # Check file size (10MB limit)
        if file.size > 10 * 1024 * 1024:
            raise forms.ValidationError("File size cannot exceed 10MB.")
        
        # Check file type
        allowed_types = ['application/pdf', 'text/plain', 'text/csv', 
                        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        'application/vnd.ms-excel']
        
        file_type = magic.from_buffer(file.read(1024), mime=True)
        file.seek(0)  # Reset file pointer
        
        if file_type not in allowed_types:
            raise forms.ValidationError("Unsupported file type. Please upload PDF, TXT, CSV, or Excel files.")
        
        return file

class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = ['title', 'description', 'entry_type', 'amount', 'date', 
                 'account_name', 'reference_number']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }