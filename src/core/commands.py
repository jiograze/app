"""CLI commands for the application."""
import click
from flask.cli import with_appcontext
from flask_migrate import upgrade


def init_app(app):
    ""Register CLI commands with the application.""
    app.cli.add_command(init_db)
    app.cli.add_command(create_admin)
    app.cli.add_command(process_documents)


@click.command('init-db')
@with_appcontext
def init_db():
    """Initialize the database."""
    from mevzuat import db
    
    click.echo('Creating database tables...')
    db.create_all()
    
    click.echo('Running database migrations...')
    upgrade()
    
    click.echo('Database initialized.')


@click.command('create-admin')
@click.argument('username')
@click.argument('email')
@click.argument('password')
@with_appcontext
def create_admin(username, email, password):
    """Create an admin user."""
    from werkzeug.security import generate_password_hash
    from mevzuat.core.models import User
    from mevzuat import db
    
    if User.query.filter_by(username=username).first():
        click.echo(f'User {username} already exists.')
        return
    
    admin = User(
        username=username,
        email=email,
        password=generate_password_hash(password),
        is_admin=True,
        is_active=True
    )
    
    db.session.add(admin)
    db.session.commit()
    
    click.echo(f'Admin user {username} created successfully.')


@click.command('process-documents')
@click.option('--all', is_flag=True, help='Process all unprocessed documents')
@click.option('--document-id', type=int, help='Process a specific document by ID')
@with_appcontext
def process_documents(all, document_id):
    """Process documents in the background."""
    from mevzuat.core.services.document_service import DocumentService
    from mevzuat import db
    
    service = DocumentService()
    
    if all:
        from mevzuat.core.models import Document
        documents = Document.query.filter_by(is_processed=False).all()
        
        if not documents:
            click.echo('No unprocessed documents found.')
            return
        
        click.echo(f'Processing {len(documents)} documents...')
        
        for doc in documents:
            try:
                service.process_document(doc)
                click.echo(f'Processed document {doc.id}: {doc.original_filename}')
            except Exception as e:
                click.echo(f'Error processing document {doc.id}: {str(e)}', err=True)
                doc.processing_error = str(e)
                db.session.add(doc)
        
        db.session.commit()
        click.echo('Document processing completed.')
    
    elif document_id:
        from mevzuat.core.models import Document
        doc = Document.query.get_or_404(document_id)
        
        try:
            service.process_document(doc)
            click.echo(f'Successfully processed document {doc.id}: {doc.original_filename}')
        except Exception as e:
            click.echo(f'Error processing document: {str(e)}', err=True)
            doc.processing_error = str(e)
            db.session.add(doc)
            db.session.commit()
    
    else:
        click.echo('Please specify --all to process all unprocessed documents or --document-id to process a specific document.')
