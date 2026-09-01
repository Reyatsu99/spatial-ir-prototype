"""
CLI Demo for Minimal Spatial IR Prototype.
Converts natural language descriptions of spaces into structured JSON Spatial IR
and validates room existence, adjacency properties, and near/far logical constraints.
"""

import json
from parser import SpatialNLParser
from validator import SpatialValidator
from visualizer import visualize
from spatial_ir import SpatialIR, SpatialRelation, RelationType

def print_section(title: str):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)

def run_demo():
    parser = SpatialNLParser()
    validator = SpatialValidator()

    # Scenario 1: Valid 4-Space Floorplan Description
    nl_desc_1 = (
        "The apartment has a living room, a kitchen, a master bedroom, and a bathroom. "
        "The living room is adjacent to the kitchen. "
        "The master bedroom is next to the bathroom. "
        "The kitchen is near the master bedroom. "
        "The bathroom is far from the living room."
    )

    print_section("SCENARIO 1: Valid 4-Space Floorplan Description")
    print("Input Text:\n", nl_desc_1.strip())
    
    spatial_ir_1 = parser.parse(nl_desc_1)
    print("\n[1] Generated Spatial IR (JSON):")
    print(spatial_ir_1.to_json(indent=2))

    res_1 = validator.validate(spatial_ir_1)
    print("\n[2] Spatial Validation Result:")
    print(json.dumps(res_1.to_dict(), indent=2))

    if res_1.is_valid:
        g_path = visualize(spatial_ir_1, output_path="4_room_apartment_graph.png", title="4-Room Apartment Adjacency Graph")
        print("\n[3] Generated Visual Artifact:")
        print(f"   ✓ Room Adjacency Graph PNG -> {g_path}")

    # Scenario 2: Invalid Floorplan with Spatial Contradictions
    print_section("SCENARIO 2: Floorplan with Spatial Contradictions & Missing Rooms")
    
    spatial_ir_2 = parser.parse(
        "The living room is adjacent to the kitchen. "
        "The kitchen is far from the living room. "
        "The master bedroom is near the dining room."
    )
    spatial_ir_2.add_relation(SpatialRelation(source="kitchen", target="garage", relation_type=RelationType.ADJACENT))
    spatial_ir_2.add_relation(SpatialRelation(source="living_room", target="living_room", relation_type=RelationType.ADJACENT))

    print("Input Text:\n", "The living room is adjacent to the kitchen. The kitchen is far from the living room...")
    print("\n[1] Generated Spatial IR (JSON):")
    print(spatial_ir_2.to_json(indent=2))

    res_2 = validator.validate(spatial_ir_2)
    print("\n[2] Spatial Validation Result:")
    print(json.dumps(res_2.to_dict(), indent=2))

    # Scenario 3: Valid 5-Space House Description
    nl_desc_3 = (
        "The house contains a foyer, living room, dining room, kitchen, and patio. "
        "The foyer is adjacent to the living room. "
        "The living room is connected to the dining room. "
        "The dining room is next to the kitchen. "
        "The kitchen is adjacent to the patio. "
        "The patio is far from the foyer."
    )

    print_section("SCENARIO 3: Valid 5-Space House Description")
    print("Input Text:\n", nl_desc_3.strip())

    spatial_ir_3 = parser.parse(nl_desc_3)
    print("\n[1] Generated Spatial IR (JSON):")
    print(spatial_ir_3.to_json(indent=2))

    res_3 = validator.validate(spatial_ir_3)
    print("\n[2] Spatial Validation Result:")
    print(json.dumps(res_3.to_dict(), indent=2))

    if res_3.is_valid:
        g_path3 = visualize(spatial_ir_3, output_path="5_room_house_graph.png", title="5-Room House Adjacency Graph")
        print("\n[3] Generated Visual Artifact:")
        print(f"   ✓ Room Adjacency Graph PNG -> {g_path3}")

if __name__ == "__main__":
    run_demo()
