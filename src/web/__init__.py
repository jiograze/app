"""Web interface for the Mevzuat Yönetim Sistemi."""
import os
from flask import (
    Blueprint, render_template, request, redirect, 
    url_for, flash, jsonify, current_app, abort
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from ..core.models import Document, DocumentPage
from ..core.services.document_service import DocumentService
from ..core.utils.file_utils import allowed_file, get_file_extension

web_bp = Blueprint('web', __name__, template_folder='templates', static_folder='static')
document_service = DocumentService()

# Helper functions
def allowed_file_size(file):
    """Check if the file size is within allowed limits."""
    file.seek(0, os.SEEK_END)
    file_length = file.tell()
    file.seek(0)  # Reset file pointer
    return file_length <= current_app.config['MAX_CONTENT_LENGTH']

# Routes
@web_bp.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')

@web_bp.route('/documents')
@login_required
def documents():
    """Document listing page with pagination and filtering."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    query = Document.query
    
    # Apply filters
    if 'document_type' in request.args:
        query = query.filter_by(document_type=request.args['document_type'])
    
    if 'q' in request.args:
        search = f"%{request.args['q']}%"
        query = query.filter(Document.title.ilike(search))
    
    # Order by creation date (newest first)
    documents = query.order_by(Document.created_at.desc())\
                    .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('documents/list.html', documents=documents)

@web_bp.route('/documents/upload', methods=['GET', 'POST'])
@login_required
def upload_document():
    """Handle document uploads."""
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('Dosya seçilmedi', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('Dosya seçilmedi', 'error')
            return redirect(request.url)
        
        # Check file size
        if not allowed_file_size(file):
            max_size = current_app.config['MAX_CONTENT_LENGTH'] / (1024 * 1024)  # Convert to MB
            flash(f'Dosya boyutu çok büyük. Maksimum {max_size}MB olabilir.', 'error')
            return redirect(request.url)
        
        # Check file extension
        if not allowed_file(file.filename):
            allowed = ', '.join(current_app.config['ALLOWED_EXTENSIONS'])
            flash(f'Geçersiz dosya uzantısı. İzin verilen uzantılar: {allowed}', 'error')
            return redirect(request.url)
        
        try:
            # Save the document
            metadata = {
                'title': request.form.get('title', file.filename),
                'document_type': request.form.get('document_type'),
                'document_number': request.form.get('document_number'),
                'user_id': current_user.id
            }
            
            document = document_service.save_document(file, metadata)
            flash('Dosya başarıyla yüklendi ve işleniyor...', 'success')
            return redirect(url_for('web.view_document', document_id=document.id))
            
        except Exception as e:
            current_app.logger.error(f'Error uploading document: {str(e)}', exc_info=True)
            flash('Dosya yüklenirken bir hata oluştu. Lütfen tekrar deneyin.', 'error')
            return redirect(request.url)
    
    # GET request - show upload form
    return render_template('documents/upload.html')

@web_bp.route('/documents/<int:document_id>')
@login_required
def view_document(document_id):
    """View a specific document."""
    document = Document.query.get_or_404(document_id)
    
    # Check if user has permission to view this document
    if not current_user.is_admin and document.user_id != current_user.id:
        abort(403)
    
    return render_template('documents/view.html', document=document)

@web_bp.route('/documents/<int:document_id>/download')
@login_required
def download_document(document_id):
    """Download a document file."""
    document = Document.query.get_or_404(document_id)
    
    # Check if user has permission to download this document
    if not current_user.is_admin and document.user_id != current_user.id:
        abort(403)
    
    if not os.path.exists(document.file_path):
        flash('Dosya bulunamadı', 'error')
        return redirect(url_for('web.documents'))
    
    return send_from_directory(
        directory=os.path.dirname(document.file_path),
        path=os.path.basename(document.file_path),
        as_attachment=True,
        download_name=document.original_filename
    )

@web_bp.route('/search')
@login_required
def search():
    """Search documents."""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    if not query:
        return redirect(url_for('web.documents'))
    
    # Search in document titles and content
    from sqlalchemy import or_
    
    # Search in titles
    title_query = Document.query.filter(
        Document.title.ilike(f'%{query}%')
    )
    
    # Search in document content (if available)
    content_query = Document.query.join(DocumentPage).filter(
        DocumentPage.text.ilike(f'%{query}%')
    )
    
    # Combine queries and remove duplicates
    documents = title_query.union(content_query)\
                          .order_by(Document.created_at.desc())\
                          .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('search/results.html', 
                         query=query, 
                         documents=documents)

@web_bp.route('/api/documents/<int:document_id>/content')
@login_required
def get_document_content(document_id):
    """Get document content as JSON (for AJAX requests)."""
    document = Document.query.get_or_404(document_id)
    
    # Check if user has permission to view this document
    if not current_user.is_admin and document.user_id != current_user.id:
        abort(403)
    
    if not document.is_processed:
        return jsonify({
            'error': 'Doküman henüz işlenmedi',
            'status': 'processing'
        }), 202
    
    pages = DocumentPage.query.filter_by(document_id=document_id)\
                            .order_by(DocumentPage.page_number)\
                            .all()
    
    return jsonify({
        'document_id': document.id,
        'title': document.title,
        'pages': [{
            'page_number': page.page_number,
            'text': page.text,
            'is_scanned': page.is_scanned,
            'ocr_confidence': page.ocr_confidence
        } for page in pages]
    })
