# KasK - Kubernetes Assistant Terminal App

KasK is an open-source terminal-based application designed to simplify your interaction with Kubernetes clusters. With KasK, you can ask natural language questions about your Kubernetes resources, and it will generate accurate `kubectl` commands to fetch the required details. The app also provides a JSON viewer to display and explore the command output in a structured and user-friendly way.

## Features

- **Natural Language Queries**: Ask questions like "Show all running pods" or "List services in all namespaces," and KasK will generate the appropriate `kubectl` command.
- **JSON Viewer**: View the output of `kubectl` commands in a tree-like structure with search and filtering capabilities.
- **Clipboard Integration**: Copy selected JSON values to your clipboard for easy sharing or further use.
- **Dark Mode Support**: Enhanced readability with dark mode styles.
- **Keyboard Shortcuts**: Navigate and interact with the app efficiently using intuitive key bindings.

![KasK in Action](kask.gif)

## Usage

```bash
git clone https://github.com/your-repo/kask.git
cd kask
pip install -r requirements.txt
python main.py
```

Write your query in the "Write your prompt here" text area. For example: Show all pods in the default namespace

Click the "Prompt" button or press Enter to generate the kubectl command and view the output.

Use the JSON viewer to explore the output:

Search for specific keys or values.

Expand or collapse nodes.

Copy selected values to your clipboard.

Use keyboard shortcuts for quick actions:

- x: Expand/Collapse all nodes.
- s or /: Focus on the search bar.
- c: Copy the selected value.
- q: Quit the application.

## Requirements

Python 3.8 or higher
Ollama server with the niradler/k8s-operator:latest model
kubectl installed and configured to access your Kubernetes cluster.

## TODO:

- limit commands (read only) or
- review before run.
- compact table view
- tools integration
- chat memory
- model selector
- ollama configuration
- UI/UX
- submit prompt with keyboard
  