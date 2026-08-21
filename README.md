# Spatial IR & Validation Prototype

A Python prototype that parses natural-language architectural space descriptions into a structured JSON **Spatial Intermediate Representation (Spatial IR)** and validates spatial constraints including room existence, adjacency graphs, and near/far logical relationships.

---

## Features

- **Natural Language Parsing**: Extracts 3–5 room entities and spatial relations (`ADJACENT`, `NEAR`, `FAR`, `CONTAINS`) without requiring external API keys.
- **Structured JSON Spatial IR**: Represents architectural layouts as spaces (nodes) and spatial relations (edges).
- **Spatial Validation Engine**:
  - **Room Existence**: Validates that all relationship endpoints refer to defined spaces.
  - **Adjacency & Graph Rules**: Validates self-adjacency violations, duplicate relations, and connectivity graphs.
  - **Near/Far Consistency**: Identifies direct contradictions (spaces declared as both `NEAR`/`ADJACENT` and `FAR`) and graph-distance conflicts (directly adjacent 1-hop spaces marked as `FAR`).

---

## File Structure

```
spatial-ir-prototype/
├── spatial_ir.py       # Core data models for Space, SpatialRelation, and SpatialIR
├── parser.py           # Natural-language text parser into Spatial IR
├── validator.py        # Spatial validation engine for existence, adjacency & near/far logic
├── main.py             # CLI demonstration runner with 3 realistic scenarios
└── test_spatial_ir.py  # Automated unit test suite (7 tests)
```

---

## Quick Start

### 1. Run CLI Demo
```bash
python3 main.py
```

### 2. Run Unit Tests
```bash
python3 -m unittest test_spatial_ir.py
```

---

## Example JSON Spatial IR Output

```json
{
  "spaces": [
    {
      "id": "master_bedroom",
      "name": "Master Bedroom",
      "space_type": "master_bedroom",
      "attributes": {}
    },
    {
      "id": "living_room",
      "name": "Living Room",
      "space_type": "living_room",
      "attributes": {}
    },
    {
      "id": "kitchen",
      "name": "Kitchen",
      "space_type": "kitchen",
      "attributes": {}
    },
    {
      "id": "bathroom",
      "name": "Bathroom",
      "space_type": "bathroom",
      "attributes": {}
    }
  ],
  "relations": [
    {
      "source": "living_room",
      "target": "kitchen",
      "relation_type": "ADJACENT"
    },
    {
      "source": "master_bedroom",
      "target": "bathroom",
      "relation_type": "ADJACENT"
    },
    {
      "source": "master_bedroom",
      "target": "kitchen",
      "relation_type": "NEAR"
    },
    {
      "source": "living_room",
      "target": "bathroom",
      "relation_type": "FAR"
    }
  ]
}
```
