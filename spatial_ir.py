"""
Spatial Intermediate Representation (Spatial IR) data models.
"""

from dataclasses import dataclass, field
from enum import Enum
import json
from typing import List, Dict, Any, Optional

class RelationType(str, Enum):
    ADJACENT = "ADJACENT"
    NEAR = "NEAR"
    FAR = "FAR"
    CONTAINS = "CONTAINS"

@dataclass
class Space:
    id: str
    name: str
    space_type: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "space_type": self.space_type or self.name.lower().replace(" ", "_"),
            "attributes": self.attributes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Space":
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            space_type=data.get("space_type"),
            attributes=data.get("attributes", {}),
        )

@dataclass
class SpatialRelation:
    source: str
    target: str
    relation_type: RelationType

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "relation_type": self.relation_type.value if isinstance(self.relation_type, RelationType) else str(self.relation_type),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpatialRelation":
        rel_str = data["relation_type"].upper()
        try:
            rel_type = RelationType(rel_str)
        except ValueError:
            rel_type = rel_str
        return cls(
            source=data["source"],
            target=data["target"],
            relation_type=rel_type,
        )

@dataclass
class SpatialIR:
    spaces: List[Space] = field(default_factory=list)
    relations: List[SpatialRelation] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_space(self, space: Space) -> None:
        if not any(s.id == space.id for s in self.spaces):
            self.spaces.append(space)

    def add_relation(self, relation: SpatialRelation) -> None:
        self.relations.append(relation)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "spaces": [s.to_dict() for s in self.spaces],
            "relations": [r.to_dict() for r in self.relations],
            "metadata": self.metadata,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpatialIR":
        spaces = [Space.from_dict(s) for s in data.get("spaces", [])]
        relations = [SpatialRelation.from_dict(r) for r in data.get("relations", [])]
        metadata = data.get("metadata", {})
        return cls(spaces=spaces, relations=relations, metadata=metadata)

    @classmethod
    def from_json(cls, json_str: str) -> "SpatialIR":
        return cls.from_dict(json.loads(json_str))
