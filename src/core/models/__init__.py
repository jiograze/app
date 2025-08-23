""
Database models for the Mevzuat Yönetim Sistemi.
"""
from datetime import datetime
from .. import db

class Document(db.Model):
    """Document model for storing document metadata."""
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(512), nullable=False)
    original_filename = db.Column(db.String(512), nullable=False)
    file_path = db.Column(db.String(1024), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # in bytes
    file_type = db.Column(db.String(32), nullable=False)
    mime_type = db.Column(db.String(128), nullable=False)
    
    # Document metadata
    document_type = db.Column(db.String(64))  # kanun, yönetmelik, genelge, etc.
    document_number = db.Column(db.String(64))
    publish_date = db.Column(db.Date)
    effective_date = db.Column(db.Date)
    
    # Status
    is_processed = db.Column(db.Boolean, default=False, nullable=False)
    processing_error = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pages = db.relationship('DocumentPage', backref='document', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Document {self.id}: {self.title}>'

class DocumentPage(db.Model):
    """Individual pages of a document with extracted text and metadata."""
    __tablename__ = 'document_pages'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    page_number = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text)
    
    # OCR/Extraction metadata
    ocr_confidence = db.Column(db.Float)
    is_scanned = db.Column(db.Boolean, default=False)
    
    # Vector embedding for semantic search
    embedding = db.Column(db.LargeBinary)  # Store as BLOB or use a vector extension
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('document_id', 'page_number', name='_document_page_uc'),
    )
    
    def __repr__(self):
        return f'<DocumentPage {self.document_id}-{self.page_number}>'

class DocumentCategory(db.Model):
    """Categories for organizing documents."""
    __tablename__ = 'document_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('document_categories.id'))
    
    # Relationships
    children = db.relationship('DocumentCategory', backref=db.backref('parent', remote_side=[id]))
    
    def __repr__(self):
        return f'<DocumentCategory {self.name}>'

class DocumentCategoryMapping(db.Model):
    """Mapping between documents and categories (many-to-many relationship)."""
    __tablename__ = 'document_category_mappings'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('document_categories.id'), nullable=False)
    
    # Relationships
    category = db.relationship('DocumentCategory')
    
    __table_args__ = (
        db.UniqueConstraint('document_id', 'category_id', name='_document_category_uc'),
    )
    
    def __repr__(self):
        return f'<DocumentCategoryMapping doc:{self.document_id} -> cat:{self.category_id}>'
