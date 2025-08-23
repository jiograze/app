"""
Document processing module for handling document parsing and text extraction.
"""
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import PyPDF2
import docx
import pandas as pd
from .bert_title_analyzer import BERTTitleAnalyzer

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Processes documents to extract text and metadata"""
    
    def __init__(self, config: Optional[dict] = None):
        """Initialize the document processor"""
        self.config = config or {}
        self.title_analyzer = BERTTitleAnalyzer()
        
    def extract_text(self, file_path: Union[str, Path]) -> str:
        """
        Extract text from a document file.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Extracted text content
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        suffix = file_path.suffix.lower()
        
        try:
            if suffix == '.pdf':
                return self._extract_from_pdf(file_path)
            elif suffix in ('.doc', '.docx'):
                return self._extract_from_docx(file_path)
            elif suffix in ('.xls', '.xlsx'):
                return self._extract_from_excel(file_path)
            elif suffix == '.txt':
                return file_path.read_text(encoding='utf-8')
            else:
                logger.warning(f"Unsupported file format: {suffix}")
                return ""
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            return ""
    
    def _extract_from_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            logger.error(f"Error reading PDF {file_path}: {str(e)}")
        return text.strip()
    
    def _extract_from_docx(self, file_path: Path) -> str:
        """Extract text from Word document"""
        try:
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            logger.error(f"Error reading DOCX {file_path}: {str(e)}")
            return ""
    
    def _extract_from_excel(self, file_path: Path) -> str:
        """Extract text from Excel file"""
        try:
            df = pd.read_excel(file_path)
            return df.to_string()
        except Exception as e:
            logger.error(f"Error reading Excel {file_path}: {str(e)}")
            return ""
    
    def analyze_document(self, file_path: Union[str, Path]) -> Dict[str, str]:
        """
        Analyze a document and extract key information.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary containing document metadata and extracted information
        """
        file_path = Path(file_path)
        text = self.extract_text(file_path)
        
        # Extract title using BERT
        title_info = self.title_analyzer.extract_title(text)
        
        return {
            'file_path': str(file_path),
            'file_name': file_path.name,
            'file_size': file_path.stat().st_size,
            'title': title_info.get('title', ''),
            'confidence': title_info.get('confidence', 0.0),
            'text': text[:1000] + '...' if len(text) > 1000 else text,
            'word_count': len(text.split())
        }
