# pylint: disable=line-too-long
"""
A module for rendering call trace data in an interactive HTML visualization.

This module provides a FastHTML renderer that creates an interactive web interface for exploring
call trace data. It uses Starlette and Uvicorn to serve the visualization and includes features
like dynamic content loading, tree navigation, and source code analysis.
"""
# pylint: enable=line-too-long

import json
import sys
import webbrowser
import threading
import time
from typing import Dict, Any, Optional
import logging
from fastcore.foundation import *   # pylint: disable=wildcard-import, unused-wildcard-import
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
    # pylint: disable=line-too-long
    """
    Generate detailed markdown content for a node by analyzing its source code.

    Args:
        node: A dictionary containing node information, including file_path.

    Returns:
        str: Markdown-formatted content with details about the source code.
    """
    # pylint: enable=line-too-long
    # Generate detailed markdown content
    logger.debug(f"call process_file with '{node.get('file_path')}")
    details = SourceCodeAnalyzer().process_file(input_source_path=node.get("file_path"))
    logger.debug(f"call process_file finished details len: {len(details)}")
    return details


class FastHtmlRenderer(RendererObject):
    # pylint: disable=line-too-long
    """
    A renderer that creates an interactive HTML visualization for call trace data.

    This renderer uses Starlette to serve a web application that displays call trace data
    in a hierarchical tree view with detailed information available on demand.
    """
    # pylint: enable=line-too-long

    def __init__(
        self, configuration: Configuration, data: Dict[str, Any]
    ):
        # pylint: disable=line-too-long
        """
        Initialize the FastHTML renderer with configuration and call trace data.

        Args:
            configuration: Configuration object containing renderer settings.
            data: Dictionary containing the call trace data to visualize.
        """
        # pylint: enable=line-too-long
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
        # pylint: disable=line-too-long
        """
        Run the FastHTML application server.

        Args:
            host: The hostname to bind the server to. Defaults to "127.0.0.1".
            port: The port to bind the server to. Defaults to 8000.
            open_browser: Whether to automatically open a browser window. Defaults to False.
        """
        # pylint: enable=line-too-long
        # If open_browser is True, open the browser after a short delay
        if open_browser:
            url = f"http://{host}:{port}"
            threading.Thread(target=lambda: self._open_browser(url)).start()

        # Run the Uvicorn server
        uvicorn.run(self.app, host=host, port=port)

    def _open_browser(self, url):
        # pylint: disable=line-too-long
        """
        Helper method to open the browser after a short delay.

        Args:
            url: The URL to open in the browser.
        """
        # pylint: enable=line-too-long
        time.sleep(1)  # Give the server a moment to start
        webbrowser.open(url)

    def render(self):
        # pylint: disable=line-too-long
        """
        Render the visualization by starting the web server and opening a browser.

        This method starts the Uvicorn server with default settings and opens a browser
        window pointing to the visualization.
        """
        # pylint: enable=line-too-long
        host: str = "127.0.0.1"
        port: int = 8000
        open_browser: bool = True

        # If open_browser is True, open the browser after a short delay
        if open_browser:
            url = f"http://{host}:{port}"
            threading.Thread(target=lambda: self._open_browser(url)).start()

        # Run the Uvicorn server
        uvicorn.run(self.app, host=host, port=port)

    async def index(self, request: Request) -> HTMLResponse:    # pylint: disable=unused-argument
        # pylint: disable=line-too-long
        """
        Render the main index page with the tree view.

        Args:
            request: The incoming HTTP request.

        Returns:
            HTMLResponse: The rendered HTML page.
        """
        # pylint: enable=line-too-long
        return HTMLResponse(self.render_page())

    async def get_node_details(self, request: Request) -> HTMLResponse:
        # pylint: disable=line-too-long
        """
        Render the details form for a specific node.

        Args:
            request: The incoming HTTP request containing the node_id path parameter.

        Returns:
            HTMLResponse: HTML content for the node details form or an error message if node not found.
        """
        # pylint: enable=line-too-long
        node_id = request.path_params["node_id"]
        node = self.find_node_by_id(self.data, node_id)

        if not node:
            return HTMLResponse("<p>Node not found</p>")

        # Return the form with loading state
        return HTMLResponse(self.generate_node_details(node_id))

    async def get_node_content(self, request: Request) -> HTMLResponse:
        # pylint: disable=line-too-long
        """
        Fetch the detailed content for a node using the source code analyzer.

        Args:
            request: The incoming HTTP request containing the node_id path parameter.

        Returns:
            HTMLResponse: HTML content with the node details or an error message if node not found.
        """
        # pylint: enable=line-too-long
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
        # pylint: disable=line-too-long
        """
        Find a node in the tree by its ID using recursive search.

        Args:
            node: The current node to check.
            node_id: The ID of the node to find.

        Returns:
            Optional[Dict[str, Any]]: The found node or None if not found.
        """
        # pylint: enable=line-too-long
        if node.get("id") == node_id:
            return node

        if "calls" in node:
            for call in node["calls"]:
                result = self.find_node_by_id(call, node_id)
                if result:
                    return result

        return None

    def generate_node_details(self, node_id: str) -> str:
        # pylint: disable=line-too-long
        """
        Generate HTML form for node details with loading state.

        This method creates the form structure and loading state, with the actual content
        fetched asynchronously.

        Args:
            node_id: The ID of the node to generate details for.

        Returns:
            str: HTML content with loading indicator and JavaScript for fetching node details.
        """
        # pylint: enable=line-too-long
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
        # pylint: disable=line-too-long
        """
        Render a single node in the tree as HTML.

        Args:
            node: The node data to render.
            level: The nesting level of the node in the tree. Defaults to 0.

        Returns:
            str: HTML representation of the node and its children.
        """
        # pylint: enable=line-too-long
        node_id = node.get("id", "")
        name = node.get("name", "Unknown")
        node_type = node.get("type", "Unknown")
        file_path = node.get("file_path", "")

        # Determine if node is selectable (has file_path)
        is_selectable = bool(file_path)
        selectable_class = "selectable" if is_selectable else ""

        # Only add the htmx attributes if the node is selectable
        htmx_attrs = (
            f'hx-get="/node/{node_id}" hx-target="#popup-content" hx-swap="innerHTML" '
            'hx-trigger="click" onclick="showPopup()"'
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
        # pylint: disable=line-too-long
        """
        Render the full HTML page with the tree structure.

        Returns:
            str: Complete HTML document for the visualization page.
        """
        # pylint: enable=line-too-long
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
                        <!-- Content will be loaded here -->
                    </div>
                </div>
            </div>

            <script>
                function showPopup() {{
                    // Show the popup immediately when a node is clicked
                    document.getElementById('popup-overlay').style.display = 'flex';

                    // Add initial loading state to popup content
                    document.getElementById('popup-content').innerHTML = `
                        <div id="loading-indicator">
                            <p>Loading node details... Please be patient as this could take some time.</p>
                            <div class="spinner"></div>
                        </div>
                    `;
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
    # pylint: disable=line-too-long
    """
    Main entry point for running the FastHTML renderer as a standalone application.

    Parses command line arguments, loads the call trace data from a JSON file,
    and starts the renderer.
    """
    # pylint: enable=line-too-long
    def load_data(self) -> Dict[str, Any]:
        # pylint: disable=line-too-long
        """
        Load the JSON data from the specified file.

        Returns:
            Dict[str, Any]: The loaded JSON data.

        Raises:
            SystemExit: If there's an error loading the JSON data.
        """
        # pylint: enable=line-too-long
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Error loading JSON data: {e}")
            sys.exit(1)

    main_data = load_data(sys.argv[1])

    main_configuration = Configuration(config_file_path="call_tracer/config.yaml")
    renderer: RendererObject = FastHtmlRenderer(configuration=main_configuration, data=main_data)
    renderer.run(open_browser=True)


if __name__ == "__main__":
    main()
