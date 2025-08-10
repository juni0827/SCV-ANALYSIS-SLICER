import ui
from utils import AppState
from unittest.mock import patch

def test_drag_drop_triggers_file_load(tmp_path):
    csv = tmp_path / "sample.csv"
    csv.write_text("a,b\n1,2\n")
    state = AppState()
    with patch("ui.on_file_selected") as mock_select:
        ui.on_files_dropped(None, [str(csv)], state)
        mock_select.assert_called_once()
        called_state, called_path = mock_select.call_args[0]
        assert called_state is state
        assert called_path == str(csv)
