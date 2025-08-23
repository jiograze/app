#!/usr/bin/env python3
"""
Prepare training data for fine-tuning the BERT title classification model.
"""
import os
import json
import logging
import random
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import re
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TrainingDataPreparer:
    """Prepare training data for title classification."""
    
    def __init__(self, data_dir: str = "data/legal_documents"):
        """
        Initialize the data preparer.
        
        Args:
            data_dir: Directory containing the raw legal documents
        """
        self.data_dir = Path(data_dir)
        self.output_dir = Path("data/training")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Common legal document section headers in Turkish
        self.section_headers = [
            'BİRİNCİ', 'İKİNCİ', 'ÜÇÜNCÜ', 'DÖRDÜNCÜ', 'BEŞİNCİ', 'ALTINCI', 'YEDİNCİ', 'SEKİZİNCİ', 'DOKUZUNCU', 'ONUNCU',
            'BÖLÜM', 'KISIM', 'BAŞLIK', 'TİTRE', 'MADDE', 'KANUN', 'YÖNETMELİK', 'TÜZÜK', 'YÖNERGE', 'TEBLİĞ',
            'AMAÇ', 'KAPSAM', 'TANIMLAR', 'İLKELER', 'ESASLAR', 'HÜKÜMLER', 'GEÇİCİ MADDELER', 'SON HÜKÜMLER'
        ]
        
        # Compile regex patterns for matching section headers
        self.header_patterns = [
            # Matches patterns like "BİRİNCİ BÖLÜM: Amaç, Kapsam ve Tanımlar"
            re.compile(r'^([A-ZĞÜŞİÖÇ]+(?:\s+[A-ZĞÜŞİÖÇ]+)*\s*[A-ZĞÜŞİÖÇ]*\s*:?\s*[A-ZĞÜŞİÖÇ\s,\-]*)$'),
            # Matches patterns like "MADDE 1 - (1) Bu Kanunun amacı..."
            re.compile(r'^MADDE\s+\d+\s*[-–]\s*\(\d+\)')
        ]
    
    def is_likely_title(self, text: str) -> bool:
        """
        Check if a line of text is likely to be a title/section header.
        
        Args:
            text: The text to check
            
        Returns:
            bool: True if the text is likely a title, False otherwise
        """
        text = text.strip()
        
        # Skip empty or very short lines
        if len(text) < 3 or len(text) > 200:
            return False
        
        # Check if it matches any of the header patterns
        for pattern in self.header_patterns:
            if pattern.match(text):
                return True
        
        # Check if it starts with common section headers
        first_word = text.split()[0] if text else ""
        if first_word in self.section_headers:
            return True
            
        # Check if it's all uppercase (common for titles in legal documents)
        if text.isupper() and len(text.split()) <= 10:
            return True
            
        return False
    
    def extract_titles_from_text(self, text: str) -> List[Dict]:
        """
        Extract potential titles from a document text.
        
        Args:
            text: The document text
            
        Returns:
            List of dictionaries with 'text' and 'label' (1 for title, 0 for non-title)
        """
        lines = text.split('\n')
        samples = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Check if this line is likely a title
            is_title = self.is_likely_title(line)
            
            # Add the line as a sample
            samples.append({
                'text': line,
                'label': 1 if is_title else 0,
                'is_title': is_title
            })
            
            # Add context as negative samples
            if is_title and i > 0:
                # Previous line is likely not a title (context before title)
                prev_line = lines[i-1].strip()
                if prev_line and not self.is_likely_title(prev_line):
                    samples.append({
                        'text': prev_line,
                        'label': 0,
                        'is_title': False
                    })
                
                # Next line is often the start of the section content
                if i < len(lines) - 1:
                    next_line = lines[i+1].strip()
                    if next_line and not self.is_likely_title(next_line):
                        samples.append({
                            'text': next_line,
                            'label': 0,
                            'is_title': False
                        })
        
        return samples
    
    def process_document(self, file_path: Path) -> List[Dict]:
        """
        Process a single document file.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            List of training samples from the document
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
                
            return self.extract_titles_from_text(text)
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return []
    
    def process_directory(self) -> List[Dict]:
        """
        Process all documents in the data directory.
        
        Returns:
            List of training samples
        """
        all_samples = []
        
        # Get all text files in the directory
        text_files = list(self.data_dir.glob("**/*.txt"))
        
        if not text_files:
            logger.warning(f"No text files found in {self.data_dir}")
            return []
        
        # Process each file
        for i, file_path in enumerate(text_files):
            logger.info(f"Processing file {i+1}/{len(text_files)}: {file_path.name}")
            samples = self.process_document(file_path)
            all_samples.extend(samples)
        
        return all_samples
    
    def save_training_data(self, samples: List[Dict], train_ratio: float = 0.8) -> None:
        """
        Save the training data to files.
        
        Args:
            samples: List of training samples
            train_ratio: Ratio of samples to use for training (vs validation)
        """
        if not samples:
            logger.warning("No samples to save")
            return
        
        # Split into training and validation sets
        random.shuffle(samples)
        split_idx = int(len(samples) * train_ratio)
        train_samples = samples[:split_idx]
        val_samples = samples[split_idx:]
        
        # Save training data
        train_file = self.output_dir / "train.json"
        with open(train_file, 'w', encoding='utf-8') as f:
            json.dump(train_samples, f, ensure_ascii=False, indent=2)
        
        # Save validation data
        val_file = self.output_dir / "val.json"
        with open(val_file, 'w', encoding='utf-8') as f:
            json.dump(val_samples, f, ensure_ascii=False, indent=2)
        
        # Print statistics
        logger.info(f"Saved {len(train_samples)} training samples to {train_file}")
        logger.info(f"Saved {len(val_samples)} validation samples to {val_file}")
        
        # Print class distribution
        train_pos = sum(1 for s in train_samples if s['is_title'])
        val_pos = sum(1 for s in val_samples if s['is_title'])
        
        logger.info("\nClass distribution:")
        logger.info(f"  Training set: {train_pos} positive, {len(train_samples)-train_pos} negative")
        logger.info(f"  Validation set: {val_pos} positive, {len(val_samples)-val_pos} negative")


def main():
    """Main function to prepare training data."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Prepare training data for title classification')
    parser.add_argument('--data-dir', type=str, default='data/legal_documents',
                      help='Directory containing raw legal documents')
    parser.add_argument('--output-dir', type=str, default='data/training',
                      help='Directory to save training data')
    parser.add_argument('--train-ratio', type=float, default=0.8,
                      help='Ratio of samples to use for training (vs validation)')
    
    args = parser.parse_args()
    
    # Create data preparer
    preparer = TrainingDataPreparer(data_dir=args.data_dir)
    
    # Process documents and extract samples
    logger.info(f"Processing documents from {args.data_dir}")
    samples = preparer.process_directory()
    
    if not samples:
        logger.error("No samples were generated. Please check your input directory.")
        return
    
    # Save training data
    preparer.save_training_data(samples, train_ratio=args.train_ratio)
    
    logger.info("\nData preparation complete!")


if __name__ == "__main__":
    main()
