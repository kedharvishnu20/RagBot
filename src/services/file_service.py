import os
import shutil
from typing import List, Tuple
from fastapi import HTTPException, UploadFile
from src.utils.config import config
from src.models.schemas import UploadResponse

class FileService:
    """Service for handling file operations"""
    
    def __init__(self):
        self.study_docs_folder = config.study_docs_folder
        self.allowed_extensions = {"pdf", "docx", "txt"}
    
    def validate_file(self, file: UploadFile) -> bool:
        """Validate file type and size"""
        if not file.filename:
            return False
            
        ext = file.filename.lower().rsplit(".", 1)[-1] if "." in file.filename else ""
        return ext in self.allowed_extensions
    
    async def upload_files(self, files: List[UploadFile]) -> List[UploadResponse]:
        """Upload and save files to the study documents folder"""
        os.makedirs(self.study_docs_folder, exist_ok=True)
        results = []
        
        for file in files:
            if not self.validate_file(file):
                ext = file.filename.lower().rsplit(".", 1)[-1] if "." in file.filename else "unknown"
                raise HTTPException(
                    status_code=400, 
                    detail=f"File type .{ext} not supported. Allowed types: {', '.join(self.allowed_extensions)}"
                )
            
            dest = os.path.join(self.study_docs_folder, file.filename)
            
            try:
                with open(dest, "wb") as out:
                    shutil.copyfileobj(file.file, out)
                    
                results.append(UploadResponse(
                    filename=file.filename,
                    status="success",
                    message=f"File {file.filename} uploaded successfully"
                ))
            except Exception as e:
                results.append(UploadResponse(
                    filename=file.filename,
                    status="error",
                    message=f"Failed to upload {file.filename}: {str(e)}"
                ))
        
        return results
    
    def get_uploaded_files(self) -> List[str]:
        """Get list of uploaded files"""
        if not os.path.exists(self.study_docs_folder):
            return []
        return [
            os.path.join(self.study_docs_folder, f) 
            for f in os.listdir(self.study_docs_folder)
            if self.validate_file_path(f)
        ]
    
    def validate_file_path(self, filename: str) -> bool:
        """Check if file path has valid extension"""
        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
        return ext in self.allowed_extensions
    
    def delete_file(self, filename: str) -> bool:
        """Delete a specific uploaded file"""
        try:
            # Sanitize filename to prevent path traversal
            filename = os.path.basename(filename)
            file_path = os.path.join(self.study_docs_folder, filename)
            
            # Check if file exists and is within the study_docs folder
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return False
            
            # Validate file extension
            if not self.validate_file_path(filename):
                print(f"Invalid file type: {filename}")
                return False
            
            # Delete the file
            os.remove(file_path)
            print(f"Successfully deleted file: {filename}")
            return True
            
        except Exception as e:
            print(f"Error deleting file {filename}: {e}")
            return False
    
    def clear_uploads(self) -> bool:
        """Clear all uploaded files"""
        try:
            if os.path.exists(self.study_docs_folder):
                shutil.rmtree(self.study_docs_folder, ignore_errors=True)
            return True
        except Exception as e:
            print(f"Error clearing uploads: {e}")
            return False
