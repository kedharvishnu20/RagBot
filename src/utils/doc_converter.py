"""
Document conversion utilities for RAG AI application.
Handles conversion of Word documents to PDF for transparent preview.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class DocumentConverter:
    """Handles document conversion, primarily Word to PDF."""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self.conversion_cache = {}  # Cache for converted files
    
    def is_word_document(self, file_path: str) -> bool:
        """Check if file is a Word document."""
        file_ext = Path(file_path).suffix.lower()
        return file_ext in ['.docx', '.doc']
    
    def get_pdf_cache_path(self, word_file_path: str) -> str:
        """Get the cache path for converted PDF."""
        word_path = Path(word_file_path)
        pdf_name = f"{word_path.stem}_converted.pdf"
        return os.path.join(self.temp_dir, "rag_pdf_cache", pdf_name)
    
    def is_conversion_needed(self, word_file_path: str) -> bool:
        """Check if Word document needs to be converted to PDF."""
        if not self.is_word_document(word_file_path):
            return False
        
        pdf_cache_path = self.get_pdf_cache_path(word_file_path)
        
        if not os.path.exists(pdf_cache_path):
            return True
        
        # Check if Word file is newer than cached PDF
        word_mtime = os.path.getmtime(word_file_path)
        pdf_mtime = os.path.getmtime(pdf_cache_path)
        
        return word_mtime > pdf_mtime
    
    def convert_word_to_pdf_libreoffice(self, word_file_path: str) -> Optional[str]:
        """Convert Word document to PDF using LibreOffice."""
        try:
            # Create cache directory
            cache_dir = os.path.dirname(self.get_pdf_cache_path(word_file_path))
            os.makedirs(cache_dir, exist_ok=True)
            
            # LibreOffice command for headless conversion
            cmd = [
                'libreoffice',
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', cache_dir,
                word_file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # LibreOffice creates PDF with original filename
                word_path = Path(word_file_path)
                generated_pdf = os.path.join(cache_dir, f"{word_path.stem}.pdf")
                target_pdf = self.get_pdf_cache_path(word_file_path)
                
                if os.path.exists(generated_pdf):
                    # Rename to our cache naming convention
                    if generated_pdf != target_pdf:
                        os.rename(generated_pdf, target_pdf)
                    logger.info(f"Successfully converted {word_file_path} to PDF")
                    return target_pdf
            
            logger.error(f"LibreOffice conversion failed: {result.stderr}")
            return None
            
        except subprocess.TimeoutExpired:
            logger.error("LibreOffice conversion timed out")
            return None
        except FileNotFoundError:
            logger.warning("LibreOffice not found, trying alternative conversion")
            return None
        except Exception as e:
            logger.error(f"LibreOffice conversion error: {e}")
            return None
    
    def convert_word_to_pdf_python(self, word_file_path: str) -> Optional[str]:
        """Convert Word document to PDF using python-docx2pdf."""
        try:
            from docx2pdf import convert
            
            # Create cache directory
            pdf_cache_path = self.get_pdf_cache_path(word_file_path)
            cache_dir = os.path.dirname(pdf_cache_path)
            os.makedirs(cache_dir, exist_ok=True)
            
            # Convert using docx2pdf
            convert(word_file_path, pdf_cache_path)
            
            if os.path.exists(pdf_cache_path):
                logger.info(f"Successfully converted {word_file_path} to PDF using docx2pdf")
                return pdf_cache_path
            
            return None
            
        except ImportError:
            logger.warning("docx2pdf not available")
            return None
        except Exception as e:
            logger.error(f"docx2pdf conversion error: {e}")
            return None
    
    def convert_word_to_pdf_fallback(self, word_file_path: str) -> Optional[str]:
        """Fallback conversion using docx content extraction to create a simple PDF."""
        try:
            from docx import Document
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.units import inch
            
            # Extract text from Word document
            doc = Document(word_file_path)
            text_content = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)
            
            if not text_content:
                return None
            
            # Create PDF
            pdf_cache_path = self.get_pdf_cache_path(word_file_path)
            cache_dir = os.path.dirname(pdf_cache_path)
            os.makedirs(cache_dir, exist_ok=True)
            
            # Create PDF document
            doc_pdf = SimpleDocTemplate(pdf_cache_path, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Add title
            word_filename = Path(word_file_path).name
            title = Paragraph(f"<b>{word_filename}</b>", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 12))
            
            # Add content
            for text in text_content:
                para = Paragraph(text, styles['Normal'])
                story.append(para)
                story.append(Spacer(1, 6))
            
            doc_pdf.build(story)
            
            if os.path.exists(pdf_cache_path):
                logger.info(f"Successfully converted {word_file_path} to PDF using fallback method")
                return pdf_cache_path
            
            return None
            
        except ImportError as e:
            logger.warning(f"Fallback conversion dependencies not available: {e}")
            return None
        except Exception as e:
            logger.error(f"Fallback conversion error: {e}")
            return None
    
    def convert_word_to_pdf(self, word_file_path: str) -> Optional[str]:
        """
        Convert Word document to PDF using the best available method.
        Returns path to converted PDF or None if conversion fails.
        """
        if not self.is_word_document(word_file_path):
            return None
        
        if not os.path.exists(word_file_path):
            return None
        
        # Check if conversion is needed
        if not self.is_conversion_needed(word_file_path):
            cached_pdf = self.get_pdf_cache_path(word_file_path)
            if os.path.exists(cached_pdf):
                logger.info(f"Using cached PDF for {word_file_path}")
                return cached_pdf
        
        logger.info(f"Converting Word document to PDF: {word_file_path}")
        
        # Try conversion methods in order of preference
        methods = [
            self.convert_word_to_pdf_libreoffice,
            self.convert_word_to_pdf_python,
            self.convert_word_to_pdf_fallback
        ]
        
        for method in methods:
            try:
                result = method(word_file_path)
                if result and os.path.exists(result):
                    return result
            except Exception as e:
                logger.warning(f"Conversion method {method.__name__} failed: {e}")
                continue
        
        logger.error(f"All conversion methods failed for {word_file_path}")
        return None
    
    def cleanup_cache(self, max_age_days: int = 7):
        """Clean up old converted PDF files."""
        try:
            cache_dir = os.path.join(self.temp_dir, "rag_pdf_cache")
            if not os.path.exists(cache_dir):
                return
            
            import time
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 60 * 60
            
            for filename in os.listdir(cache_dir):
                file_path = os.path.join(cache_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        logger.info(f"Cleaned up old cache file: {filename}")
        
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")

# Global converter instance
converter = DocumentConverter()
