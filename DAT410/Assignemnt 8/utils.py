import io
from PIL import Image
from pathlib import Path
from langchain_core.runnables.graph import MermaidDrawMethod

def save_graph(graph, full_file_path):
    """
    Save the graph as a png image
    """
    img_bytes = graph.draw_mermaid_png(draw_method=MermaidDrawMethod.API) # must use API method for saving, otherwise timeout error 
    image = Image.open(io.BytesIO(img_bytes))
    Path(full_file_path).parent.mkdir(parents=True, exist_ok=True)
    image.save(full_file_path)