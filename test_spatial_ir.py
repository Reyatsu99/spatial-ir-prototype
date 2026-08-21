"""
Unit tests for Spatial IR parser, validator, and JSON data models.
"""

import unittest
from spatial_ir import SpatialIR, Space, SpatialRelation, RelationType
from parser import SpatialNLParser
from validator import SpatialValidator

class TestSpatialIR(unittest.TestCase):

    def setUp(self):
        self.parser = SpatialNLParser()
        self.validator = SpatialValidator()

    def test_spatial_ir_json_serialization(self):
        ir = SpatialIR()
        ir.add_space(Space(id="living_room", name="Living Room"))
        ir.add_space(Space(id="kitchen", name="Kitchen"))
        ir.add_relation(SpatialRelation(source="living_room", target="kitchen", relation_type=RelationType.ADJACENT))

        json_str = ir.to_json()
        restored = SpatialIR.from_json(json_str)

        self.assertEqual(len(restored.spaces), 2)
        self.assertEqual(len(restored.relations), 1)
        self.assertEqual(restored.spaces[0].id, "living_room")
        self.assertEqual(restored.relations[0].relation_type, RelationType.ADJACENT)

    def test_parser_extracts_spaces_and_relations(self):
        text = (
            "The house has a living room, a kitchen, a master bedroom, and a bathroom. "
            "The living room is adjacent to the kitchen. "
            "The master bedroom is far from the kitchen."
        )
        ir = self.parser.parse(text)
        space_ids = {s.id for s in ir.spaces}

        self.assertIn("living_room", space_ids)
        self.assertIn("kitchen", space_ids)
        self.assertIn("master_bedroom", space_ids)
        self.assertIn("bathroom", space_ids)

        self.assertGreaterEqual(len(ir.relations), 2)

    def test_validator_room_existence_pass(self):
        ir = SpatialIR()
        ir.add_space(Space(id="living_room", name="Living Room"))
        ir.add_space(Space(id="kitchen", name="Kitchen"))
        ir.add_relation(SpatialRelation(source="living_room", target="kitchen", relation_type=RelationType.ADJACENT))

        res = self.validator.validate(ir)
        self.assertTrue(res.is_valid)
        self.assertEqual(len(res.errors), 0)

    def test_validator_room_existence_fail(self):
        ir = SpatialIR()
        ir.add_space(Space(id="living_room", name="Living Room"))
        # kitchen missing!
        ir.add_relation(SpatialRelation(source="living_room", target="kitchen", relation_type=RelationType.ADJACENT))

        res = self.validator.validate(ir)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("does not exist" in err for err in res.errors))

    def test_validator_self_adjacency_fail(self):
        ir = SpatialIR()
        ir.add_space(Space(id="living_room", name="Living Room"))
        ir.add_relation(SpatialRelation(source="living_room", target="living_room", relation_type=RelationType.ADJACENT))

        res = self.validator.validate(ir)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("cannot be adjacent to itself" in err for err in res.errors))

    def test_validator_near_far_direct_contradiction(self):
        ir = SpatialIR()
        ir.add_space(Space(id="living_room", name="Living Room"))
        ir.add_space(Space(id="kitchen", name="Kitchen"))
        ir.add_relation(SpatialRelation(source="living_room", target="kitchen", relation_type=RelationType.ADJACENT))
        ir.add_relation(SpatialRelation(source="living_room", target="kitchen", relation_type=RelationType.FAR))

        res = self.validator.validate(ir)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("Direct Contradiction Error" in err or "ADJACENT" in err for err in res.errors))

    def test_validator_adjacent_and_far_path_conflict(self):
        ir = SpatialIR()
        ir.add_space(Space(id="room_a", name="Room A"))
        ir.add_space(Space(id="room_b", name="Room B"))
        ir.add_relation(SpatialRelation(source="room_a", target="room_b", relation_type=RelationType.ADJACENT))
        ir.add_relation(SpatialRelation(source="room_a", target="room_b", relation_type=RelationType.FAR))

        res = self.validator.validate(ir)
        self.assertFalse(res.is_valid)
        self.assertGreater(len(res.errors), 0)

if __name__ == "__main__":
    unittest.main()
