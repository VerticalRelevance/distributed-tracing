import argparse
import webbrowser
import threading
import time
from typing import Dict, Any, Optional
import logging
from fastcore.foundation import *
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import HTMLResponse
import uvicorn
from common.configuration import Configuration
from call_tracer.renderers.renderer import RendererObject
from source_analyzer.main import SourceCodeAnalyzer


STATIC_FILES_LOCATION = "call_tracer/renderers/fasthtml_renderer/static"

logger = logging.getLogger(__name__)

async def generate_node_content(node: Dict[str, Any]) -> str:
    """Generate sample markdown content for a node.
    This function waits for 5 seconds to simulate a time-consuming operation."""

    # Generate detailed markdown content
    logger.debug(f"call process_file with '{node.get('file_path')}")
    try:
        details = SourceCodeAnalyzer().process_file(input_source_path=node.get("file_path"))
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(str(e))
        details = str(e)

    logger.debug(f"call process_file finished details len: {len(details)}")
    return details


# Define the FastHtmlRenderer class
class FastHtmlRenderer(RendererObject):
    def __init__(
        self, configuration: Configuration, data: Dict[str, Any] = None, *args, **kwargs
    ):
        """Initialize the renderer with either a JSON data file path or a data dictionary."""
        # self.data_file = data_file

        # # If data is provided directly, use it; otherwise load from file
        # if data is not None:
        #     self.data = data
        # elif data_file:
        #     self.data = self.load_data()
        # else:
        #     self.data = {}

        super().__init__(configuration=configuration, data=data)

        # Create the Starlette app
        self.app = Starlette(
            debug=True,
            routes=[
                Route("/", self.index),
                Route("/node/{node_id}", self.get_node_details),
                Route("/node/{node_id}/content", self.get_node_content),
                Mount(
                    "/static",
                    StaticFiles(directory=STATIC_FILES_LOCATION),
                    name="static",
                ),
            ],
        )

    def run(self, host="127.0.0.1", port=8000, open_browser=False):
        """Run the FastHTML application."""
        # If open_browser is True, open the browser after a short delay
        if open_browser:
            url = f"http://{host}:{port}"
            threading.Thread(target=lambda: self._open_browser(url)).start()

        # Run the Uvicorn server
        uvicorn.run(self.app, host=host, port=port)

    def _open_browser(self, url):
        """Helper method to open the browser after a short delay."""
        time.sleep(1)  # Give the server a moment to start
        webbrowser.open(url)

    def render(self):
        host: str = "127.0.0.1"
        port: int = 8000
        open_browser: bool = True

        # If open_browser is True, open the browser after a short delay
        if open_browser:
            url = f"http://{host}:{port}"
            threading.Thread(target=lambda: self._open_browser(url)).start()

        # Run the Uvicorn server
        uvicorn.run(self.app, host=host, port=port)

    def _open_browser(self, url):
        """Helper method to open the browser after a short delay."""
        time.sleep(1)  # Give the server a moment to start
        webbrowser.open(url)
        # self.run(host=host, port=port, open_browser=True)
        # self.run(open_browser=True)

    async def index(self, request: Request) -> HTMLResponse:
        """Render the main index page with the tree view."""
        return HTMLResponse(self.render_page())

    async def get_node_details(self, request: Request) -> HTMLResponse:
        """Render the details form for a specific node."""
        node_id = request.path_params["node_id"]
        node = self.find_node_by_id(self.data, node_id)

        if not node:
            return HTMLResponse("<p>Node not found</p>")

        # Return the form with loading state
        return HTMLResponse(self.generate_node_details(node_id))

    async def get_node_content(self, request: Request) -> HTMLResponse:
        """Fetch the content for a node using the external function."""
        node_id = request.path_params["node_id"]
        node = self.find_node_by_id(self.data, node_id)

        if not node:
            return HTMLResponse("<p>Node not found</p>", status_code=404)

        # Generate the content using the separate method
        content = await generate_node_content(node)
        return HTMLResponse(content)

    def find_node_by_id(
        self, node: Dict[str, Any], node_id: str
    ) -> Optional[Dict[str, Any]]:
        """Find a node in the tree by its ID."""
        if node.get("id") == node_id:
            return node

        if "calls" in node:
            for call in node["calls"]:
                result = self.find_node_by_id(call, node_id)
                if result:
                    return result

        return None

    def generate_node_details(self, node_id: str) -> str:
        """Generate HTML form for node details with loading state.
        This method only creates the form structure and loading state,
        the actual content is fetched separately."""
        return f"""
        <div id="loading-indicator">
            <p>Loading node details... Please be patient as this could take some time.</p>
            <div class="spinner"></div>
        </div>

        <div id="node-content" style="display: none;"></div>

        <script>
            // Immediately start fetching the content
            fetch('/node/{node_id}/content')
                .then(response => {{
                    if (!response.ok) {{
                        throw new Error('Network response was not ok');
                    }}
                    return response.text();
                }})
                .then(content => {{
                    // Hide loading indicator
                    document.getElementById('loading-indicator').style.display = 'none';

                    // Show and populate content with parsed markdown
                    const contentElement = document.getElementById('node-content');
                    contentElement.innerHTML = marked.parse(content);
                    contentElement.style.display = 'block';
                }})
                .catch(error => {{
                    console.error('Error fetching content:', error);
                    document.getElementById('loading-indicator').innerHTML =
                        '<p>Error loading content. Please try again.</p>';
                }});
        </script>
        """

    def render_tree_node(self, node: Dict[str, Any], level: int = 0) -> str:
        """Render a single node in the tree."""
        node_id = node.get("id", "")
        name = node.get("name", "Unknown")
        node_type = node.get("type", "Unknown")
        file_path = node.get("file_path", "")

        # Determine if node is selectable (has file_path)
        is_selectable = bool(file_path)
        selectable_class = "selectable" if is_selectable else ""

        # Only add the htmx attributes if the node is selectable
        htmx_attrs = (
            f'hx-get="/node/{node_id}" hx-target="#popup-content" hx-swap="innerHTML" onclick="showPopup()"'
            if is_selectable
            else ""
        )

        html = f"""
        <li>
            <div class="node {selectable_class}" {htmx_attrs}>
                <span class="function-name">{name}</span>
                <span class="type-label">({node_type})</span>
                {f'<div class="file-path">{file_path}</div>' if file_path else ''}
            </div>
        """

        # If the node has calls, make them collapsible
        calls = node.get("calls", [])
        if calls:
            html += f"""
            <details>
                <summary>Calls ({len(calls)})</summary>
                <ul>
            """

            for call in calls:
                html += self.render_tree_node(call, level + 1)

            html += """
                </ul>
            </details>
            """

        html += "</li>"
        return html

    def render_page(self) -> str:
        """Render the full HTML page with the tree structure."""
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Call Tracer Visualizer</title>
            <link rel="stylesheet" href="/static/styles.css">
            <script src="https://cdnjs.cloudflare.com/ajax/libs/htmx/1.9.2/htmx.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/4.3.0/marked.min.js"></script>
        </head>
        <body>
            <h1>Call Tracer Visualizer</h1>

            <div class="container">
                <div class="tree-container">
                    <h2>Function Call Tree</h2>
                    <div class="tree">
                        <ul>
                            {self.render_tree_node(self.data)}
                        </ul>
                    </div>
                </div>
            </div>

            <!-- Popup for node details -->
            <div class="popup-overlay" id="popup-overlay">
                <div class="popup-container">
                    <button class="close-button" onclick="hidePopup()">&times;</button>
                    <div id="popup-content" class="markdown-content">
                        <p>Loading details...</p>
                    </div>
                </div>
            </div>

            <script>
                function showPopup() {{
                    document.getElementById('popup-overlay').style.display = 'flex';
                }}

                function hidePopup() {{
                    document.getElementById('popup-overlay').style.display = 'none';
                }}

                // Add selected class to clicked nodes
                document.addEventListener('click', function(e) {{
                    const node = e.target.closest('.node.selectable');
                    if (node) {{
                        document.querySelectorAll('.node').forEach(n => n.classList.remove('selected'));
                        node.classList.add('selected');
                    }}
                }});

                // Close popup when clicking outside
                document.getElementById('popup-overlay').addEventListener('click', function(e) {{
                    if (e.target === this) {{
                        hidePopup();
                    }}
                }});

                // Close popup with escape key
                document.addEventListener('keydown', function(e) {{
                    if (e.key === 'Escape') {{
                        hidePopup();
                    }}
                }});
            </script>
        </body>
        </html>
        """


def main():
    parser = argparse.ArgumentParser(description="FastHTML Call Tracer Visualizer")
    parser.add_argument("json_file", help="Path to the JSON call tracer file")
    args = parser.parse_args()

    renderer = FastHtmlRenderer(args.json_file)
    renderer.run(open_browser=True)


if __name__ == "__main__":
    main()
