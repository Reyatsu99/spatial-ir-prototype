"""
Validator for Spatial IR checking room existence, adjacency consistency, and near/far logical relationships.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Any, Tuple
from collections import deque
from spatial_ir import SpatialIR, RelationType

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "metrics": self.metrics,
        }

class SpatialValidator:
    def __init__(self):
        pass

    def validate(self, ir: SpatialIR) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        space_ids = {s.id for s in ir.spaces}

        # 1. Validate Room Existence
        existence_errors = self._validate_existence(ir, space_ids)
        errors.extend(existence_errors)

        # 2. Validate Adjacency Relations
        adj_errors, adj_warnings, adj_graph = self._validate_adjacency(ir, space_ids)
        errors.extend(adj_errors)
        warnings.extend(adj_warnings)

        # 3. Validate Near/Far Relationships & Contradictions
        near_far_errors, near_far_warnings = self._validate_near_far(ir, space_ids, adj_graph)
        errors.extend(near_far_errors)
        warnings.extend(near_far_warnings)

        is_valid = len(errors) == 0

        metrics = {
            "total_spaces": len(ir.spaces),
            "total_relations": len(ir.relations),
            "adjacency_edges": sum(len(neighbors) for neighbors in adj_graph.values()) // 2,
            "error_count": len(errors),
            "warning_count": len(warnings)
        }

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            metrics=metrics
        )

    def _get_rel_str(self, rel_type: Any) -> str:
        if hasattr(rel_type, "value"):
            return str(rel_type.value).upper()
        return str(rel_type).upper()

    def _validate_existence(self, ir: SpatialIR, space_ids: Set[str]) -> List[str]:
        errors = []
        if len(ir.spaces) == 0:
            errors.append("Spatial IR contains 0 spaces.")
        
        for idx, rel in enumerate(ir.relations):
            rel_str = self._get_rel_str(rel.relation_type)
            if rel.source not in space_ids:
                errors.append(f"Relation #{idx+1} ({rel_str}): Source space '{rel.source}' does not exist.")
            if rel.target not in space_ids:
                errors.append(f"Relation #{idx+1} ({rel_str}): Target space '{rel.target}' does not exist.")
        
        return errors

    def _validate_adjacency(self, ir: SpatialIR, space_ids: Set[str]) -> Tuple[List[str], List[str], Dict[str, Set[str]]]:
        errors = []
        warnings = []
        adj_graph: Dict[str, Set[str]] = {sp: set() for sp in space_ids}

        seen_relations: Set[Tuple[str, str, str]] = set()

        for rel in ir.relations:
            if rel.source not in space_ids or rel.target not in space_ids:
                continue

            rel_str = self._get_rel_str(rel.relation_type)
            rel_tuple = (rel.source, rel.target, rel_str)
            rev_tuple = (rel.target, rel.source, rel_str)

            if rel_tuple in seen_relations or rev_tuple in seen_relations:
                warnings.append(f"Duplicate spatial relation: {rel.source} --[{rel_str}]--> {rel.target}")
            seen_relations.add(rel_tuple)

            if rel_str == RelationType.ADJACENT.value:
                if rel.source == rel.target:
                    errors.append(f"Adjacency Error: Space '{rel.source}' cannot be adjacent to itself.")
                else:
                    adj_graph[rel.source].add(rel.target)
                    adj_graph[rel.target].add(rel.source)

        return errors, warnings, adj_graph

    def _validate_near_far(
        self, ir: SpatialIR, space_ids: Set[str], adj_graph: Dict[str, Set[str]]
    ) -> Tuple[List[str], List[str]]:
        errors = []
        warnings = []

        # Maps pair (min(a,b), max(a,b)) to set of declared relations
        pair_relations: Dict[Tuple[str, str], Set[str]] = {}

        for rel in ir.relations:
            if rel.source not in space_ids or rel.target not in space_ids:
                continue
            pair = tuple(sorted([rel.source, rel.target]))
            if pair not in pair_relations:
                pair_relations[pair] = set()
            pair_relations[pair].add(self._get_rel_str(rel.relation_type))

        # Check direct contradictions
        for (u, v), rels in pair_relations.items():
            if u == v:
                if RelationType.FAR.value in rels:
                    errors.append(f"Near/Far Error: Space '{u}' cannot be FAR from itself.")
                continue

            has_adj_or_near = bool(rels & {RelationType.ADJACENT.value, RelationType.NEAR.value})
            has_far = RelationType.FAR.value in rels

            if has_adj_or_near and has_far:
                errors.append(
                    f"Direct Contradiction Error: Spaces '{u}' and '{v}' are declared as both NEAR/ADJACENT and FAR."
                )

        # Topological distance check based on Adjacency graph
        for (u, v), rels in pair_relations.items():
            if u == v or RelationType.FAR.value not in rels:
                continue

            # Compute shortest path hop count in adjacency graph
            dist = self._bfs_shortest_path(adj_graph, u, v)
            if dist is not None:
                if dist == 1:
                    errors.append(
                        f"Spatial Contradiction Error: Spaces '{u}' and '{v}' are directly ADJACENT (distance=1), but marked as FAR."
                    )
                elif dist > 1:
                    warnings.append(
                        f"Potential Conflict Warning: Spaces '{u}' and '{v}' are connected via {dist} hops of adjacency, but marked as FAR."
                    )

        return errors, warnings

    def _bfs_shortest_path(self, graph: Dict[str, Set[str]], start: str, end: str) -> Optional[int]:
        if start not in graph or end not in graph:
            return None
        if start == end:
            return 0

        visited = {start: 0}
        queue = deque([start])

        while queue:
            curr = queue.popleft()
            curr_dist = visited[curr]

            for neighbor in graph[curr]:
                if neighbor == end:
                    return curr_dist + 1
                if neighbor not in visited:
                    visited[neighbor] = curr_dist + 1
                    queue.append(neighbor)

        return None
