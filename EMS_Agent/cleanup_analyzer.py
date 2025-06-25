#!/usr/bin/env python3
"""
EMS Agent - File Cleanup Script
Identifies and removes useless/redundant files to optimize the project
"""

import os
import glob
import shutil
from pathlib import Path
from typing import List, Dict
import json

class EMSFileCleanup:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.removed_files = []
        self.analysis_report = {
            'system_files': [],
            'backup_files': [],
            'temp_files': [],
            'redundant_files': [],
            'test_files': [],
            'documentation_duplicates': [],
            'large_files': [],
            'total_space_saved': 0
        }
    
    def analyze_project_files(self):
        """Analyze all files in the project for cleanup opportunities"""
        print("🔍 Analyzing EMS Agent project files...")
        print("=" * 60)
        
        # 1. Find system files (.DS_Store, Thumbs.db, etc.)
        self._find_system_files()
        
        # 2. Find backup files
        self._find_backup_files()
        
        # 3. Find temporary files
        self._find_temp_files()
        
        # 4. Find potentially redundant files
        self._find_redundant_files()
        
        # 5. Find test files that might be outdated
        self._find_test_files()
        
        # 6. Find large files that might be unnecessary
        self._find_large_files()
        
        # 7. Analyze documentation duplicates
        self._find_documentation_duplicates()
        
        return self.analysis_report
    
    def _find_system_files(self):
        """Find OS-generated system files"""
        patterns = [
            '**/.DS_Store',
            '**/Thumbs.db', 
            '**/desktop.ini',
            '**/.AppleDouble',
            '**/.LSOverride',
            '**/._*'
        ]
        
        for pattern in patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    size = file_path.stat().st_size
                    self.analysis_report['system_files'].append({
                        'path': str(file_path.relative_to(self.project_root)),
                        'size': size,
                        'type': 'system'
                    })
    
    def _find_backup_files(self):
        """Find backup files"""
        patterns = [
            '**/*_backup.*',
            '**/*.backup',
            '**/*.bak',
            '**/*~',
            '**/*.orig',
            '**/*.old'
        ]
        
        for pattern in patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    size = file_path.stat().st_size
                    self.analysis_report['backup_files'].append({
                        'path': str(file_path.relative_to(self.project_root)),
                        'size': size,
                        'type': 'backup'
                    })
    
    def _find_temp_files(self):
        """Find temporary files"""
        patterns = [
            '**/*.tmp',
            '**/*.temp',
            '**/temp/**',
            '**/tmp/**',
            '**/__pycache__/**',
            '**/*.pyc',
            '**/*.pyo',
            '**/.pytest_cache/**',
            '**/.coverage',
            '**/coverage.xml',
            '**/.mypy_cache/**',
            '**/node_modules/**'
        ]
        
        for pattern in patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    size = file_path.stat().st_size
                    self.analysis_report['temp_files'].append({
                        'path': str(file_path.relative_to(self.project_root)),
                        'size': size,
                        'type': 'temp'
                    })
    
    def _find_redundant_files(self):
        """Find potentially redundant files based on analysis"""
        # Based on our analysis, these files seem redundant
        redundant_candidates = [
            'enhanced_ems_agent.py',  # Superseded by current app.py integration
            'enhanced_ems_simplified.py',  # Demo version, not needed for production
        ]
        
        for file_name in redundant_candidates:
            file_path = self.project_root / file_name
            if file_path.exists() and file_path.is_file():
                size = file_path.stat().st_size
                self.analysis_report['redundant_files'].append({
                    'path': str(file_path.relative_to(self.project_root)),
                    'size': size,
                    'type': 'redundant',
                    'reason': self._get_redundancy_reason(file_name)
                })
    
    def _find_test_files(self):
        """Find test files that might be outdated"""
        test_files = list(self.project_root.glob('**/test_*.py'))
        
        # We'll keep the main test files but analyze them
        for file_path in test_files:
            if file_path.is_file():
                size = file_path.stat().st_size
                # Check if it's actually used or just a demo
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Determine if it's essential
                is_essential = self._is_test_file_essential(file_path.name, content)
                
                self.analysis_report['test_files'].append({
                    'path': str(file_path.relative_to(self.project_root)),
                    'size': size,
                    'type': 'test',
                    'essential': is_essential,
                    'recommendation': 'keep' if is_essential else 'review'
                })
    
    def _find_large_files(self):
        """Find unusually large files"""
        large_threshold = 1024 * 1024  # 1MB
        
        for file_path in self.project_root.rglob('*'):
            if file_path.is_file():
                size = file_path.stat().st_size
                if size > large_threshold:
                    self.analysis_report['large_files'].append({
                        'path': str(file_path.relative_to(self.project_root)),
                        'size': size,
                        'size_mb': round(size / (1024 * 1024), 2),
                        'type': 'large'
                    })
    
    def _find_documentation_duplicates(self):
        """Find potentially duplicate documentation"""
        doc_files = list(self.project_root.glob('**/*.md'))
        
        # Group by similar names
        doc_groups = {}
        for doc in doc_files:
            base_name = doc.stem.lower()
            if base_name not in doc_groups:
                doc_groups[base_name] = []
            doc_groups[base_name].append(doc)
        
        # Find groups with multiple files
        for base_name, files in doc_groups.items():
            if len(files) > 1:
                for file_path in files:
                    size = file_path.stat().st_size
                    self.analysis_report['documentation_duplicates'].append({
                        'path': str(file_path.relative_to(self.project_root)),
                        'size': size,
                        'group': base_name,
                        'type': 'doc_duplicate'
                    })
    
    def _get_redundancy_reason(self, file_name: str) -> str:
        """Get reason why a file is considered redundant"""
        reasons = {
            'enhanced_ems_agent.py': 'Superseded by integrated app.py - functionality moved to main app',
            'enhanced_ems_simplified.py': 'Demo/simplified version - not needed for production use',
        }
        return reasons.get(file_name, 'Potentially redundant')
    
    def _is_test_file_essential(self, file_name: str, content: str) -> bool:
        """Determine if a test file is essential"""
        # test_integrated_system.py and ems_test_questions.py are essential
        if file_name in ['test_integrated_system.py', 'ems_test_questions.py']:
            return True
        
        # test_chatbot.py is less essential as it's for a specific component
        if file_name == 'test_chatbot.py':
            return False
        
        # Check content for indicators of essential tests
        essential_indicators = [
            'def test_', 'class Test', 'unittest', 'pytest',
            'integration', 'system', 'comprehensive'
        ]
        
        return any(indicator in content for indicator in essential_indicators)
    
    def generate_cleanup_report(self):
        """Generate a detailed cleanup report"""
        report = []
        report.append("🧹 EMS Agent - File Cleanup Analysis Report")
        report.append("=" * 60)
        
        total_files = 0
        total_size = 0
        
        for category, files in self.analysis_report.items():
            if category == 'total_space_saved':
                continue
                
            if files:
                report.append(f"\n📁 {category.replace('_', ' ').title()}: {len(files)} files")
                report.append("-" * 40)
                
                category_size = 0
                for file_info in files:
                    size = file_info['size']
                    size_str = self._format_file_size(size)
                    category_size += size
                    total_size += size
                    total_files += 1
                    
                    path = file_info['path']
                    if 'reason' in file_info:
                        report.append(f"  • {path} ({size_str}) - {file_info['reason']}")
                    elif 'recommendation' in file_info:
                        rec = file_info['recommendation']
                        report.append(f"  • {path} ({size_str}) - {rec}")
                    else:
                        report.append(f"  • {path} ({size_str})")
                
                report.append(f"  Subtotal: {self._format_file_size(category_size)}")
        
        report.append(f"\n📊 Summary:")
        report.append(f"  Total files analyzed: {total_files}")
        report.append(f"  Total potential space savings: {self._format_file_size(total_size)}")
        
        return "\n".join(report)
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    def create_cleanup_script(self):
        """Create a script to perform the actual cleanup"""
        script_content = [
            "#!/bin/bash",
            "# EMS Agent - Automated Cleanup Script",
            "# Generated automatically - review before running",
            "",
            "echo '🧹 EMS Agent File Cleanup'",
            "echo '========================='",
            ""
        ]
        
        # Add removal commands for different categories
        for category, files in self.analysis_report.items():
            if category in ['system_files', 'temp_files', 'backup_files'] and files:
                script_content.append(f"# Remove {category.replace('_', ' ')}")
                for file_info in files:
                    path = file_info['path']
                    script_content.append(f"rm -f '{path}'")
                script_content.append("")
        
        # Add optional removals for redundant files
        redundant_files = self.analysis_report.get('redundant_files', [])
        if redundant_files:
            script_content.append("# Optional: Remove redundant files (review first)")
            for file_info in redundant_files:
                path = file_info['path']
                reason = file_info.get('reason', 'Redundant')
                script_content.append(f"# {reason}")
                script_content.append(f"# rm -f '{path}'")
            script_content.append("")
        
        script_content.extend([
            "echo 'Cleanup completed!'",
            "echo 'Project structure optimized.'"
        ])
        
        return "\n".join(script_content)

def main():
    """Main function"""
    project_root = os.getcwd()
    cleanup = EMSFileCleanup(project_root)
    
    # Analyze files
    analysis = cleanup.analyze_project_files()
    
    # Generate report
    report = cleanup.generate_cleanup_report()
    print(report)
    
    # Generate cleanup script
    cleanup_script = cleanup.create_cleanup_script()
    
    # Save cleanup script
    script_path = Path(project_root) / "cleanup_files.sh"
    with open(script_path, 'w') as f:
        f.write(cleanup_script)
    
    print(f"\n💾 Cleanup script saved to: {script_path}")
    print("\n⚠️  RECOMMENDATIONS:")
    print("1. Review the cleanup script before running")
    print("2. Backup important files if unsure")
    print("3. Run: chmod +x cleanup_files.sh && ./cleanup_files.sh")
    print("\n🎯 SAFE TO REMOVE:")
    print("• System files (.DS_Store)")
    print("• Temporary files (__pycache__, *.pyc)")
    print("• Backup files (*_backup.*, *.bak)")
    print("\n🔍 REVIEW BEFORE REMOVING:")
    print("• Enhanced demo files (if not needed)")
    print("• Test files (keep essential ones)")
    print("• Large files (check if actually needed)")

if __name__ == "__main__":
    main()
