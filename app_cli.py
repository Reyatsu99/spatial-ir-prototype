"""
Interactive CLI REPL for Spatial IR Parser & Validator.
Run once (`python3 app_cli.py`) to continuously parse and validate room descriptions interactively.
"""

import json
from parser import SpatialNLParser
from validator import SpatialValidator
from visualizer import visualize

def run_repl():
    parser = SpatialNLParser()
    validator = SpatialValidator()

    print("=" * 70)
    print(" 🏗️ Spatial IR Interactive Terminal Workbench")
    print(" Type or paste room descriptions. Type 'exit' or 'q' to quit.")
    print("=" * 70)

    count = 1
    while True:
        try:
            print(f"\n[Prompt #{count}] Enter spatial description (or 'preset1', 'preset2', 'exit'):")
            user_input = input("> ").strip()
            
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Exiting Spatial IR Workbench. Goodbye!")
                break

            if user_input.lower() == "preset1":
                user_input = "The apartment has a living room, a kitchen, a master bedroom, and a bathroom. The living room is adjacent to the kitchen. The master bedroom is next to the bathroom. The kitchen is near the master bedroom. The bathroom is far from the living room."
            elif user_input.lower() == "preset2":
                user_input = "The house contains a foyer, living room, dining room, kitchen, and patio. The foyer is adjacent to the living room. The living room is connected to the dining room. The dining room is next to the kitchen. The kitchen is adjacent to the patio. The patio is far from the foyer."

            print(f"\nParsing: '{user_input}'")

            # 1. Parse
            spatial_ir = parser.parse(user_input)
            print("\n--- Spatial IR (JSON) ---")
            print(spatial_ir.to_json(indent=2))

            # 2. Validate
            result = validator.validate(spatial_ir)
            print("\n--- Validation Result ---")
            print(json.dumps(result.to_dict(), indent=2))

            # 3. Visualize if valid
            if result.is_valid:
                img_name = f"user_graph_{count}.png"
                visualize(spatial_ir, output_path=img_name, title=f"User Description #{count}")
                print(f"\n✓ Saved room adjacency graph PNG: {img_name}")

            count += 1

        except KeyboardInterrupt:
            print("\nExiting. Goodbye!")
            break
        except Exception as e:
            print(f"Error processing input: {e}")

if __name__ == "__main__":
    run_repl()
