"""
Loads the CHIMera Explorer server extension (from the 'qoffeeapi' package).

This extension now primarily provides a system health check endpoint,
reflecting the project's focus as an offline Quantum Combinatorics Explorer.
"""
from notebook.utils import url_path_join
from .api_orchestrator import OrchestratorHealthCheckHandler # Import the health check handler

def load_jupyter_server_extension(nb_server_app):
    """
    Called when the extension is loaded.
    Args:
        nb_server_app (NotebookWebApplication): handle to the Notebook webserver instance.
    """
    web_app = nb_server_app.web_app
    host_pattern = '.*$'
    
    # Add Health Check Endpoint
    health_route_pattern = url_path_join(web_app.settings['base_url'], '/api/health')
    web_app.add_handlers(host_pattern, [(health_route_pattern, OrchestratorHealthCheckHandler)])

    nb_server_app.log.info("CHIMeraAPI (within qoffeeapi package for CHIMera Explorer) extension loaded with Health Check.")
