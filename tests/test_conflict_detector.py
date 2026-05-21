import pytest
from skill_seekers.cli.conflict_detector import ConflictDetector, Conflict


class TestConflictDetectorEdgeCases:
	"""Edge case tests for ConflictDetector when docs and code data diverge."""

	def test_detector_with_empty_docs_data(self):
		"""When docs_data is empty dict, detector should still initialize without error."""
		detector = ConflictDetector(docs_data={}, github_data={'apis': {}})
		assert detector is not None
		assert detector.docs_apis == {}
		assert detector.code_apis == {}

	def test_detector_with_empty_code_data(self):
		"""When github_data is empty dict, detector should still initialize without error."""
		detector = ConflictDetector(docs_data={'apis': {}}, github_data={})
		assert detector is not None
		assert detector.docs_apis == {}
		assert detector.code_apis == {}

	def test_detector_with_both_empty(self):
		"""When both data sources are empty, detector should still initialize."""
		detector = ConflictDetector(docs_data={}, github_data={})
		assert detector is not None
		conflicts = detector.detect_conflicts()
		assert conflicts == []

	def test_apis_with_non_dict_structure(self):
		"""When apis are not dicts (e.g., list), extraction should not crash."""
		detector = ConflictDetector(
			docs_data={'apis': [{'name': 'test'}]},  # wrong structure
			github_data={'apis': {'test_api': {}}}
		)
		assert detector.docs_apis == {}  # should gracefully skip non-dict entries

	def test_conflict_dataclass_all_fields_none(self):
		"""Conflict dataclass should be instantiable with all None optional fields."""
		conflict = Conflict(
			type='missing_in_code',
			severity='high',
			api_name='test_api'
		)
		assert conflict.type == 'missing_in_code'
		assert conflict.severity == 'high'
		assert conflict.api_name == 'test_api'
		assert conflict.docs_info is None
		assert conflict.code_info is None
		assert conflict.difference is None
		assert conflict.suggestion is None

	def test_conflict_asdict_with_all_fields(self):
		"""Conflict.asdict() should work when all optional fields are populated."""
		conflict = Conflict(
			type='signature_mismatch',
			severity='medium',
			api_name='my_api',
			docs_info={'params': ['a', 'b']},
			code_info={'params': ['a', 'b', 'c']},
			difference='code has extra param c',
			suggestion='add param c to docs'
		)
		d = conflict.__dict__
		assert d['type'] == 'signature_mismatch'
		assert d['severity'] == 'medium'
		assert d['api_name'] == 'my_api'
		assert d['docs_info'] == {'params': ['a', 'b']}
		assert d['code_info'] == {'params': ['a', 'b', 'c']}