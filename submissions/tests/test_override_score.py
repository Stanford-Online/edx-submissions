"""
Test override scores.
"""

from mock import patch
from django.test import TestCase
from django.core.cache import cache
from django.db import DatabaseError
from submissions import api as sub_api
from submissions.models import Score


class TestOverrideScore(TestCase):
    """
    Test overriding scores for a specific student on a specific problem.
    """

    STUDENT_ITEM = {
        'student_id': 'Test student',
        'course_id': 'Test course',
        'item_id': 'Test item',
        'item_type': 'Test item type',
    }

    def setUp(self):
        """
        Clear the cache.
        """
        cache.clear()

    def test_override_with_no_score(self):

        sub_api.score_override(
            self.STUDENT_ITEM,
            8,
            10,
        )

        self.assertEqual(sub_api.get_score(self.STUDENT_ITEM)['points_earned'], 8)
        self.assertEqual(sub_api.get_score(self.STUDENT_ITEM)['points_possible'], 10)

    def test_override_with_one_score(self):
        # Create a submission for the student and score it
        submission = sub_api.create_submission(self.STUDENT_ITEM, 'test answer')
        sub_api.set_score(submission['uuid'], 1, 10)

        sub_api.score_override(
            self.STUDENT_ITEM,
            5,
            10,
        )

        self.assertEqual(sub_api.get_score(self.STUDENT_ITEM)['points_earned'], 5)
        self.assertEqual(sub_api.get_score(self.STUDENT_ITEM)['points_possible'], 10)

    def test_override_after_reset_score(self):
        # Create a submission for the student and score it
        submission = sub_api.create_submission(self.STUDENT_ITEM, 'test answer')
        sub_api.set_score(submission['uuid'], 1, 10)

        # Reset score
        sub_api.reset_score(
            self.STUDENT_ITEM['student_id'],
            self.STUDENT_ITEM['course_id'],
            self.STUDENT_ITEM['item_id'],
        )

        sub_api.score_override(
            self.STUDENT_ITEM,
            5,
            10,
        )

        self.assertEqual(sub_api.get_score(self.STUDENT_ITEM)['points_earned'], 5)
        self.assertEqual(sub_api.get_score(self.STUDENT_ITEM)['points_possible'], 10)

    @patch.object(Score.objects, 'create')
    def test_database_error(self, create_mock):
        # Simulate a database error when creating the override score
        create_mock.side_effect = DatabaseError('Test error')
        with self.assertRaises(sub_api.SubmissionInternalError):
            sub_api.score_override(
                self.STUDENT_ITEM,
                7,
                10,
            )

    def test_override_doesnt_overwrite_submission_score(self):
        # Create a submission for the student and score it
        submission = sub_api.create_submission(self.STUDENT_ITEM, 'test answer')
        sub_api.set_score(submission['uuid'], 1, 10)

        sub_api.score_override(
            self.STUDENT_ITEM,
            8,
            10,
        )

        submission_score = sub_api.get_latest_score_for_submission(submission['uuid'])
        self.assertEqual(submission_score['points_earned'], 1)
        self.assertEqual(submission_score['points_possible'], 10)

        override_score = sub_api.get_score_override(self.STUDENT_ITEM)
        self.assertEqual(override_score['points_earned'], 8)
        self.assertEqual(override_score['points_possible'], 10)

    def test_get_override_when_no_override(self):
        sub_api.create_submission(self.STUDENT_ITEM, 'test answer')
        override_score = sub_api.get_score_override(self.STUDENT_ITEM)
        self.assertIsNone(override_score)

    def test_get_override_when_no_studentItem(self):
        override_score = sub_api.get_score_override(self.STUDENT_ITEM)
        self.assertIsNone(override_score)
