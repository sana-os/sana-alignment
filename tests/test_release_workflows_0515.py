import runpy
from pathlib import Path
import pytest

CHECKS = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'scripts/verify_release_0515.py'))


@pytest.mark.parametrize('name', ['sana-alignment.en.yml', 'sana-plan-and-align.en.yml'])
def test_distributed_workflow_preserves_input_mode_output_and_status_routes(name):
    CHECKS['check_workflow'](name)


def test_archived_operator_evidence_keeps_original_bytes():
    CHECKS['check_archive']()
