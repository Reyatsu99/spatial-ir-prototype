"""
Step 2: Spatial IR → Bubble Diagram Layout

Converts a validated SpatialIR into a structured bubble diagram —
the input format expected by HouseDiffusion and similar graph-constrained
floorplan generators.

Output JSON schema (bubble_diagram.json):
{
  "rooms": [
    {
      "id":        "living_room",
      "name":      "Living Room",
      "room_type": "living_room",
      "type_idx":  0,            # index into ROOM_TYPES list (for one-hot)
      "area_hint": 25.0,         # suggested area in m²
      "pos":       [x, y],       # normalised bubble position [0,1]
      "bbox":      [x0, y0, x1, y1]  # normalised bounding box estimate
    }
  ],
  "edges": [
    {
      "source":   "living_room",
      "target":   "kitchen",
      "relation": "ADJACENT"     # only ADJACENT edges are door connections
    }
  ],
  "adjacency_matrix": [[...]]    # NxN binary matrix (door connections only)
}
"""

import json
import math
from typing import Dict, List, Tuple, Optional

from spatial_ir import SpatialIR, RelationType

try:
    import networkx as nx
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    VIZ_AVAILABLE = True
except ImportError:
    VIZ_AVAILABLE = False

# ── Room type registry (matches HouseDiffusion's 25 room-type vocabulary) ─────
ROOM_TYPES = [
    "living_room", "master_bedroom", "kitchen", "bathroom", "dining_room",
    "child_bedroom", "study",  "second_bedroom", "guest_room", "balcony",
    "entrance", "storage",   "wall",            "exterior_wall", "front_door",
    "interior_door", "staircase", "garage", "laundry_room", "patio",
    "foyer", "hallway", "closet", "gym", "office",
]
ROOM_TYPE_INDEX: Dict[str, int] = {rt: i for i, rt in enumerate(ROOM_TYPES)}

# Suggested area hints per room type (m²)
AREA_HINTS: Dict[str, float] = {
    "living_room":    25.0,
    "master_bedroom": 20.0,
    "kitchen":        12.0,
    "bathroom":        6.0,
    "dining_room":    14.0,
    "child_bedroom":  12.0,
    "study":          10.0,
    "second_bedroom": 14.0,
    "guest_room":     14.0,
    "balcony":         6.0,
    "entrance":        4.0,
    "storage":         4.0,
    "garage":         20.0,
    "laundry_room":    5.0,
    "patio":          10.0,
    "foyer":           8.0,
    "hallway":         6.0,
}
DEFAULT_AREA = 10.0

# Node colour for bubble diagram rendering
ROOM_COLORS = {
    "living_room":    "#64B5F6",
    "kitchen":        "#FFB74D",
    "master_bedroom": "#CE93D8",
    "bathroom":       "#80DEEA",
    "dining_room":    "#FFCC80",
    "foyer":          "#EF9A9A",
    "patio":          "#C5E1A5",
    "hallway":        "#B0BEC5",
    "study":          "#F48FB1",
    "garage":         "#BCAAA4",
    "laundry_room":   "#FFE082",
}
DEFAULT_COLOR = "#E0E0E0"


def _spring_positions(ir: SpatialIR) -> Dict[str, Tuple[float, float]]:
    """
    Use networkx spring layout on the ADJACENT sub-graph to get 2D room positions.
    Non-adjacent rooms are placed using the full relation graph.
    Returns positions normalised to [0.1, 0.9].
    """
    G = nx.Graph()
    for s in ir.spaces:
        G.add_node(s.id)
    for r in ir.relations:
        if r.relation_type == RelationType.ADJACENT:
            G.add_edge(r.source, r.target, weight=3.0)
        elif r.relation_type == RelationType.NEAR:
            G.add_edge(r.source, r.target, weight=1.5)
        elif r.relation_type == RelationType.FAR:
            G.add_edge(r.source, r.target, weight=0.3)

    raw = nx.spring_layout(G, seed=42, k=1.8, weight="weight")

    # Normalise to [0.1, 0.9]
    xs = [v[0] for v in raw.values()]
    ys = [v[1] for v in raw.values()]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    xrange = max(xmax - xmin, 1e-6)
    yrange = max(ymax - ymin, 1e-6)

    return {
        node: (
            0.1 + 0.8 * (v[0] - xmin) / xrange,
            0.1 + 0.8 * (v[1] - ymin) / yrange,
        )
        for node, v in raw.items()
    }


def _area_to_radius(area_m2: float, canvas: float = 1.0) -> float:
    """Convert area hint to a bubble radius on a normalised [0,1] canvas."""
    # Scale: assume total canvas ~100 m², so bubble radius proportional to sqrt(area)
    scale = canvas / math.sqrt(100.0)
    return scale * math.sqrt(area_m2) * 0.5


def ir_to_bubble_diagram(ir: SpatialIR) -> dict:
    """
    Convert SpatialIR → bubble diagram dict.
    """
    pos = _spring_positions(ir)
    space_ids = [s.id for s in ir.spaces]
    n = len(space_ids)
    idx_map = {sid: i for i, sid in enumerate(space_ids)}

    rooms = []
    for s in ir.spaces:
        x, y = pos.get(s.id, (0.5, 0.5))
        area = AREA_HINTS.get(s.space_type or s.id, DEFAULT_AREA)
        r = _area_to_radius(area)
        room = {
            "id":        s.id,
            "name":      s.name,
            "room_type": s.space_type or s.id,
            "type_idx":  ROOM_TYPE_INDEX.get(s.space_type or s.id, 0),
            "area_hint": area,
            "pos":       [round(x, 4), round(y, 4)],
            "bbox":      [
                round(max(0.0, x - r), 4),
                round(max(0.0, y - r), 4),
                round(min(1.0, x + r), 4),
                round(min(1.0, y + r), 4),
            ],
        }
        rooms.append(room)

    # Only ADJACENT edges become door connections (HouseDiffusion convention)
    edges = []
    adj_matrix = [[0] * n for _ in range(n)]
    seen = set()
    for rel in ir.relations:
        if rel.relation_type != RelationType.ADJACENT:
            continue
        if rel.source not in idx_map or rel.target not in idx_map:
            continue
        pair = tuple(sorted([rel.source, rel.target]))
        if pair in seen:
            continue
        seen.add(pair)
        edges.append({
            "source":   rel.source,
            "target":   rel.target,
            "relation": "ADJACENT",
        })
        i, j = idx_map[rel.source], idx_map[rel.target]
        adj_matrix[i][j] = 1
        adj_matrix[j][i] = 1

    return {
        "rooms":            rooms,
        "edges":            edges,
        "adjacency_matrix": adj_matrix,
        "metadata": {
            "total_rooms": n,
            "total_door_connections": len(edges),
        },
    }


def save_bubble_diagram(diagram: dict, path: str = "bubble_diagram.json") -> str:
    with open(path, "w") as f:
        json.dump(diagram, f, indent=2)
    return path


def visualize_bubble_diagram(
    diagram: dict,
    output_path: str = "bubble_diagram.png",
    title: str = "Bubble Diagram",
) -> str:
    """Render the bubble diagram as a styled PNG."""
    if not VIZ_AVAILABLE:
        raise ImportError("pip install matplotlib networkx")

    rooms  = {r["id"]: r for r in diagram["rooms"]}
    edges  = diagram["edges"]

    fig, ax = plt.subplots(figsize=(9, 9))
    fig.patch.set_facecolor("#12121E")
    ax.set_facecolor("#12121E")
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.set_aspect("equal")
    ax.axis("off")

    # Draw edges first
    for e in edges:
        r1 = rooms[e["source"]]
        r2 = rooms[e["target"]]
        x1, y1 = r1["pos"]
        x2, y2 = r2["pos"]
        ax.plot([x1, x2], [y1, y2], color="#4CAF50", lw=2.2, alpha=0.7, zorder=1)

    # Draw bubbles
    for rid, r in rooms.items():
        x, y = r["pos"]
        area  = r["area_hint"]
        radius = _area_to_radius(area) * 1.05   # slight visual padding

        color = ROOM_COLORS.get(r["room_type"], DEFAULT_COLOR)
        circle = plt.Circle((x, y), radius, color=color, alpha=0.88, zorder=2)
        ax.add_patch(circle)
        # Room name (split on underscore for readability)
        label = r["name"].replace(" ", "\n")
        ax.text(x, y, label, ha="center", va="center",
                fontsize=7.5, fontweight="bold", color="#1A1A2E", zorder=3,
                multialignment="center")

        # Area hint badge
        ax.text(x, y - radius - 0.025, f"{area}m²",
                ha="center", va="top", fontsize=6.5,
                color="#AAAACC", zorder=3)

    ax.set_title(title, color="white", fontsize=13, fontweight="bold", pad=12)
    ax.text(0.5, -0.04, "● Bubble size ∝ room area   ─── Door connection (ADJACENT)",
            ha="center", va="center", color="#8888AA", fontsize=7.5,
            transform=ax.transAxes)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    return output_path


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from parser import SpatialNLParser
    from validator import SpatialValidator

    scenarios = {
        "4_room_apartment": (
            "The apartment has a living room, a kitchen, a master bedroom, and a bathroom. "
            "The living room is adjacent to the kitchen. "
            "The master bedroom is next to the bathroom. "
            "The kitchen is near the master bedroom. "
            "The bathroom is far from the living room."
        ),
        "5_room_house": (
            "The house contains a foyer, living room, dining room, kitchen, and patio. "
            "The foyer is adjacent to the living room. "
            "The living room is connected to the dining room. "
            "The dining room is next to the kitchen. "
            "The kitchen is adjacent to the patio. "
            "The patio is far from the foyer."
        ),
    }

    parser    = SpatialNLParser()
    validator = SpatialValidator()

    for name, text in scenarios.items():
        ir     = parser.parse(text)
        result = validator.validate(ir)

        if not result.is_valid:
            print(f"[{name}] ✗ Validation failed — skipping layout generation")
            for err in result.errors:
                print(f"   {err}")
            continue

        diagram = ir_to_bubble_diagram(ir)
        json_path = save_bubble_diagram(diagram, f"{name}_bubble.json")
        img_path  = visualize_bubble_diagram(diagram, f"{name}_bubble.png",
                                             title=name.replace("_", " ").title())

        print(f"[{name}] ✓  {result.metrics['total_spaces']} rooms  "
              f"| {diagram['metadata']['total_door_connections']} door-connections")
        print(f"   JSON → {json_path}")
        print(f"   PNG  → {img_path}")
        print()
