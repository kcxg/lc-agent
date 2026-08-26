from types import SimpleNamespace

from lc_agent.server.routes.file_changes import _build_hunk_diff


def test_edit_after_create_does_not_render_created_file_as_full_addition():
    changes = [
        SimpleNamespace(
            change_type="create",
            old_string=None,
            new_string="10\n11\n12\n13\n14",
            move_destination=None,
        ),
        SimpleNamespace(
            change_type="edit",
            old_string="12",
            new_string="12b",
            move_destination=None,
        ),
    ]

    hunks = _build_hunk_diff(changes, "t2.py")

    assert hunks == [
        {
            "type": "edit",
            "removed": ["12"],
            "added": ["12b"],
        }
    ]
