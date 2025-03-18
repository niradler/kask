from ollama import chat
from ollama import ChatResponse

def check_installation() -> None:
    """Check if Ollama is installed and the required model is available."""
    try:
        # Try importing ollama to verify installation
        import ollama
    except ImportError:
        raise RuntimeError("Ollama Python package is not installed. Please install it with: pip install ollama")

    try:
        # Check if Ollama server is running by attempting to list models
        ollama.list()
    except Exception:
        raise RuntimeError("Ollama server is not running. Please install and start the Ollama server: https://ollama.ai/download")

    try:
        # Pull the model to ensure it's available
        models = ollama.list()
        models = models.get('models')
        if not models:
            raise RuntimeError("Model 'niradler/k8s-operator:latest' is not available.")
        for model in models:
            if model.get('model') == 'niradler/k8s-operator:latest':
                return
        raise RuntimeError("Model 'niradler/k8s-operator:latest' is not available.")
        # ollama.create()
    except Exception as e:
        raise RuntimeError(f"Failed to pull required model: {str(e)}")

# Verify installation and model availability on module import
check_installation()

def query(user_query: str) -> str:
    """Call Ollama API to generate a kubectl command."""
    try:
        response: ChatResponse = chat(model='niradler/k8s-operator:latest', messages=[
            {
                'role': 'assistant',
                'content': """You are an AI assistant specializing in Kubernetes (k8s).
                Your goal is to help users interact with Kubernetes clusters by providing accurate, 
                well-structured, and practical kubectl commands. 
                Guide:
                - output command only as we going to run it and show the results to the user.
                - dont output explanation or any text other then the kubectl command to run
                - command output should always be json
                - if the request is on all resources use --all-namespaces, dont add --all-namespaces on create/update/delete commands.
                
                Example:
                - show running pods => kubectl get pods -o json
                - show all pods => kubectl get pods --all-namespaces -o json
                """,
            },
            {
                'role': 'user',
                'content': user_query,
            },
        ])

        return response.message.content
    except Exception as e:
        return f"Model error: {str(e)}"

# print(query_prod("show running pods"))
# print(ollama.list())