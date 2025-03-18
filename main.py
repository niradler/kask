import json
import pyperclip
from typing import Any, Dict, List, Optional, Union, Generator

from rich.text import Text
from rich.syntax import Syntax
from rich.highlighter import JSONHighlighter

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import (
    Button, Footer, Header, Input, Static, TextArea, Tree, Label, Switch
)
from textual.widgets.tree import TreeNode
import model
import tools


class JsonViewerApp(App):
    """A JSON viewer application with search, filtering, and tree view."""

    CSS_PATH = "style.tcss"

    TITLE = "KasK - kubectl that will answer your questions"

    BINDINGS = [
        Binding("x", "toggle_all", "Expand/Collapse All"),
        Binding("s", "focus_search", "Search"),
        Binding("/", "focus_search", "Search"),
        Binding("c", "copy_selected", "Copy Value"),
        Binding("q", "quit", "Quit"),
    ]

    # Reactive variables
    prompt_data = reactive(None)
    is_expanded_all = reactive(False)
    search_text = reactive("")
    is_searching = reactive(False)
    has_json = reactive(False)
    selected_path = reactive("")
    selected_node = reactive(None)

    def compose(self) -> ComposeResult:
        """Compose the UI layout."""
        yield Header()

        with Container(id="main-container"):
            with Horizontal(id="input-area"):
                with Vertical(id="textarea-container"):
                    yield Label("Write your prompt here:", id="textarea-label")
                    yield TextArea(id="prompt-input", language="json")

                    with Horizontal(id="button-container"):
                        yield Button("Prompt", id="submit-button", variant="primary")
                        yield Button("Clear", id="clear-button", variant="default")

            with Vertical(id="viewer-container"):
                with Horizontal(id="search-container"):
                    yield Input(placeholder="Search JSON...", id="search-input")
                    yield Label("Case sensitive", id="case-label")
                    yield Switch(id="case-switch", name="case-sensitive")

                with VerticalScroll(id="tree-container"):
                    yield Tree("JSON", id="json-tree")

                with Container(id="info-container"):
                    yield Label("No node selected", id="path-display")
                    yield Static("", id="value-display")

        yield Footer()

    def on_mount(self) -> None:
        """Handle mount event."""
        # Set focus to the JSON input
        self.query_one("#prompt-input").focus()

        # Initialize empty tree with placeholder
        tree = self.query_one("#json-tree", Tree)
        tree.root.expand()

    def walk_nodes(self, node: Optional[TreeNode] = None) -> Generator[TreeNode, None, None]:
        """Walk through all nodes in the tree recursively.

        Args:
            node: The starting node. If None, starts from the root.

        Yields:
            Each node in the tree.
        """
        tree = self.query_one("#json-tree", Tree)
        node = node or tree.root

        # Yield the current node
        yield node

        # Recursively yield all children nodes
        for child in node.children:
            yield from self.walk_nodes(child)

    def query_to_kubectl(self, prompt: str, retryCount: int) -> str:
        print("prompt:", prompt)
        cmd = model.query(prompt)
        print("command:", cmd)
        output = tools.run_kubectl(cmd)
        if output.startswith("Error:") and retryCount > 0:
            return self.query_to_kubectl(f'Original prompt: {prompt}, previous generated: {cmd}, Error to fix: {output}', retryCount - 1)
        if output.startswith("Error:"):                
                self.notify(output, title="Error")
        else:
            self.notify(f'Command: {cmd}', title="Success")
        
        return output

    def submit(self) -> None:
        """Load JSON from the command output."""
        prompt = self.query_one("#prompt-input", TextArea).text
        output = self.query_to_kubectl(prompt, 3)
        print("output:", output)
        self.load_json(output)    

    @on(Button.Pressed, selector="#submit-button")
    def handle_load_button(self) -> None:
       self.submit()

    @on(Button.Pressed, selector="#clear-button")
    def handle_clear_button(self) -> None:
        """Clear the text area when the clear button is pressed."""
        self.query_one("#prompt-input", TextArea).clear()

    @on(Input.Submitted, selector="#search-input")
    def handle_search_input_changed(self, event: Input.Changed) -> None:
        """Handle changes to the search input."""
        self.search_text = event.value
        if event.value:
            self.is_searching = True
            self.filter_tree(event.value)
        else:
            self.is_searching = False
            self.reset_tree()

    @on(Tree.NodeSelected)
    def handle_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle node selection in the tree."""
        # Get the node data or label
        node = event.node

        # Extract node path and value
        if hasattr(node, "data") and node.data is not None:
            path = node.data.get("path", "")
            value = node.data.get("value", "")
            self.selected_path = path
            self.selected_node = node

            # Update the info display
            path_display = self.query_one("#path-display", Label)
            value_display = self.query_one("#value-display", Static)

            path_display.update(f"Path: {path}")

            # Use syntax highlighting for values when appropriate
            if isinstance(value, (dict, list)):
                try:
                    json_str = json.dumps(value, indent=2)
                    value_display.update(
                        Syntax(json_str, "json", theme="monokai"))
                except:
                    value_display.update(Text(repr(value)))
            else:
                value_display.update(Text(repr(value)))

    def action_toggle_all(self) -> None:
        """Toggle expand/collapse all nodes."""
        tree = self.query_one("#json-tree", Tree)

        # Toggle the expansion state
        self.is_expanded_all = not self.is_expanded_all

        # Apply to all nodes
        if self.is_expanded_all:
            # Expand all nodes
            for node in self.walk_nodes():
                node.expand()
        else:
            # Collapse all nodes except root
            for node in self.walk_nodes():
                if node != tree.root:
                    node.collapse()
            # Keep root expanded
            tree.root.expand()

    def action_focus_search(self) -> None:
        """Focus the search input."""
        search_input = self.query_one("#search-input", Input)
        search_input.focus()

    def action_clear_search(self) -> None:
        """Clear the search input."""
        if self.is_searching:
            search_input = self.query_one("#search-input", Input)
            search_input.value = ""
            search_input.focus()

    def action_copy_selected(self) -> None:
        """Copy selected node value to clipboard."""
        if self.selected_node:
            value = self.selected_node.data.get("value", "")
            try:
                try:
                    if isinstance(value, dict) or isinstance(value, list):
                        value = json.dumps(value, indent=2)
                    elif isinstance(value, str) and (value.startswith("{") or value.startswith("[")):
                        value = json.dumps(json.loads(value), indent=2)
                    else:
                        value = value.strip('"').strip("'")
                except Exception as e:
                    self.notify(
                        f"Failed to process value: {str(e)}", title="Error")

                pyperclip.copy(value)
                self.notify("Value copied to clipboard", title="Copy Success")
            except Exception as e:
                self.notify(f"Failed to copy: {str(e)}", title="Copy Failed")

    def load_json(self, json_text: str) -> None:
        """Load and validate JSON data."""
        if not json_text.strip():
            self.notify("No JSON data provided", title="Empty Input")
            return

        # Try to parse the JSON
        try:
            prompt_data = json.loads(json_text)
            self.prompt_data = prompt_data["items"] if "items" in prompt_data else prompt_data
            self.has_json = True
            self.populate_tree(self.prompt_data)
            # self.action_toggle_all()
            # self.notify("JSON loaded successfully", title="Success")
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON: {str(e)}"
            self.notify(error_msg, title="Error", severity="error")

    def populate_tree(self, json_data: Any) -> None:
        """Populate the tree with JSON data."""
        tree = self.query_one("#json-tree", Tree)
        tree.clear()
        tree.root.set_label("JSON Root")

        highlighter = JSONHighlighter()

        def add_node(path: str, parent: TreeNode, key: str, data: Any) -> None:
            """Add a node to the tree recursively."""
            current_path = f"{path}.{key}" if path else key

            if isinstance(data, dict):
                # Create a dictionary node
                node_label = Text.assemble(
                    Text.from_markup(f"[bold]{key}[/bold]" if key else "{}"),
                    Text(" {...}") if data else Text(" {}")
                )
                new_node = parent.add(node_label)
                new_node.data = {"path": current_path, "value": data}

                # Add child nodes
                for k, v in data.items():
                    add_node(current_path, new_node, k, v)

            elif isinstance(data, list):
                # Create a list node
                node_label = Text.assemble(
                    Text.from_markup(f"[bold]{key}[/bold]" if key else "[]"),
                    Text(f" [{len(data)} items]")
                )
                new_node = parent.add(node_label)
                new_node.data = {"path": current_path, "value": data}

                # Add child nodes
                for i, item in enumerate(data):
                    add_node(current_path, new_node, str(i), item)

            else:
                # Create a leaf node
                if key:
                    node_label = Text.assemble(
                        Text.from_markup(f"[bold]{key}[/bold]: "),
                        highlighter(repr(data))
                    )
                else:
                    node_label = highlighter(repr(data))

                new_node = parent.add(node_label)
                new_node.allow_expand = False
                new_node.data = {"path": current_path, "value": data}

        # Start building the tree
        if isinstance(json_data, dict):
            for key, value in json_data.items():
                add_node("", tree.root, key, value)
        elif isinstance(json_data, list):
            for i, item in enumerate(json_data):
                add_node("", tree.root, str(i), item)
        else:
            # Handle primitive types
            tree.root.add(highlighter(repr(json_data)))

        # Expand the root node
        tree.root.expand()

    def filter_tree(self, search_text: str) -> None:
        """Filter tree nodes based on search text."""
        if not self.has_json or not search_text:
            return

        tree = self.query_one("#json-tree", Tree)
        case_sensitive = self.query_one("#case-switch", Switch).value

        # Prepare search text based on case sensitivity
        if not case_sensitive:
            search_text = search_text.lower()

        def match_node(node: TreeNode) -> bool:
            """Check if a node matches the search criteria."""
            if not node.data:
                return False

            # Get the node's path and value
            path = str(node.data.get("path", ""))
            value = str(node.data.get("value", ""))

            # Prepare text for comparison based on case sensitivity
            if not case_sensitive:
                path = path.lower()
                value = value.lower()

            # Check if the search text is in either the path or value
            return search_text in path or search_text in value

        # Walk through all nodes and update visibility
        for node in self.walk_nodes():
            if node == tree.root:
                continue

            if match_node(node):
                # For matching nodes, expand all parent nodes
                parent = node.parent
                while parent and parent != tree.root:
                    parent.expand()
                    parent = parent.parent
                node.expand()
            else:
                # Collapse non-matching nodes
                node.collapse()

    def reset_tree(self) -> None:
        """Reset tree to its default state."""
        if not self.has_json:
            return

        tree = self.query_one("#json-tree", Tree)

        # Reset all nodes to default state (first level expanded)
        for node in self.walk_nodes():
            if node == tree.root:
                node.expand()
            elif node.parent == tree.root:
                node.expand()
            else:
                node.collapse()


# Run the application
if __name__ == "__main__":
    app = JsonViewerApp()
    app.run()
