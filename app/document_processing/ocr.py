"""
OCR module for document processing using Tesseract and OCRmyPDF.
Supports Turkish and English language OCR with configurable confidence thresholds.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

import pytesseract
from pdf2image import convert_from_path
import ocrmypdf
from PIL import Image
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

class OCRProcessor:
    def __init__(self, config: Dict = None):
        """
        Initialize OCR processor with configuration.
        
        Args:
            config: Dictionary containing OCR configuration
        """
        self.config = config or {}
        self.language = self.config.get('language', 'tur+eng')
        self.confidence_threshold = self.config.get('confidence_threshold', 75)
        self.dpi = self.config.get('dpi', 300)
        self.enable_preprocessing = self.config.get('enable_preprocessing', True)
        
        self._validate_tesseract()

    def _validate_tesseract(self):
        """Validate Tesseract installation and language packs."""
        try:
            pytesseract.get_languages()
            logger.info("Tesseract installation validated successfully")
        except Exception as e:
            logger.error(f"Tesseract validation failed: {str(e)}")
            raise RuntimeError("Tesseract is not properly installed or configured")

    def process_image(self, image_path: str) -> Tuple[str, float]:
        """
        Process a single image with OCR.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        try:
            # Open and preprocess image
            with Image.open(image_path) as img:
                if self.enable_preprocessing:
                    img = self._preprocess_image(img)
                
                # Perform OCR with confidence
                data = pytesseract.image_to_data(
                    img, 
                    lang=self.language,
                    output_type=pytesseract.Output.DICT
                )
                
                # Extract text and calculate confidence
                text = ' '.join([word for word in data['text'] if word.strip()])
                conf_scores = [score for score in data['conf'] if score != -1]
                avg_confidence = sum(conf_scores) / len(conf_scores) if conf_scores else 0
                
                logger.info(f"OCR completed for {image_path} with {avg_confidence:.2f}% confidence")
                return text, avg_confidence
                
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {str(e)}")
            raise

    def process_pdf(self, pdf_path: str, output_path: Optional[str] = None) -> Dict:
        """
        Process a PDF file, adding OCR layer if needed.
        
        Args:
            pdf_path: Path to input PDF
            output_path: Optional path for OCR'd PDF output
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        try:
            if output_path is None:
                output_path = pdf_path.replace('.pdf', '_ocr.pdf')
                
            # Check if PDF needs OCR
            needs_ocr = self._check_pdf_needs_ocr(pdf_path)
            
            if needs_ocr:
                logger.info(f"PDF requires OCR processing: {pdf_path}")
                # Process with OCRmyPDF
                ocrmypdf.ocr(
                    pdf_path,
                    output_path,
                    language=self.language,
                    deskew=True,
                    optimize=1,
                    skip_text=True,
                    force_ocr=True
                )
                result_path = output_path
            else:
                logger.info(f"PDF already contains text layer: {pdf_path}")
                result_path = pdf_path
            
            # Extract text and metadata from processed PDF
            return self._extract_pdf_text_and_metadata(result_path)
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
            raise

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Apply preprocessing to improve OCR results."""
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # Basic image enhancement
        from PIL import ImageEnhance
        
        # Increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Increase sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.5)
        
        return image

    def _check_pdf_needs_ocr(self, pdf_path: str) -> bool:
        """Check if PDF needs OCR by looking for text content."""
        doc = fitz.open(pdf_path)
        text_content = False
        
        for page in doc:
            if len(page.get_text().strip()) > 100:  # Arbitrary threshold
                text_content = True
                break
                
        doc.close()
        return not text_content

    def _extract_pdf_text_and_metadata(self, pdf_path: str) -> Dict:
        """Extract text and metadata from processed PDF."""
        doc = fitz.open(pdf_path)
        
        text_content = []
        total_words = 0
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            text_content.append(text)
            total_words += len(text.split())
        
        metadata = {
            'page_count': len(doc),
            'total_words': total_words,
            'pdf_metadata': doc.metadata
        }
        
        doc.close()
        
        return {
            'text': '\n\n'.join(text_content),
            'metadata': metadata
        }

if __name__ == "__main__":
    # Example configuration
    config = {
        'language': 'tur+eng',
        'confidence_threshold': 75,
        'dpi': 300,
        'enable_preprocessing': True
    }
    
    # Initialize processor
    processor = OCRProcessor(config)
    
    # Example usage
    try:
        # Process an image
        text, confidence = processor.process_image("sample.png")
        print(f"Image OCR Confidence: {confidence}%")
        print(f"Extracted Text:\n{text}\n")
        
        # Process a PDF
        result = processor.process_pdf("sample.pdf")
        print(f"PDF Processing Results:")
        print(f"Total Pages: {result['metadata']['page_count']}")
        print(f"Total Words: {result['metadata']['total_words']}")
        
    except Exception as e:
        print(f"Error in OCR processing: {str(e)}")
