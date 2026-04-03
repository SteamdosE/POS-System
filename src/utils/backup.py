"""
Database Backup and Recovery Module
"""
import shutil
import os
from datetime import datetime
import json

class BackupManager:
    """Manage database backups and recovery"""
    
    def __init__(self, db_path='pos_system.db', backup_dir='backups'):
        self.db_path = db_path
        self.backup_dir = backup_dir
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
    
    def create_backup(self):
        """Create database backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_{timestamp}.db"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        try:
            shutil.copy2(self.db_path, backup_path)
            return {
                'success': True,
                'message': f'Backup created: {backup_name}',
                'path': backup_path,
                'timestamp': timestamp
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Backup failed: {str(e)}'
            }
    
    def restore_backup(self, backup_filename):
        """Restore from backup"""
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        if not os.path.exists(backup_path):
            return {
                'success': False,
                'message': f'Backup file not found: {backup_filename}'
            }
        
        try:
            # Create safety backup of current database
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safety_backup = os.path.join(self.backup_dir, f"safety_backup_{timestamp}.db")
            if os.path.exists(self.db_path):
                shutil.copy2(self.db_path, safety_backup)
            
            # Restore backup
            shutil.copy2(backup_path, self.db_path)
            
            return {
                'success': True,
                'message': f'Database restored from {backup_filename}',
                'safety_backup': safety_backup
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Restore failed: {str(e)}'
            }
    
    def list_backups(self):
        """List all available backups"""
        try:
            backups = []
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.db'):
                    filepath = os.path.join(self.backup_dir, filename)
                    size = os.path.getsize(filepath)
                    mtime = os.path.getmtime(filepath)
                    mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                    
                    backups.append({
                        'filename': filename,
                        'size': size,
                        'size_mb': round(size / (1024*1024), 2),
                        'date': mtime_str,
                        'path': filepath
                    })
            
            return sorted(backups, key=lambda x: x['date'], reverse=True)
        except Exception as e:
            return []
    
    def export_json(self, output_file='export.json'):
        """Export database data to JSON"""
        # This would require database access
        # Simplified example
        try:
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'source': 'POS System Database Export'
            }
            
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            return {
                'success': True,
                'message': f'Data exported to {output_file}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Export failed: {str(e)}'
            }
    
    def auto_backup(self):
        """Auto backup (run this periodically)"""
        return self.create_backup()
