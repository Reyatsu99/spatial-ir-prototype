"""
Parser to convert natural language descriptions of architectural spaces into Spatial IR.
"""

import re
from typing import List, Dict, Tuple, Optional, Set
from spatial_ir import SpatialIR, Space, SpatialRelation, RelationType

# Common room keywords and canonical spatial relations
KNOWN_ROOM_TYPES = [
    "master bedroom", "living room", "dining room", "laundry room", 
    "bedroom", "kitchen", "bathroom", "balcony", "foyer", "hallway", 
    "study", "garage", "patio"
]

RELATION_PATTERNS = [
    # (Regex pattern, RelationType)
    (r"\b(adjacent to|next to|beside|shares a wall with|connected to|adjoins)\b", RelationType.ADJACENT),
    (r"\b(far from|far away from|distant from|far off from)\b", RelationType.FAR),
    (r"\b(near|close to|in proximity to|nearby)\b", RelationType.NEAR),
    (r"\b(contains|inside|includes)\b", RelationType.CONTAINS),
]

class SpatialNLParser:
    def __init__(self):
        pass

    def _normalize_id(self, raw_name: str) -> str:
        clean = raw_name.lower().strip()
        clean = re.sub(r"^(the|a|an)\s+", "", clean)
        return clean.replace(" ", "_")

    def _format_name(self, space_id: str) -> str:
        return space_id.replace("_", " ").title()

    def extract_spaces_from_text(self, text: str) -> List[Space]:
        """Extract space entities from natural language text without duplicate substring matching."""
        text_lower = text.lower()
        found_spaces: Dict[str, Space] = {}

        # Track matched spans in text to prevent matching sub-phrases like 'bedroom' inside 'master bedroom'
        matched_spans: List[Tuple[int, int]] = []

        for room_type in KNOWN_ROOM_TYPES:
            for match in re.finditer(rf"\b{re.escape(room_type)}\b", text_lower):
                start, end = match.span()
                # Check if this span overlaps with an already matched longer span
                if any(m_start <= start and end <= m_end for m_start, m_end in matched_spans):
                    continue

                matched_spans.append((start, end))
                sp_id = self._normalize_id(room_type)
                if sp_id not in found_spaces:
                    found_spaces[sp_id] = Space(
                        id=sp_id,
                        name=self._format_name(sp_id),
                        space_type=sp_id
                    )

        return list(found_spaces.values())

    def parse(self, text: str) -> SpatialIR:
        """
        Parse a natural language text describing 3-5 spaces and their relations into a SpatialIR object.
        """
        spatial_ir = SpatialIR()
        spatial_ir.metadata["raw_description"] = text

        spaces = self.extract_spaces_from_text(text)
        for s in spaces:
            spatial_ir.add_space(s)

        # Split sentences/clauses on punctuation or explicit conjunctions
        clauses = re.split(r"[.;\n]|(?:\band\b)", text)

        for clause in clauses:
            clause = clause.strip()
            if not clause:
                continue

            # Determine relation type in this clause
            detected_rel: Optional[RelationType] = None
            for pattern, rtype in RELATION_PATTERNS:
                if re.search(pattern, clause, re.IGNORECASE):
                    detected_rel = rtype
                    break

            if not detected_rel or detected_rel == RelationType.CONTAINS:
                # 'contains' in room listings e.g., 'The house contains a foyer, living room...' is listing, not pairwise relation
                continue

            clause_lower = clause.lower()
            present_spaces: List[str] = []

            # Match spaces sorted by length descending so longer room names match first
            sorted_spaces = sorted(spatial_ir.spaces, key=lambda s: len(s.name), reverse=True)
            matched_clause_spans: List[Tuple[int, int]] = []

            for space in sorted_spaces:
                patterns = [rf"\b{re.escape(space.id.replace('_', ' '))}\b", rf"\b{re.escape(space.name.lower())}\b"]
                for p in patterns:
                    for match in re.finditer(p, clause_lower):
                        start, end = match.span()
                        if not any(m_start <= start and end <= m_end for m_start, m_end in matched_clause_spans):
                            matched_clause_spans.append((start, end))
                            if space.id not in present_spaces:
                                present_spaces.append(space.id)

            # Pair adjacent matched spaces in clause
            if len(present_spaces) >= 2:
                source_id = present_spaces[0]
                target_id = present_spaces[1]
                spatial_ir.add_relation(SpatialRelation(
                    source=source_id,
                    target=target_id,
                    relation_type=detected_rel
                ))

        return spatial_ir
