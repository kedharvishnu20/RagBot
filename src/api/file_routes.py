from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from typing import List
import os
import mimetypes
import tempfile
import hashlib
from pathlib import Path
from src.services.file_service import FileService
from src.services.chat_orchestrator import ChatOrchestrator
from src.models.schemas import UploadResponse

router = APIRouter(tags=["files"])
file_service = FileService()
chat_orchestrator = ChatOrchestrator()

# Create a directory for converted PDFs
CONVERTED_PDF_DIR = "converted_pdfs"
os.makedirs(CONVERTED_PDF_DIR, exist_ok=True)

@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload documents for RAG processing"""
    try:
        results = await file_service.upload_files(files)
        return {"files": results}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/rebuild_index")
async def rebuild_index(api_key_index: int = Form(0)):
    """Rebuild the vector index from uploaded documents"""
    try:
        result = await chat_orchestrator.rebuild_vector_index(api_key_index)
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Index rebuild failed: {str(e)}")

@router.post("/clear_vector_db")
async def clear_vector_db():
    """Clear the vector database"""
    try:
        result = chat_orchestrator.clear_vector_database()
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["message"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clear operation failed: {str(e)}")

@router.get("/vector_status")
def get_vector_status():
    """Get vector store status and statistics"""
    try:
        return chat_orchestrator.get_vector_store_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@router.get("/uploaded")
def list_uploaded_files():
    """Get list of uploaded files"""
    try:
        files = file_service.get_uploaded_files()
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")

@router.delete("/delete/{filename}")
def delete_file(filename: str):
    """Delete a specific uploaded file"""
    try:
        success = file_service.delete_file(filename)
        if success:
            return {"status": "success", "message": f"File '{filename}' deleted successfully"}
        else:
            return {"status": "error", "message": f"Failed to delete file '{filename}'"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete operation failed: {str(e)}")

@router.delete("/clear_uploads")
def clear_uploads():
    """Clear all uploaded files"""
    try:
        success = file_service.clear_uploads()
        if success:
            return {"status": "success", "message": "All uploads cleared"}
        else:
            return {"status": "error", "message": "Failed to clear uploads"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clear operation failed: {str(e)}")

@router.get("/content-preview/{filename}")
async def get_file_content_preview(filename: str, page: int = 1, fast: bool = False):
    """Get file content preview with pagination support"""
    try:
        # Sanitize filename to prevent path traversal
        filename = os.path.basename(filename)
        file_path = os.path.join("study_docs", filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get file info
        file_size = os.path.getsize(file_path)
        file_ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
        
        # Initialize preview data
        preview_data = {
            "file_type": file_ext,
            "file_size": file_size,
            "page": page,
            "total_pages": 1,
            "has_multiple_pages": False,
            "content": "",
            "converted_to_pdf": False,
            "will_convert_to_pdf": False,
            "fast_mode": fast
        }
        
        # Handle different file types
        if file_ext == "pdf":
            preview_data.update(await _handle_pdf_preview(file_path, page))
        elif file_ext in ["docx", "doc"]:
            if fast:
                # Fast mode: Skip PDF conversion, use text only
                preview_data.update(await _handle_word_text_only_preview(file_path))
            else:
                # Normal mode: Try PDF conversion
                preview_data.update(await _handle_word_preview(file_path))
        elif file_ext == "txt":
            preview_data.update(await _handle_text_preview(file_path))
        else:
            preview_data["content"] = "Preview not available for this file type"
        
        return JSONResponse(content=preview_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating preview: {str(e)}")

@router.get("/preview/{filename}")
async def get_file_preview_info(filename: str):
    """Get basic file information for preview modal"""
    try:
        # Sanitize filename to prevent path traversal
        filename = os.path.basename(filename)
        file_path = os.path.join("study_docs", filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get file info
        file_size = os.path.getsize(file_path)
        file_ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
        
        # Determine file properties
        file_info = {
            "filename": filename,
            "file_size": file_size,
            "file_type": file_ext,
            "is_pdf": file_ext == "pdf",
            "is_word": file_ext in ["docx", "doc"],
            "is_text": file_ext == "txt",
            "will_convert_to_pdf": file_ext in ["docx", "doc"],
            "supports_preview": file_ext in ["pdf", "docx", "doc", "txt"]
        }
        
        return JSONResponse(content=file_info)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting file info: {str(e)}")

@router.get("/view/{filename}")
async def view_file(filename: str, download: bool = False):
    """Serve file for direct viewing (PDF, images, etc.) or download"""
    try:
        # Sanitize filename to prevent path traversal
        filename = os.path.basename(filename)
        file_path = os.path.join("study_docs", filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get file extension
        file_ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
        
        # Handle DOCX files - serve converted PDF if available or force conversion
        if file_ext in ["docx", "doc"] and not download:
            pdf_path = _get_converted_pdf_path(file_path)
            
            # If PDF doesn't exist, try to convert
            if not os.path.exists(pdf_path):
                try:
                    pdf_path = await _convert_docx_to_pdf(file_path)
                except Exception as e:
                    # If conversion fails, fall back to serving original file
                    print(f"Conversion failed, serving original file: {e}")
                    pdf_path = None
            
            # If we have a converted PDF, serve it
            if pdf_path and os.path.exists(pdf_path):
                headers = {"Content-Disposition": f"inline; filename={os.path.splitext(filename)[0]}.pdf"}
                return FileResponse(
                    path=pdf_path,
                    media_type="application/pdf",
                    headers=headers
                )
        
        # Handle regular files or download requests
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"
        
        # Set headers based on whether download is requested
        headers = {}
        if download:
            # Force download
            headers["Content-Disposition"] = f"attachment; filename={filename}"
        else:
            # Try to display inline (especially for PDFs)
            if mime_type == "application/pdf":
                headers["Content-Disposition"] = f"inline; filename={filename}"
            # For other file types, let browser decide
        
        return FileResponse(
            path=file_path,
            media_type=mime_type,
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving file: {str(e)}")

# Helper functions for file preview processing
async def _handle_pdf_preview(file_path: str, page: int = 1):
    """Handle PDF file preview using pypdf library"""
    try:
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        total_pages = len(reader.pages)
        
        if page > total_pages:
            page = total_pages
        if page < 1:
            page = 1
            
        # Get text content from the specific page
        page_obj = reader.pages[page - 1]
        text_content = page_obj.extract_text()
        
        return {
            "content": text_content[:2000] + "..." if len(text_content) > 2000 else text_content,
            "page": page,
            "total_pages": total_pages,
            "has_multiple_pages": total_pages > 1
        }
    except ImportError:
        return {
            "content": "PDF preview requires pypdf library. Please install with: pip install pypdf",
            "page": page,
            "total_pages": 1,
            "has_multiple_pages": False
        }
    except Exception as e:
        return {
            "content": f"Error reading PDF: {str(e)}",
            "page": page,
            "total_pages": 1,
            "has_multiple_pages": False
        }

async def _handle_word_preview(file_path: str):
    """Handle Word document preview with PDF conversion"""
    try:
        # First, try to get or create the converted PDF
        pdf_path = _get_converted_pdf_path(file_path)
        
        if not os.path.exists(pdf_path):
            # Convert DOCX to PDF
            try:
                pdf_path = await _convert_docx_to_pdf(file_path)
                conversion_successful = True
            except Exception as convert_error:
                print(f"PDF conversion failed: {convert_error}")
                conversion_successful = False
                pdf_path = None
        else:
            conversion_successful = True
        
        # If conversion was successful, extract text from PDF for preview
        if conversion_successful and pdf_path and os.path.exists(pdf_path):
            try:
                from pypdf import PdfReader
                reader = PdfReader(pdf_path)
                text_content = ""
                
                # Extract text from first few pages for preview
                max_pages = min(3, len(reader.pages))
                for i in range(max_pages):
                    text_content += reader.pages[i].extract_text() + "\n\n"
                
                return {
                    "content": text_content[:2000] + "..." if len(text_content) > 2000 else text_content,
                    "converted_to_pdf": True,
                    "pdf_path": pdf_path,
                    "total_pages": len(reader.pages),
                    "has_multiple_pages": len(reader.pages) > 1
                }
            except Exception as e:
                print(f"Error reading converted PDF: {e}")
        
        # Fallback to original docx2txt method
        try:
            import docx2txt
            text_content = docx2txt.process(file_path)
            
            return {
                "content": text_content[:2000] + "..." if len(text_content) > 2000 else text_content,
                "converted_to_pdf": conversion_successful,
                "pdf_path": pdf_path if conversion_successful else None,
                "will_convert_to_pdf": not conversion_successful
            }
        except ImportError:
            return {
                "content": "Word preview requires docx2txt library. Please install with: pip install docx2txt",
                "converted_to_pdf": False,
                "will_convert_to_pdf": False
            }
        except Exception as e:
            return {
                "content": f"Error reading Word document: {str(e)}",
                "converted_to_pdf": False,
                "will_convert_to_pdf": False
            }
            
    except Exception as e:
        return {
            "content": f"Error processing Word document: {str(e)}",
            "converted_to_pdf": False,
            "will_convert_to_pdf": False
        }

async def _handle_word_text_only_preview(file_path: str):
    """Handle Word document preview with fast text-only extraction (no PDF conversion)"""
    try:
        # Skip PDF conversion for fast preview
        import docx2txt
        text_content = docx2txt.process(file_path)
        
        return {
            "content": text_content[:2000] + "..." if len(text_content) > 2000 else text_content,
            "converted_to_pdf": False,
            "will_convert_to_pdf": True,  # Indicate conversion is possible but not done yet
            "fast_preview": True
        }
    except ImportError:
        return {
            "content": "Word preview requires docx2txt library. Please install with: pip install docx2txt",
            "converted_to_pdf": False,
            "will_convert_to_pdf": False,
            "fast_preview": True
        }
    except Exception as e:
        return {
            "content": f"Error reading Word document: {str(e)}",
            "converted_to_pdf": False,
            "will_convert_to_pdf": False,
            "fast_preview": True
        }

async def _handle_text_preview(file_path: str):
    """Handle text file preview"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "content": content[:2000] + "..." if len(content) > 2000 else content
        }
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            return {
                "content": content[:2000] + "..." if len(content) > 2000 else content
            }
        except Exception as e:
            return {
                "content": f"Error reading text file: {str(e)}"
            }
    except Exception as e:
        return {
            "content": f"Error reading text file: {str(e)}"
        }

async def _convert_docx_to_pdf(docx_path: str) -> str:
    """Convert DOCX file to PDF and return the PDF path"""
    try:
        # Create a unique filename for the converted PDF
        docx_filename = os.path.basename(docx_path)
        pdf_filename = os.path.splitext(docx_filename)[0] + ".pdf"
        
        # Create a hash of the original file to handle duplicates and caching
        with open(docx_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()[:8]
        
        pdf_filename = f"{os.path.splitext(docx_filename)[0]}_{file_hash}.pdf"
        pdf_path = os.path.join(CONVERTED_PDF_DIR, pdf_filename)
        
        # Check if converted file already exists
        if os.path.exists(pdf_path):
            return pdf_path
        
        # Try different conversion methods
        conversion_successful = False
        
        # Method 1: Try docx2pdf (works well on Windows)
        try:
            from docx2pdf import convert
            convert(docx_path, pdf_path)
            if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                conversion_successful = True
        except Exception as e:
            print(f"docx2pdf conversion failed: {e}")
        
        # Method 2: If docx2pdf fails, try python-docx with reportlab
        if not conversion_successful:
            try:
                from docx import Document
                from reportlab.lib.pagesizes import letter
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                from reportlab.lib.styles import getSampleStyleSheet
                from reportlab.lib.units import inch
                
                # Read the docx file
                doc = Document(docx_path)
                
                # Create PDF
                pdf_doc = SimpleDocTemplate(pdf_path, pagesize=letter)
                styles = getSampleStyleSheet()
                story = []
                
                for paragraph in doc.paragraphs:
                    if paragraph.text.strip():
                        p = Paragraph(paragraph.text, styles['Normal'])
                        story.append(p)
                        story.append(Spacer(1, 0.2*inch))
                
                pdf_doc.build(story)
                if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                    conversion_successful = True
                    
            except Exception as e:
                print(f"python-docx + reportlab conversion failed: {e}")
        
        # Method 3: If both fail, try using LibreOffice (if available)
        if not conversion_successful:
            try:
                import subprocess
                result = subprocess.run([
                    'libreoffice', '--headless', '--convert-to', 'pdf',
                    '--outdir', CONVERTED_PDF_DIR, docx_path
                ], capture_output=True, text=True, timeout=30)
                
                # LibreOffice creates the PDF with the original name
                expected_pdf = os.path.join(CONVERTED_PDF_DIR, os.path.splitext(docx_filename)[0] + ".pdf")
                if os.path.exists(expected_pdf):
                    # Rename to our hashed version
                    os.rename(expected_pdf, pdf_path)
                    conversion_successful = True
                    
            except Exception as e:
                print(f"LibreOffice conversion failed: {e}")
        
        if conversion_successful and os.path.exists(pdf_path):
            return pdf_path
        else:
            raise Exception("All conversion methods failed")
            
    except Exception as e:
        raise Exception(f"DOCX to PDF conversion failed: {str(e)}")

def _get_converted_pdf_path(docx_path: str) -> str:
    """Get the path where the converted PDF would be stored"""
    docx_filename = os.path.basename(docx_path)
    
    # Create a hash of the original file
    try:
        with open(docx_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()[:8]
    except:
        file_hash = "unknown"
    
    pdf_filename = f"{os.path.splitext(docx_filename)[0]}_{file_hash}.pdf"
    return os.path.join(CONVERTED_PDF_DIR, pdf_filename)
