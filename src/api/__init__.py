"""
API endpoints for the Mevzuat Yönetim Sistemi.
"""
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest, NotFound, Unauthorized
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import os
import uuid

from ..core.models import db, Document, DocumentPage, User
from ..core.services.document_service import DocumentService
from ..core.utils.file_utils import allowed_file, get_file_extension

api_bp = Blueprint('api', __name__)
document_service = DocumentService()

# Helper functions
def get_current_user():
    """Get the current authenticated user."""
    user_id = get_jwt_identity()
    if not user_id:
        raise Unauthorized('Authentication required')
    
    user = User.query.get(user_id)
    if not user or not user.is_active:
        raise Unauthorized('Invalid or inactive user')
    
    return user

# Document endpoints
@api_bp.route('/documents', methods=['POST'])
@jwt_required()
def upload_document():
    """
    Upload a new document to the system.
    
    Expected form data:
    - file: The document file to upload (required)
    - title: (optional) Document title
    - document_type: (optional) Type of document (kanun, yönetmelik, etc.)
    - document_number: (optional) Document number
    """
    user = get_current_user()
    
    if 'file' not in request.files:
        raise BadRequest('No file part in the request')
    
    file = request.files['file']
    if not file or file.filename == '':
        raise BadRequest('No selected file')
    
    # Validate file type
    if not allowed_file(file.filename):
        raise BadRequest('File type not allowed')
    
    try:
        # Save the document
        metadata = {
            'title': request.form.get('title', file.filename),
            'document_type': request.form.get('document_type'),
            'document_number': request.form.get('document_number'),
            'user_id': user.id
        }
        
        document = document_service.save_document(file, metadata)
        
        # Return the created document
        return jsonify({
            'id': document.id,
            'title': document.title,
            'document_type': document.document_type,
            'file_type': document.file_type,
            'file_size': document.file_size,
            'is_processed': document.is_processed,
            'created_at': document.created_at.isoformat(),
            'processing_error': document.processing_error
        }), 201
        
    except Exception as e:
        current_app.logger.error(f'Error uploading document: {str(e)}', exc_info=True)
        raise BadRequest(str(e))

@api_bp.route('/documents', methods=['GET'])
@jwt_required()
def list_documents():
    """
    List documents with pagination and filtering.
    
    Query parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20)
    - document_type: Filter by document type
    - search: Search in document title or content
    - is_processed: Filter by processing status (true/false)
    """
    user = get_current_user()
    
    # Parse query parameters
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    
    # Build query
    query = Document.query
    
    # Apply filters
    if 'document_type' in request.args:
        query = query.filter(Document.document_type == request.args['document_type'])
    
    if 'is_processed' in request.args:
        is_processed = request.args['is_processed'].lower() == 'true'
        query = query.filter(Document.is_processed == is_processed)
    
    if 'search' in request.args:
        search = f"%{request.args['search']}%"
        query = query.filter(Document.title.ilike(search))
    
    # Order by creation date (newest first)
    query = query.order_by(Document.created_at.desc())
    
    # Execute paginated query
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    documents = pagination.items
    
    return jsonify({
        'items': [{
            'id': doc.id,
            'title': doc.title,
            'document_type': doc.document_type,
            'file_type': doc.file_type,
            'file_size': doc.file_size,
            'is_processed': doc.is_processed,
            'created_at': doc.created_at.isoformat(),
            'processing_error': doc.processing_error
        } for doc in documents],
        'pagination': {
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        }
    })

@api_bp.route('/documents/<int:document_id>', methods=['GET'])
@jwt_required()
def get_document(document_id):
    """Get details of a specific document."""
    user = get_current_user()
    
    document = Document.query.get_or_404(document_id)
    
    return jsonify({
        'id': document.id,
        'title': document.title,
        'document_type': document.document_type,
        'document_number': document.document_number,
        'original_filename': document.original_filename,
        'file_type': document.file_type,
        'file_size': document.file_size,
        'is_processed': document.is_processed,
        'processing_error': document.processing_error,
        'created_at': document.created_at.isoformat(),
        'updated_at': document.updated_at.isoformat() if document.updated_at else None,
        'pages': [{
            'page_number': page.page_number,
            'has_text': bool(page.text)
        } for page in document.pages]
    })

@api_bp.route('/documents/<int:document_id>/content', methods=['GET'])
@jwt_required()
def get_document_content(document_id):
    """Get the text content of a document."""
    user = get_current_user()
    
    document = Document.query.get_or_404(document_id)
    
    if not document.is_processed:
        raise BadRequest('Document processing is not complete')
    
    pages = DocumentPage.query.filter_by(document_id=document_id)\
                            .order_by(DocumentPage.page_number)\
                            .all()
    
    return jsonify({
        'document_id': document.id,
        'title': document.title,
        'pages': [{
            'page_number': page.page_number,
            'text': page.text,
            'ocr_confidence': page.ocr_confidence,
            'is_scanned': page.is_scanned
        } for page in pages]
    })

@api_bp.route('/documents/<int:document_id>/process', methods=['POST'])
@jwt_required()
def process_document(document_id):
    """Trigger processing of a specific document."""
    user = get_current_user()
    
    document = Document.query.get_or_404(document_id)
    
    if document.is_processed:
        return jsonify({
            'status': 'already_processed',
            'message': 'Document is already processed'
        })
    
    # Process the document in the background
    from ..tasks import process_document_task
    task = process_document_task.delay(document_id)
    
    return jsonify({
        'status': 'processing_started',
        'task_id': task.id,
        'document_id': document_id
    }), 202

# Search endpoint
@api_bp.route('/search', methods=['GET'])
@jwt_required()
def search_documents():
    """Search documents by content."""
    user = get_current_user()
    
    query = request.args.get('q')
    if not query:
        raise BadRequest('Search query is required')
    
    # TODO: Implement search functionality
    # This is a placeholder implementation
    results = []
    
    return jsonify({
        'query': query,
        'results': results,
        'total': len(results)
    })
