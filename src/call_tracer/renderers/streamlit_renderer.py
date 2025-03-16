import streamlit as st
import json
import sys
from typing import Dict, Any, Callable


class StreamlitRenderer:
    def __init__(self, json_file_path: str):
        """Initialize the StreamlitRenderer with the path to the JSON file."""
        self.json_file_path = json_file_path
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
        """Load the JSON data from the file."""
        try:
            with open(self.json_file_path, "r") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading JSON file: {e}")
            return {}

    def toggle_node(self, node_id: str):
        """Toggle the expanded/collapsed state of a node."""
        if node_id in st.session_state.expanded_nodes:
            st.session_state.expanded_nodes.remove(node_id)
        else:
            st.session_state.expanded_nodes.add(node_id)

    def select_node(self, node_id: str):
        """Select a node to display its details."""
        st.session_state.selected_node = node_id

    def _get_node_details(self, node_id: str) -> str:
        """
        External function to get details about a node.
        This would be replaced with actual implementation.
        """
        # Find the node in the data
        for key, value in self.data.items():
            if key == node_id:
                return f"# {key}\n\n**File Path:** {value.get('file_path', 'N/A')}\n\n**Name:** {value.get('name', 'N/A')}"

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
        """Render a tree node and its children recursively."""
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
        """Create the menu bar with File submenu."""
        menu = st.sidebar.selectbox("Menu", ["File"])

        if menu == "File":
            if st.sidebar.button("Close"):
                st.stop()

    def render(self):
        """Main rendering function for the Streamlit app."""
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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        st.error("Please provide a JSON file path as a command line argument.")
        st.stop()

    json_file_path = sys.argv[1]
    app = StreamlitRenderer(json_file_path)
    app.render()
