#!/usr/bin/env python3
"""
Prepare training data for fine-tuning the BERT model for title extraction.
"""
import os
import json
import re
import random
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Generator
import logging
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TitleDataPreparer:
    """Prepare training data for title extraction model."""
    
    def __init__(self, input_dir: str, output_dir: str = "data/title_training"):
        """
        Initialize the data preparer.
        
        Args:
            input_dir: Directory containing extracted legal documents
            output_dir: Directory to save training data
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory set to: {self.output_dir.absolute()}")
        
        # Verify input directory
        if not self.input_dir.exists() or not self.input_dir.is_dir():
            logger.error(f"Input directory does not exist or is not a directory: {self.input_dir}")
            raise FileNotFoundError(f"Input directory not found: {self.input_dir}")
            
        logger.info(f"Input directory: {self.input_dir.absolute()}")
        logger.info(f"Found {len(list(self.input_dir.glob('**/*.jsonl')))} JSONL files in input directory")
        
        # Common Turkish legal document patterns
        self.title_patterns = [
            # Law patterns
            r'(?i)(?:^|\n)\s*(\d+\s*[-–]?\s*\w*\s*)?(?:KANUNU|KANUN\s*NUMARASI|KANUN\s*NO(?:SU)?|YASASI|YASA\s*NO(?:SU)?)',
            # Regulation patterns
            r'(?i)(?:^|\n)\s*(\d+\s*[-–]?\s*\w*\s*)?(?:YÖNETMELİĞİ|YÖNETMELİK|TÜZÜĞÜ|TÜZÜK|GENELGESİ|GENELGE|TEBLİĞİ|TEBLİĞ|TALİMATI|TALİMAT)',
            # Numbered legal documents
            r'(?i)(?:^|\n)\s*(\d+\s*[-–]?\s*\w*\s*)?(?:SAYILI|SAYI\s*NO(?:SU)?|NO(?:SU)?\s*\d+)',
            # Common legal document titles
            r'(?i)(?:^|\n)\s*(\d+\s*[-–]?\s*\w*\s*)?(?:TÜRK\s*CEZA\s*KANUNU|TÜRK\s*BORÇLAR\s*KANUNU|TÜRK\s*TİCARET\s*KANUNU|ANAYASA|ANAYASA\s*MAHKEMESİ)',
        ]
        
        # Compile patterns
        self.compiled_patterns = [re.compile(pattern) for pattern in self.title_patterns]
        
        # Common false positive patterns (to filter out)
        self.false_positive_patterns = [
            r'(?i)madde\s*\d+',  # Article numbers
            r'(?i)kanun(ları|u)\s*(ile|veya|yı|yi|ye|ya|da|de|den|dan)',  # Common false triggers
            r'(?i)yönetmeliği\s*(ile|veya|yı|yi|ye|ya|da|de|den|dan)',
            r'(?i)kanun\s+.*\s+hükmü',
            r'(?i)kanun\s+.*\s+uyarınca',
        ]
        self.compiled_false_positives = [re.compile(pattern) for pattern in self.false_positive_patterns]
    
    def is_likely_title(self, text: str) -> bool:
        """
        Check if a text is likely to be a legal document title.
        
        Args:
            text: Text to check
            
        Returns:
            bool: True if the text is likely a title, False otherwise
        """
        if not text or len(text.strip()) < 5 or len(text) > 500:
            return False
            
        # Check for false positives
        for pattern in self.compiled_false_positives:
            if pattern.search(text):
                return False
                
        # Check for title patterns
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                return True
                
        return False
    
    def process_document(self, doc: Dict) -> List[Dict]:
        """
        Process a single document to extract title candidates and labels.
        
        Args:
            doc: Document dictionary with 'title' and 'content' keys
            
        Returns:
            List of training examples with 'text' and 'label' keys
        """
        examples = []
        doc_id = doc.get('id', 'unknown')
        
        logger.debug(f"Processing document ID: {doc_id}")
        
        # Get the actual title
        actual_title = doc.get('title', '').strip()
        if not actual_title:
            logger.warning(f"Document {doc_id} has no title, skipping")
            return examples
            
        logger.debug(f"Document title: {actual_title}")
        
        # Add the document title as a positive example
        examples.append({
            'text': actual_title,
            'label': 1,  # Positive example
            'source': 'document_title',
            'document_id': doc.get('id'),
            'document_type': doc.get('type')
        })
        
        # Extract titles from article content
        for article in doc.get('articles', []):
            content = article.get('content', '')
            if not content:
                continue
                
            # Split content into lines and check each line
            lines = content.split('\n')
            
            # Check for section headers (usually titles)
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                    
                # Check if line is likely a title
                is_title = self.is_likely_title(line)
                
                # Get context (previous and next lines)
                prev_line = lines[i-1].strip() if i > 0 else ""
                next_line = lines[i+1].strip() if i < len(lines)-1 else ""
                
                examples.append({
                    'text': line,
                    'label': 1 if is_title else 0,
                    'source': 'article_content',
                    'document_id': doc.get('id'),
                    'article_id': article.get('id'),
                    'context': {
                        'prev_line': prev_line,
                        'next_line': next_line
                    }
                })
        
        return examples
    
    def generate_negative_examples(self, doc: Dict, num_negatives: int = 5) -> List[Dict]:
        """
        Generate negative examples from document content.
        
        Args:
            doc: Document dictionary
            num_negatives: Number of negative examples to generate per document
            
        Returns:
            List of negative examples with label 0
        """
        negative_examples = []
        
        # Get all article content
        all_content = []
        for article in doc.get('articles', []):
            content = article.get('content', '')
            if content:
                # Split into sentences or meaningful chunks
                # Simple approach: split by common sentence terminators
                sentences = re.split(r'(?<=[.!?])\s+', content)
                all_content.extend([s.strip() for s in sentences if 10 < len(s.strip()) < 500])
        
        # Randomly sample negative examples
        if len(all_content) > num_negatives:
            samples = random.sample(all_content, num_negatives)
        else:
            samples = all_content
        
        # Add negative examples
        for text in samples:
            # Skip if it looks like a title
            if self.is_likely_title(text):
                continue
                
            negative_examples.append({
                'text': text,
                'label': 0,  # Negative example
                'source': 'negative_sampling',
                'document_id': doc.get('id')
            })
        
        return negative_examples
    
    def process_documents(self, input_files: List[Path], val_split: float = 0.1) -> Dict:
        """
        Process documents and prepare training data.
        
        Args:
            input_files: List of input JSONL files
            val_split: Fraction of data to use for validation
            
        Returns:
            Dictionary with training and validation datasets
        """
        all_examples = []
        
        # Process each input file
        for input_file in input_files:
            logger.info(f"Processing {input_file}...")
            
            with open(input_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        doc = json.loads(line)
                        
                        # Extract positive examples (titles)
                        title_examples = self.process_document(doc)
                        
                        # Generate negative examples
                        negative_examples = self.generate_negative_examples(doc)
                        
                        all_examples.extend(title_examples)
                        all_examples.extend(negative_examples)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing JSON in {input_file}: {e}")
                        continue
        
        logger.info(f"Extracted {len(all_examples)} total examples")
        
        # Shuffle examples
        random.shuffle(all_examples)
        
        # Split into train/validation
        split_idx = int(len(all_examples) * (1 - val_split))
        train_data = all_examples[:split_idx]
        val_data = all_examples[split_idx:]
        
        # Count labels for statistics
        def count_labels(examples):
            counts = defaultdict(int)
            for ex in examples:
                counts[ex['label']] += 1
            return counts
        
        train_counts = count_labels(train_data)
        val_counts = count_labels(val_data)
        
        logger.info(f"Training set: {len(train_data)} examples (1: {train_counts.get(1, 0)}, 0: {train_counts.get(0, 0)})")
        logger.info(f"Validation set: {len(val_data)} examples (1: {val_counts.get(1, 0)}, 0: {val_counts.get(0, 0)})")
        
        return {
            'train': train_data,
            'validation': val_data,
            'stats': {
                'total_examples': len(all_examples),
                'train_size': len(train_data),
                'val_size': len(val_data),
                'train_positives': train_counts.get(1, 0),
                'train_negatives': train_counts.get(0, 0),
            }
        }
    
    return examples

    def generate_negative_examples(self, doc: Dict, num_negatives: int = 5) -> List[Dict]:
        """
        Generate negative examples from document content.
            
        Args:
            doc: Document dictionary
            num_negatives: Number of negative examples to generate per document
                
        Returns:
            List of negative examples with label 0
        """
        negative_examples = []
            
        # Get all article content
        all_content = []
        for article in doc.get('articles', []):
            content = article.get('content', '')
            if content:
                # Split into sentences or meaningful chunks
                # Simple approach: split by common sentence terminators
                sentences = re.split(r'(?<=[.!?])\s+', content)
                all_content.extend([s.strip() for s in sentences if 10 < len(s.strip()) < 500])
            
        # Randomly sample negative examples
        if len(all_content) > num_negatives:
            samples = random.sample(all_content, num_negatives)
        else:
            samples = all_content
            
        # Add negative examples
        for text in samples:
            # Skip if it looks like a title
            if self.is_likely_title(text):
                continue
                    
            negative_examples.append({
                'text': text,
                'label': 0,  # Negative example
                'source': 'negative_sampling',
                'document_id': doc.get('id')
            })
            
        return negative_examples

    def prepare_data(self, val_split: float = 0.1) -> Path:
        """
        Prepare training data from input documents.
            
        Args:
            val_split: Fraction of data to use for validation
                
        Returns:
            Path to the output directory
        """
        all_examples = []
        input_files = list(self.input_dir.glob('**/*.jsonl'))
            
        if not input_files:
            logger.error("No JSONL files found in input directory")
            return self.output_dir
                
        logger.info(f"Found {len(input_files)} JSONL files to process")
            
        for i, doc_path in enumerate(input_files, 1):
            try:
                logger.info(f"Processing file {i}/{len(input_files)}: {doc_path}")
                with open(doc_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        try:
                            doc = json.loads(line)
                            examples = self.process_document(doc)
                            all_examples.extend(examples)
                            if line_num % 10 == 0:
                                logger.debug(f"  Processed {line_num} lines, {len(examples)} examples generated")
                        except json.JSONDecodeError as e:
                            logger.error(f"Error parsing JSON from {doc_path} line {line_num}: {e}")
                        except Exception as e:
                            logger.error(f"Error processing document in {doc_path} line {line_num}: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Error reading file {doc_path}: {e}", exc_info=True)
            
        logger.info(f"Processed {len(all_examples)} total examples from {len(input_files)} files")
            
        if not all_examples:
            logger.error("No training examples were generated. Check the input data and logs for issues.")
            return self.output_dir
                
        return self.save_training_data(all_examples, 1.0 - val_split)

    def save_training_data(self, examples: List[Dict], train_ratio: float = 0.9) -> Path:
        """
        Save training data to disk with train/validation split.
            
        Args:
            examples: List of training examples
            train_ratio: Ratio of training to validation data
                
        Returns:
            Path to the output directory
        """
        if not examples:
            logger.warning("No examples to save")
            return self.output_dir
                
        logger.info(f"Saving {len(examples)} training examples...")
                
        # Shuffle examples
        random.shuffle(examples)
                
        # Split into train and validation
        split_idx = int(len(examples) * train_ratio)
        train_examples = examples[:split_idx]
        val_examples = examples[split_idx:]
                
        # Save to files
        train_path = self.output_dir / 'train.jsonl'
        val_path = self.output_dir / 'validation.jsonl'
        stats_path = self.output_dir / 'stats.json'
                
        # Save training data
        logger.info(f"Writing {len(train_examples)} training examples to {train_path}")
        try:
            with open(train_path, 'w', encoding='utf-8') as f:
                for i, example in enumerate(train_examples, 1):
                    f.write(json.dumps(example, ensure_ascii=False) + '\n')
                    if i % 100 == 0:
                        logger.debug(f"  Wrote {i}/{len(train_examples)} training examples")
            logger.info(f"Successfully wrote training data to {train_path}")
        except Exception as e:
            logger.error(f"Error writing training data: {e}", exc_info=True)
                    
        # Save validation data
        logger.info(f"Writing {len(val_examples)} validation examples to {val_path}")
        try:
            with open(val_path, 'w', encoding='utf-8') as f:
                for i, example in enumerate(val_examples, 1):
                    f.write(json.dumps(example, ensure_ascii=False) + '\n')
                    if i % 100 == 0:
                        logger.debug(f"  Wrote {i}/{len(val_examples)} validation examples")
            logger.info(f"Successfully wrote validation data to {val_path}")
        except Exception as e:
            logger.error(f"Error writing validation data: {e}", exc_info=True)
                    
        # Calculate statistics
        stats = {
            'total_examples': len(examples),
            'train_examples': len(train_examples),
            'val_examples': len(val_examples),
            'positive_examples': sum(1 for ex in examples if ex['label'] == 1),
            'negative_examples': sum(1 for ex in examples if ex['label'] == 0),
            'positive_ratio': f"{sum(1 for ex in examples if ex['label'] == 1) / len(examples):.2f}" if examples else 0,
            'negative_ratio': f"{sum(1 for ex in examples if ex['label'] == 0) / len(examples):.2f}" if examples else 0
        }
                
        logger.info("Training data statistics:")
        for k, v in stats.items():
            logger.info(f"  {k}: {v}")
                
        # Save statistics
        logger.info(f"Writing statistics to {stats_path}")
        try:
            with open(stats_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            logger.info(f"Successfully wrote statistics to {stats_path}")
        except Exception as e:
            logger.error(f"Error writing statistics: {e}", exc_info=True)
                    
        return self.output_dir

def main():
"""Main function to prepare training data."""
import argparse
    
parser = argparse.ArgumentParser(description='Prepare training data for title extraction model')
parser.add_argument('--input-dir', type=str, required=True,
                    help='Directory containing extracted legal documents')
parser.add_argument('--output-dir', type=str, default='data/title_training',
                    help='Directory to save training data')
parser.add_argument('--val-split', type=float, default=0.1,
                    help='Fraction of data to use for validation (default: 0.1)')
parser.add_argument('--debug', action='store_true',
                    help='Enable debug logging')
    
args = parser.parse_args()
    
# Set log level
log_level = logging.DEBUG if args.debug else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('prepare_title_data.log')
    ]
)
    
logger.info("Starting title training data preparation")
logger.info(f"Input directory: {os.path.abspath(args.input_dir)}")
logger.info(f"Output directory: {os.path.abspath(args.output_dir)}")
logger.info(f"Validation split: {args.val_split}")
    
# Initialize data preparer
try:
    preparer = TitleDataPreparer(args.input_dir, args.output_dir)
        
    # Process all documents and save training data
    output_dir = preparer.prepare_data(val_split=args.val_split)
        
    logger.info(f"Training data preparation complete. Output saved to {output_dir}")
        
    # Print statistics if available
    stats_file = output_dir / 'stats.json'
    if stats_file.exists():
        with open(stats_file, 'r', encoding='utf-8') as f:
            stats = json.load(f)
            logger.info("Training data statistics:")
            for k, v in stats.items():
                logger.info(f"  {k}: {v}")
        
except Exception as e:
    logger.error(f"Error preparing training data: {e}", exc_info=True)
    sys.exit(1)

if __name__ == "__main__":
    main()
