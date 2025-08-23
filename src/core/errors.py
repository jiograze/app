"""Error handlers for the application."""
from flask import jsonify, render_template
from werkzeug.exceptions import HTTPException

def register_error_handlers(app):
    """Register error handlers for the application."""
    @app.errorhandler(400)
    def bad_request_error(error):
        if _wants_json_response():
            return jsonify({
                'error': 'bad_request',
                'message': 'The request was invalid or cannot be served.'
            }), 400
        return render_template('errors/400.html'), 400

    @app.errorhandler(401)
    def unauthorized_error(error):
        if _wants_json_response():
            return jsonify({
                'error': 'unauthorized',
                'message': 'Authentication is required to access this resource.'
            }), 401
        return render_template('errors/401.html'), 401

    @app.errorhandler(403)
    def forbidden_error(error):
        if _wants_json_response():
            return jsonify({
                'error': 'forbidden',
                'message': 'You do not have permission to access this resource.'
            }), 403
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        if _wants_json_response():
            return jsonify({
                'error': 'not_found',
                'message': 'The requested resource was not found.'
            }), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(405)
    def method_not_allowed_error(error):
        if _wants_json_response():
            return jsonify({
                'error': 'method_not_allowed',
                'message': 'The method is not allowed for the requested URL.'
            }), 405
        return render_template('errors/405.html'), 405

    @app.errorhandler(500)
    def internal_server_error(error):
        if _wants_json_response():
            return jsonify({
                'error': 'internal_server_error',
                'message': 'An unexpected error occurred on the server.'
            }), 500
        return render_template('errors/500.html'), 500

def _wants_json_response():
    """Check if the client prefers JSON response."""
    from flask import request
    return request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']
