import pandas as pd
import PyPDF2
import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation
from .models import JournalEntry, ProcessingLog

class FileProcessor:
    def __init__(self, uploaded_file, project=None):
        self.uploaded_file = uploaded_file
        self.project = project
        self.entries_created = 0
        
    def log(self, message, level='info'):
        ProcessingLog.objects.create(
            uploaded_file=self.uploaded_file,
            message=message,
            level=level
        )
    
    def process(self):
        try:
            self.uploaded_file.status = 'processing'
            self.uploaded_file.save()
            
            if self.uploaded_file.file_type == 'pdf':
                self.process_pdf()
            elif self.uploaded_file.file_type == 'txt':
                self.process_txt()
            elif self.uploaded_file.file_type == 'csv':
                self.process_csv()
            elif self.uploaded_file.file_type == 'excel':
                self.process_excel()
            
            self.uploaded_file.status = 'completed'
            self.uploaded_file.processed_entries_count = self.entries_created
            self.uploaded_file.processed_at = datetime.now()
            self.log(f"Processing completed. Created {self.entries_created} journal entries.")
            
        except Exception as e:
            self.uploaded_file.status = 'failed'
            self.uploaded_file.error_message = str(e)
            self.log(f"Processing failed: {str(e)}", level='error')
        
        finally:
            self.uploaded_file.save()
    
    def process_pdf(self):
        with open(self.uploaded_file.file.path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        
        # Simple text processing - you can enhance this based on your PDF format
        lines = text.split('\n')
        self.log(f"Extracted {len(lines)} lines from PDF")
        
        # Process each line looking for journal entry patterns
        for line in lines:
            if self.parse_journal_line(line.strip()):
                self.entries_created += 1
    
    def process_txt(self):
        with open(self.uploaded_file.file.path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        self.log(f"Processing {len(lines)} lines from text file")
        
        for line in lines:
            if self.parse_journal_line(line.strip()):
                self.entries_created += 1
    
    def process_csv(self):
        df = pd.read_csv(self.uploaded_file.file.path)
        self.log(f"Processing CSV with {len(df)} rows")
        
        for index, row in df.iterrows():
            if self.create_entry_from_row(row, index + 1):
                self.entries_created += 1
    
    def process_excel(self):
        df = pd.read_excel(self.uploaded_file.file.path)
        self.log(f"Processing Excel with {len(df)} rows")
        
        for index, row in df.iterrows():
            if self.create_entry_from_row(row, index + 1):
                self.entries_created += 1
    
    def create_entry_from_row(self, row, row_number):
        try:
            # Map common column names (you can customize this mapping)
            column_mapping = {
                'title': ['title', 'description', 'memo', 'reference'],
                'amount': ['amount', 'value', 'total', 'sum'],
                'date': ['date', 'transaction_date', 'entry_date'],
                'account': ['account', 'account_name', 'account_number'],
                'type': ['type', 'entry_type', 'debit_credit', 'dr_cr'],
                'reference': ['reference', 'ref', 'ref_number', 'transaction_id']
            }
            
            # Find matching columns
            data = {}
            for field, possible_names in column_mapping.items():
                for name in possible_names:
                    for col in row.index:
                        if name.lower() in col.lower():
                            data[field] = row[col]
                            break
                    if field in data:
                        break
            
            # Create journal entry
            if 'amount' in data and 'date' in data:
                entry = JournalEntry(
                    project=self.project,
                    user=self.uploaded_file.user,
                    title=str(data.get('title', f'Entry from {self.uploaded_file.original_filename}')),
                    amount=abs(Decimal(str(data['amount']))),
                    date=pd.to_datetime(data['date']).date(),
                    account_name=str(data.get('account', 'General')),
                    entry_type='debit' if str(data.get('type', '')).lower().startswith('d') else 'credit',
                    reference_number=str(data.get('reference', ''))
                )
                entry.save()
                return True
            
        except Exception as e:
            self.log(f"Error processing row {row_number}: {str(e)}", level='warning')
        
        return False
    
    def parse_journal_line(self, line):
        # Simple parser for text lines - customize based on your format
        # Example format: "2023-12-01 | Sales Revenue | 1000.00 | Credit"
        try:
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 4:
                    date_str, title, amount_str, entry_type = parts[:4]
                    
                    entry = JournalEntry(
                        project=self.project,
                        user=self.uploaded_file.user,
                        title=title,
                        amount=abs(Decimal(amount_str)),
                        date=datetime.strptime(date_str, '%Y-%m-%d').date(),
                        account_name='General',
                        entry_type='debit' if entry_type.lower().startswith('d') else 'credit'
                    )
                    entry.save()
                    return True
        except Exception as e:
            self.log(f"Error parsing line '{line}': {str(e)}", level='warning')
        
        return False