import streamlit as st
import json
import sys
import os
from typing import Dict, List, Any, Union, Optional


def load_json_file(file_path: str) -> Dict:
    """Load JSON data from a file."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
        return {}
    except json.JSONDecodeError:
        st.error(f"Invalid JSON format in file: {file_path}")
        return {}
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return {}


def display_json_node(
    data: Any, key: str, path: str, expanded_paths: Dict[str, bool]
) -> None:
    """Display a single JSON node with expand/collapse functionality."""
    current_path = f"{path}/{key}" if path else key
    is_expanded = expanded_paths.get(current_path, False)

    # Create a container for this node
    container = st.container()

    # Display the node with expand/collapse button
    col1, col2 = container.columns([0.05, 0.95])

    # Show expand/collapse icon
    if isinstance(data, (dict, list)) and data:  # Non-empty dict or list
        if is_expanded:
            if col1.button("➖", key=f"btn_{current_path}"):
                expanded_paths[current_path] = False
                st.rerun()
        else:
            if col1.button("➕", key=f"btn_{current_path}"):
                expanded_paths[current_path] = True
                st.rerun()
    else:
        col1.write("🔹")

    # Display the key and value
    if isinstance(data, (dict, list)) and data:
        if isinstance(data, dict):
            col2.write(f"**{key}** (Object with {len(data)} keys)")
        else:
            col2.write(f"**{key}** (Array with {len(data)} items)")

        # If expanded, show the children
        if is_expanded:
            child_container = container.container()
            with child_container:
                st.markdown('<div style="margin-left: 20px">', unsafe_allow_html=True)
                display_json_tree(data, current_path, expanded_paths)
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        # For simple values
        col2.write(f"**{key}**: {data}")


def display_json_tree(
    data: Any, path: str = "", expanded_paths: Dict[str, bool] = None
) -> None:
    """Recursively display JSON data as an expandable/collapsible tree."""
    if expanded_paths is None:
        expanded_paths = {}

    # Handle different data types
    if isinstance(data, dict):
        # For dictionaries, create an entry for each key
        for key, value in data.items():
            display_json_node(value, key, path, expanded_paths)

    elif isinstance(data, list):
        # For lists, handle each item
        if not data:  # Empty list
            st.write("[ ]")
        elif all(
            isinstance(item, (str, int, float, bool, type(None))) for item in data
        ):
            # For lists of simple values, display them directly
            for i, item in enumerate(data):
                st.write(f"{i}: {item}")
        else:
            # For lists of complex objects
            for i, item in enumerate(data):
                display_json_node(item, f"Item {i}", path, expanded_paths)
    else:
        # For simple values
        st.write(data)


def main():
    st.set_page_config(
        page_title="JSON Tree Viewer",
        page_icon="🌳",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("JSON Tree Viewer")

    # Use session state to store expanded paths
    if "expanded_paths" not in st.session_state:
        st.session_state.expanded_paths = {}

    # Sidebar controls
    st.sidebar.header("Controls")

    # File path input
    file_path = st.sidebar.text_input(
        "Enter JSON file path:", value=st.session_state.get("file_path", "")
    )

    # Save the file path in session state
    if file_path:
        st.session_state.file_path = file_path

    # File uploader as an alternative
    uploaded_file = st.sidebar.file_uploader("Or upload a JSON file:", type=["json"])

    # Option to expand all nodes
    if st.sidebar.button("Expand all nodes"):
        st.session_state.expand_all = True
        st.rerun()

    # Option to collapse all nodes
    if st.sidebar.button("Collapse all nodes"):
        st.session_state.expanded_paths = {}
        st.rerun()

    # Load data
    data = {}

    # Check command line arguments for file path
    if len(sys.argv) > 1 and not file_path:
        file_path = sys.argv[1]
        st.session_state.file_path = file_path

    if uploaded_file is not None:
        # If a file is uploaded, use that
        try:
            data = json.load(uploaded_file)
            st.sidebar.success(f"Loaded uploaded file")
        except Exception as e:
            st.sidebar.error(f"Error loading uploaded file: {str(e)}")
    elif file_path:
        # Otherwise use the file path
        data = load_json_file(file_path)
        if data:
            st.sidebar.success(f"Loaded file: {file_path}")

    # Handle expand all if needed
    if hasattr(st.session_state, "expand_all") and st.session_state.expand_all:

        def set_all_expanded(d, path=""):
            if isinstance(d, dict):
                for k, v in d.items():
                    current_path = f"{path}/{k}" if path else k
                    st.session_state.expanded_paths[current_path] = True
                    if isinstance(v, (dict, list)):
                        set_all_expanded(v, current_path)
            elif isinstance(d, list):
                for i, item in enumerate(d):
                    current_path = f"{path}/{i}" if path else str(i)
                    st.session_state.expanded_paths[current_path] = True
                    if isinstance(item, (dict, list)):
                        set_all_expanded(item, current_path)

        set_all_expanded(data)
        st.session_state.expand_all = False

    # Display the JSON tree
    if data:
        display_json_tree(data, expanded_paths=st.session_state.expanded_paths)
    else:
        st.info("No data to display. Please enter a file path or upload a JSON file.")

        # Show usage instructions
        st.markdown(
            """
        ## Usage Instructions

        ### Option 1: Enter a file path
        Enter the full path to your JSON file in the text input field in the sidebar.

        ### Option 2: Upload a JSON file
        Use the file uploader in the sidebar to upload a JSON file.

        ### Option 3: Command line parameter
        Run the app with a file path as a parameter:
        ```
        streamlit run json_tree_viewer.py /path/to/your/file.json
        ```
        """
        )


if __name__ == "__main__":
    main()
