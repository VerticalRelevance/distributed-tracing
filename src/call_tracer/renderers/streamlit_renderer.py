# pylint: disable=line-too-long
"""
A Streamlit application for visualizing Python method call trees from a JSON file.

This module provides a user interface to explore and navigate through function call hierarchies,
displaying details about each function call node. The application loads a JSON file containing
function call data and renders it as an interactive tree structure.

The main components include:
- StreamlitRenderer: A class that creates an interactive tree visualization
- Interactive tree navigation with expand/collapse functionality
- Node selection and detail viewing
- Command-line interface for JSON file input

Usage:
    python streamlit_renderer.py <json_file_path>

Example:
    python streamlit_renderer.py call_trace.json
"""
# pylint: enable=line-too-long

import sys
import json
from typing import Dict, Any
import streamlit as st
from call_tracer.renderers.renderer import RendererObject
from common.configuration import Configuration


class StreamlitRenderer(RendererObject):
    # pylint: disable=line-too-long
    """
    A class that renders a Python method call tree in a Streamlit application.

    This class loads function call data from a JSON file and creates an interactive UI to explore
    the call hierarchy. Users can expand/collapse nodes, select nodes to view details, and navigate
    through the call tree.

    The renderer maintains session state for node expansion and selection, providing a persistent
    user experience across interactions. It creates a two-column layout with the call tree on the
    left and node details on the right.

    Attributes:
        json_file_path (str): Path to the JSON file containing the function call data.
        data (Dict[str, Any]): The loaded JSON data representing the function call tree.
    """
    # pylint: enable=line-too-long

    def __init__(self, configuration: Configuration, data: Dict[str, Any]):
        # pylint: disable=line-too-long
        """
        Initialize the StreamlitRenderer with configuration and data.

        Sets up the renderer by loading the JSON data and initializing Streamlit session state
        for node selection and expansion tracking. The first level of nodes is expanded by default.

        Args:
            configuration (Configuration): Configuration object containing renderer settings.
            data (Dict[str, Any]): The function call data to be rendered as a tree structure.
        """
        # pylint: enable=line-too-long

        super().__init__(configuration=configuration, data=data)

        self.json_file_path = None
        self.data = self._load_json()

        # Initialize session state for selected node if it doesn't exist
        if "selected_node" not in st.session_state:
            st.session_state.selected_node = None

        # Initialize session state for expanded nodes if it doesn't exist
        if "expanded_nodes" not in st.session_state:
            st.session_state.expanded_nodes = set()
            # Default to expand the first level
            for key in self.data.keys():
                st.session_state.expanded_nodes.add(key)

    def _load_json(self) -> Dict[str, Any]:
        # pylint: disable=line-too-long
        """
        Load the JSON data from the instance data or file.

        Returns the data that was passed to the constructor. If json_file_path is set,
        attempts to read and parse the JSON file. If the file cannot be loaded or parsed,
        displays an error message in the Streamlit UI and returns an empty dictionary.

        Returns:
            Dict[str, Any]: The loaded JSON data as a dictionary. Returns the instance data
                           if no file path is set, or an empty dictionary if loading fails.

        Raises:
            Exception: Displays an error message in the Streamlit UI if the JSON file cannot be loaded.
        """
        # pylint: enable=line-too-long

        if self.json_file_path is None:
            return {}

        try:
            with open(self.json_file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:  # pylint: disable=broad-exception-caught
            st.error(f"Error loading JSON file: {e}")
            return {}

    def toggle_node(self, node_id: str):
        # pylint: disable=line-too-long
        """
        Toggle the expanded/collapsed state of a node.

        If the node is currently expanded, it will be collapsed. If it's collapsed, it will be
        expanded. This affects the visibility of the node's children in the tree view.

        Args:
            node_id (str): The ID of the node to toggle.
        """
        # pylint: enable=line-too-long

        if node_id in st.session_state.expanded_nodes:
            st.session_state.expanded_nodes.remove(node_id)
        else:
            st.session_state.expanded_nodes.add(node_id)

    def select_node(self, node_id: str):
        # pylint: disable=line-too-long
        """
        Select a node to display its details.

        Updates the session state to mark the specified node as selected, which will cause
        its details to be displayed in the details panel.

        Args:
            node_id (str): The ID of the node to select.
        """
        # pylint: enable=line-too-long

        st.session_state.selected_node = node_id

    def _get_node_details(self, node_id: str) -> str:
        # pylint: disable=line-too-long
        """
        Get detailed information about a specific node.

        This function searches for the node in the data structure and returns formatted details
        about the node if found. It handles both root-level nodes and nested call nodes,
        extracting relevant information such as file paths, line numbers, and function names.

        Args:
            node_id (str): The ID of the node to get details for.

        Returns:
            str: Formatted markdown string containing the node details, or an error message
                 if the node is not found.
        """
        # pylint: enable=line-too-long

        # Find the node in the data
        for key, value in self.data.items():
            if key == node_id:
                return (
                    f"# {key}\n\n**File Path:** {value.get('file_path', 'N/A')}"
                    "\n\n**Name:** {value.get('name', 'N/A')}"
                )

            # Check in calls list
            if "calls" in value:
                for call in value["calls"]:
                    if call.get("id") == node_id:
                        details = [
                            f"# {call.get('qualified_name', 'Unknown')}\n",
                            f"**ID:** {call.get('id', 'N/A')}\n",
                            f"**Line Number:** {call.get('lineno', 'N/A')}\n",
                            f"**Column Offset:** {call.get('col_offset', 'N/A')}\n",
                        ]

                        if "object" in call:
                            details.append(f"**Object:** {call.get('object', 'N/A')}\n")

                        if "not_found" in call:
                            details.append(f"**Not Found:** {call.get('not_found')}\n")

                        if "is_self_attribute" in call:
                            details.append(
                                f"**Is Self Attribute:** {call.get('is_self_attribute')}\n"
                            )

                        return "".join(details)

        return f"# No details found for node: {node_id}"

    def _render_tree_node(self, key: str, value: Dict[str, Any], level: int = 0):
        # pylint: disable=line-too-long
        """
        Render a tree node and its children recursively.

        This function creates the UI elements for each node in the tree, including buttons for
        expanding/collapsing nodes and selecting nodes to view details. It handles both parent
        nodes (with children) and leaf nodes differently, providing appropriate expand/collapse
        functionality only for parent nodes.

        Args:
            key (str): The key or name of the node.
            value (Dict[str, Any]): The data associated with the node.
            level (int, optional): The indentation level of the node. Defaults to 0.
        """
        # pylint: enable=line-too-long

        indent = "  " * level

        # For the root node
        if "calls" in value:
            col1, col2, col3 = st.columns([0.7, 0.15, 0.15])
            with col1:
                if st.button(
                    f"{indent}📁 {key}", key=f"node_{key}", help="Click to view details"
                ):
                    self.select_node(key)

            with col2:
                if st.button("Expand", key=f"expand_{key}"):
                    st.session_state.expanded_nodes.add(key)

            with col3:
                if st.button("Collapse", key=f"collapse_{key}"):
                    if key in st.session_state.expanded_nodes:
                        st.session_state.expanded_nodes.remove(key)

            if key in st.session_state.expanded_nodes:
                for call in value["calls"]:
                    call_id = call.get("id")
                    qualified_name = call.get("qualified_name")

                    # Check if this call_id exists as a key in the data
                    if call_id in self.data:
                        self._render_tree_node(
                            qualified_name, self.data[call_id], level + 1
                        )
                    else:
                        if st.button(
                            f"{indent}  📄 {qualified_name}",
                            key=f"node_{call_id}",
                            help="Click to view details",
                        ):
                            self.select_node(call_id)
        else:
            # For leaf nodes
            if st.button(
                f"{indent}📄 {key}", key=f"node_{key}", help="Click to view details"
            ):
                self.select_node(key)

    def _create_menu(self):
        # pylint: disable=line-too-long
        """
        Create the menu bar with File submenu.

        This function creates a simple menu in the sidebar with options like "Close" to exit the application.
        Currently provides basic file operations, with the close option terminating the Streamlit application.
        """
        # pylint: enable=line-too-long

        menu = st.sidebar.selectbox("Menu", ["File"])

        if menu == "File":
            if st.sidebar.button("Close"):
                st.stop()

    def render(self):
        # pylint: disable=line-too-long
        """
        Main rendering function for the Streamlit app.

        This function sets up the overall layout of the application, including the title, menu,
        function call tree, and node details panel. It creates a two-column layout where the left
        column displays the interactive tree and the right column shows details of the selected node.
        """
        # pylint: enable=line-too-long

        st.title("Python Method Call Tree Viewer")

        # Create the menu
        self._create_menu()

        # Split the screen into two columns
        col1, col2 = st.columns([0.4, 0.6])

        with col1:
            st.subheader("Function Call Tree")
            # Create a container with scrollbar for the tree
            tree_container = st.container()
            with tree_container:
                for key, value in self.data.items():
                    self._render_tree_node(key, value)

        with col2:
            st.subheader("Node Details")
            if st.session_state.selected_node:
                # Create a container with scrollbar for the markdown
                details_container = st.container()
                with details_container:
                    st.markdown(self._get_node_details(st.session_state.selected_node))
            else:
                st.info("Select a node to view details")


# pylint: disable=line-too-long
def main():
    """
    Main entry point for the Streamlit application.

    This function handles command-line argument parsing and initializes the StreamlitRenderer
    with the provided JSON file path. It validates that a JSON file path is provided as a
    command-line argument before starting the application.

    Raises:
        SystemExit: If no JSON file path is provided as a command-line argument.
    """
    # pylint: enable=line-too-long

    if len(sys.argv) < 2:
        st.error("Please provide a JSON file path as a command line argument.")
        st.stop()

    main_json_file_path = sys.argv[1]
    app = StreamlitRenderer(main_json_file_path)
    app.render()

if __name__ == "__main__":
    main()
