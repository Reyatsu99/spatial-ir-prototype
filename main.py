"""
CLI Demo for Spatial IR Parser & Validator.
Takes natural language descriptions of 3–5 spaces, converts to structured JSON Spatial IR, and runs spatial validation.
"""

import json
from parser import SpatialNLParser
from validator import SpatialValidator
from spatial_ir import SpatialIR, Space, SpatialRelation, RelationType

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
    print("\nGenerated Spatial IR (JSON):")
    print(spatial_ir_1.to_json(indent=2))

    res_1 = validator.validate(spatial_ir_1)
    print("\nValidation Result:")
    print(json.dumps(res_1.to_dict(), indent=2))

    # Scenario 2: Invalid Floorplan with Spatial Contradictions (Existence + Direct Near/Far Conflict + Self Adjacency)
    print_section("SCENARIO 2: Floorplan with Spatial Contradictions & Missing Rooms")
    
    # Construct invalid Spatial IR to showcase validator edge cases
    spatial_ir_2 = parser.parse(
        "The living room is adjacent to the kitchen. "
        "The kitchen is far from the living room. "
        "The master bedroom is near the dining room."
    )
    
    # Introduce an explicit bad relation with a non-existent space and self-adjacency
    spatial_ir_2.add_relation(SpatialRelation(source="kitchen", target="garage", relation_type=RelationType.ADJACENT))
    spatial_ir_2.add_relation(SpatialRelation(source="living_room", target="living_room", relation_type=RelationType.ADJACENT))

    print("\nGenerated Spatial IR (JSON):")
    print(spatial_ir_2.to_json(indent=2))

    res_2 = validator.validate(spatial_ir_2)
    print("\nValidation Result:")
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
    print("\nGenerated Spatial IR (JSON):")
    print(spatial_ir_3.to_json(indent=2))

    res_3 = validator.validate(spatial_ir_3)
    print("\nValidation Result:")
    print(json.dumps(res_3.to_dict(), indent=2))

if __name__ == "__main__":
    run_demo()
