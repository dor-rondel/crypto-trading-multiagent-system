"""
Script to generate a PNG visualization of the LangGraph workflow.
"""

import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.workflows.graph import trading_app


def main():
    """
    Generates and saves the graph visualization.
    """
    output_path = "graph.png"
    print(f"Generating graph visualization to {output_path}...")

    try:
        # Get the graph and generate PNG bytes using mermaid.ink API
        png_bytes = trading_app.get_graph().draw_mermaid_png()

        with open(output_path, "wb") as f:
            f.write(png_bytes)

        print(f"✅ Graph successfully saved to {os.path.abspath(output_path)}")
    except Exception as e:
        print(f"❌ Failed to generate graph: {e}")
        print("Note: This requires an internet connection to use the Mermaid.ink API.")


if __name__ == "__main__":
    main()
