from django.core.management.base import BaseCommand
from journal_app.models import UploadedFile
from journal_app.file_processors import FileProcessor

class Command(BaseCommand):
    help = 'Process pending uploaded files'

    def handle(self, *args, **options):
        pending_files = UploadedFile.objects.filter(status='pending')
        
        for file_obj in pending_files:
            self.stdout.write(f'Processing {file_obj.original_filename}...')
            processor = FileProcessor(file_obj)
            processor.process()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully processed {file_obj.original_filename}')
            )