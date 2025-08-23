#!/usr/bin/env python3
"""
Extract legal documents from the database for fine-tuning the title extraction model.
"""
import os
import sqlite3
import json
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DocumentExtractor:
    """Extract legal documents from the database for training."""
    
    def __init__(self, db_path: str, output_dir: str = "data/legal_documents"):
        """
        Initialize the document extractor.
        
        Args:
            db_path: Path to the SQLite database
            output_dir: Directory to save extracted documents
        """
        self.db_path = Path(db_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate database path
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database file not found: {self.db_path}")
    
    def get_documents(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Extract documents from the database.
        
        Args:
            limit: Maximum number of documents to extract
            
        Returns:
            List of document dictionaries with id, title, and content
        """
        try:
            conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get document count
            cursor.execute("SELECT COUNT(*) as count FROM documents")
            total_docs = cursor.fetchone()['count']
            logger.info(f"Found {total_docs} documents in the database")
            
            # Get documents with their articles
            query = """
            SELECT 
                d.id as doc_id, 
                d.title as doc_title,
                d.law_number,
                d.document_type as doc_type,
                d.category,
                d.subcategory,
                d.original_filename,
                d.stored_filename,
                d.file_path,
                d.file_size,
                d.created_at,
                d.updated_at,
                d.effective_date,
                d.publication_date,
                d.status,
                a.id as article_id,
                a.article_number,
                a.title as article_title,
                a.content as article_content,
                a.content_clean,
                a.seq_index,
                a.is_repealed,
                a.is_amended,
                a.article_type,
                a.created_at as article_created_at,
                a.updated_at as article_updated_at
            FROM documents d
            LEFT JOIN articles a ON d.id = a.document_id
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Group articles by document
            documents = {}
            for row in rows:
                doc_id = row['doc_id']
                if doc_id not in documents:
                    documents[doc_id] = {
                        'id': doc_id,
                        'title': row['doc_title'],
                        'law_number': row['law_number'],
                        'type': row['doc_type'] if row['doc_type'] else 'Belge',
                        'category': row['category'],
                        'subcategory': row['subcategory'],
                        'original_filename': row['original_filename'],
                        'stored_filename': row['stored_filename'],
                        'file_path': row['file_path'],
                        'file_size': row['file_size'],
                        'effective_date': row['effective_date'],
                        'publication_date': row['publication_date'],
                        'status': row['status'],
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at'],
                        'articles': []
                    }
                
                if row['article_id']:
                    documents[doc_id]['articles'].append({
                        'id': row['article_id'],
                        'article_number': row['article_number'],
                        'title': row['article_title'],
                        'content': row['article_content'],
                        'content_clean': row['content_clean'],
                        'seq_index': row['seq_index'],
                        'is_repealed': bool(row['is_repealed']) if row['is_repealed'] is not None else False,
                        'is_amended': bool(row['is_amended']) if row['is_amended'] is not None else False,
                        'article_type': row['article_type'],
                        'created_at': row['article_created_at'],
                        'updated_at': row['article_updated_at']
                    })
            
            return list(documents.values())
            
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            raise
        finally:
            if 'conn' in locals():
                conn.close()
    
    def save_documents(self, documents: List[Dict], format: str = 'jsonl') -> Tuple[int, Path]:
        """
        Save extracted documents to files.
        
        Args:
            documents: List of document dictionaries
            format: Output format ('jsonl' or 'txt')
            
        Returns:
            Tuple of (number of documents saved, output directory)
        """
        if not documents:
            logger.warning("No documents to save")
            return 0, self.output_dir
        
        # Create output directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = self.output_dir / f"extracted_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if format == 'jsonl':
            # Save as JSON Lines (one document per line)
            output_file = output_dir / "documents.jsonl"
            with open(output_file, 'w', encoding='utf-8') as f:
                for doc in documents:
                    f.write(json.dumps(doc, ensure_ascii=False) + '\n')
            logger.info(f"Saved {len(documents)} documents to {output_file}")
            
        elif format == 'txt':
            # Save as individual text files
            for doc in documents:
                # Create a safe filename
                title = doc.get('title', f"document_{doc['id']}")
                safe_title = "".join(c if c.isalnum() or c in ' -_' else '_' for c in title)
                safe_title = safe_title[:100].strip()  # Limit filename length
                
                # Combine document info and articles into a single text
                content = [
                    f"# {doc.get('title', '')}",
                    f"Type: {doc.get('type', '')}",
                    f"Law Number: {doc.get('law_number', '')}",
                    f"Status: {doc.get('status', '')}",
                    f"Issue Date: {doc.get('issue_date', '')}",
                    f"Official Gazette: {doc.get('official_gazette_number', '')} - {doc.get('official_gazette_date', '')}",
                    "\n## Articles\n"
                ]
                
                for article in doc.get('articles', []):
                    content.append(f"### {article.get('article_number', '')}")
                    content.append(article.get('content', ''))
                    if article.get('summary'):
                        content.append(f"\n**Summary:** {article['summary']}\n")
                
                # Save to file
                output_file = output_dir / f"{doc['id']}_{safe_title}.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write("\n".join(content))
            
            logger.info(f"Saved {len(documents)} documents to {output_dir}/")
        
        return len(documents), output_dir

def main():
    """Main function to extract legal documents."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract legal documents from the database')
    parser.add_argument('--db-path', type=str, 
                      default='/home/altay/Masaüstü/mevzuat/C:\\Users\\klc\\Documents\\MevzuatDeposu/db/mevzuat.sqlite',
                      help='Path to the SQLite database file')
    parser.add_argument('--output-dir', type=str, default='data/legal_documents',
                      help='Directory to save extracted documents')
    parser.add_argument('--limit', type=int, default=None,
                      help='Maximum number of documents to extract')
    parser.add_argument('--format', type=str, default='jsonl',
                      choices=['jsonl', 'txt'],
                      help='Output format: jsonl (default) or txt')
    
    args = parser.parse_args()
    
    try:
        # Initialize extractor
        extractor = DocumentExtractor(db_path=args.db_path, output_dir=args.output_dir)
        
        # Extract documents
        logger.info(f"Extracting documents from {args.db_path}...")
        documents = extractor.get_documents(limit=args.limit)
        
        if not documents:
            logger.warning("No documents found in the database")
            return
        
        # Save documents
        count, output_dir = extractor.save_documents(documents, format=args.format)
        logger.info(f"Successfully extracted {count} documents to {output_dir}")
        
    except Exception as e:
        logger.error(f"Error extracting documents: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
