"""
Temporary smoke test for DQSN.

Goal:
- Prove that GitHub Actions + pytest run correctly.
- If this passes, any remaining failures are from real tests,
  not the workflow itself.
"""

def test_placeholder_always_passes():
    """This test always passes."""
    assert True
