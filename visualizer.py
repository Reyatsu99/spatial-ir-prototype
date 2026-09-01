"""
Spatial IR Graph Visualizer.
Renders the room adjacency graph from a SpatialIR object using networkx + matplotlib.

Node  = Room (space)
Edge  = Spatial relation, color-coded:
  GREEN  = ADJACENT
  ORANGE = NEAR
  RED    = FAR
"""

import json
import sys
from typing import Optional
from spatial_ir import SpatialIR, RelationType

try:
    import networkx as nx
    import matplotlib
    matplotlib.use("Agg")           # headless / file output
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    VIZ_AVAILABLE = True
except ImportError:
    VIZ_AVAILABLE = False

# ── colour palette ─────────────────────────────────────────────────────────────
RELATION_COLORS = {
    RelationType.ADJACENT: "#4CAF50",   # green
    RelationType.NEAR:     "#FF9800",   # orange
    RelationType.FAR:      "#F44336",   # red
    RelationType.CONTAINS: "#9C27B0",   # purple
}

ROOM_TYPE_COLORS = {
    "living_room":    "#64B5F6",
    "kitchen":        "#FFB74D",
    "master_bedroom": "#CE93D8",
    "bedroom":        "#A5D6A7",
    "bathroom":       "#80DEEA",
    "dining_room":    "#FFCC80",
    "foyer":          "#EF9A9A",
    "hallway":        "#B0BEC5",
    "study":          "#F48FB1",
    "garage":         "#BCAAA4",
    "patio":          "#C5E1A5",
    "balcony":        "#80CBC4",
    "laundry_room":   "#FFE082",
}
DEFAULT_NODE_COLOR = "#E0E0E0"


def build_graph(ir: SpatialIR) -> "nx.MultiDiGraph":
    G = nx.MultiDiGraph()
    for space in ir.spaces:
        G.add_node(
            space.id,
            label=space.name,
            color=ROOM_TYPE_COLORS.get(space.space_type or space.id, DEFAULT_NODE_COLOR),
        )
    for rel in ir.relations:
        rtype = rel.relation_type
        color = RELATION_COLORS.get(rtype, "#999999")
        G.add_edge(rel.source, rel.target, relation=rtype, color=color)
    return G


def visualize(ir: SpatialIR, output_path: str = "spatial_graph.png", title: str = "Spatial IR Graph") -> str:
    """
    Render the SpatialIR as a coloured room-adjacency graph and save to output_path.
    Returns the saved file path.
    """
    if not VIZ_AVAILABLE:
        raise ImportError("Install matplotlib and networkx: pip install matplotlib networkx")

    G = build_graph(ir)

    fig, ax = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor("#1E1E2E")
    ax.set_facecolor("#1E1E2E")

    # layout
    pos = nx.spring_layout(G, seed=42, k=2.5)

    # nodes
    node_colors = [G.nodes[n].get("color", DEFAULT_NODE_COLOR) for n in G.nodes()]
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors,
                           node_size=2200, alpha=0.95)

    # node labels
    labels = {n: G.nodes[n].get("label", n) for n in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels=labels, ax=ax,
                            font_size=9, font_color="#1E1E2E", font_weight="bold")

    # edges – draw each relation type separately for colour
    for rtype, ecolor in RELATION_COLORS.items():
        edges = [(u, v) for u, v, d in G.edges(data=True)
                 if d.get("relation") == rtype]
        if edges:
            style = "solid" if rtype == RelationType.ADJACENT else "dashed"
            nx.draw_networkx_edges(
                G, pos, edgelist=edges, ax=ax,
                edge_color=ecolor, width=2.5,
                style=style,
                arrows=True,
                arrowsize=20,
                connectionstyle="arc3,rad=0.1",
                min_source_margin=30,
                min_target_margin=30,
            )

    # legend
    legend_patches = [
        mpatches.Patch(color=RELATION_COLORS[RelationType.ADJACENT], label="ADJACENT"),
        mpatches.Patch(color=RELATION_COLORS[RelationType.NEAR],     label="NEAR"),
        mpatches.Patch(color=RELATION_COLORS[RelationType.FAR],      label="FAR"),
    ]
    ax.legend(handles=legend_patches, loc="lower right",
              facecolor="#2D2D3F", labelcolor="white", fontsize=9,
              framealpha=0.9, edgecolor="#555")

    ax.set_title(title, color="white", fontsize=13, fontweight="bold", pad=14)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return output_path


# ── CLI usage ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from parser import SpatialNLParser

    descriptions = {
        "4-room apartment": (
            "The apartment has a living room, a kitchen, a master bedroom, and a bathroom. "
            "The living room is adjacent to the kitchen. "
            "The master bedroom is next to the bathroom. "
            "The kitchen is near the master bedroom. "
            "The bathroom is far from the living room."
        ),
        "5-room house": (
            "The house contains a foyer, living room, dining room, kitchen, and patio. "
            "The foyer is adjacent to the living room. "
            "The living room is connected to the dining room. "
            "The dining room is next to the kitchen. "
            "The kitchen is adjacent to the patio. "
            "The patio is far from the foyer."
        ),
    }

    p = SpatialNLParser()
    for name, text in descriptions.items():
        ir = p.parse(text)
        fname = name.replace(" ", "_").replace("-", "_") + "_graph.png"
        saved = visualize(ir, output_path=fname, title=name.title())
        print(f"✓ Saved: {saved}  ({len(ir.spaces)} spaces, {len(ir.relations)} relations)")
