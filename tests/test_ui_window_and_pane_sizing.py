import re
from pathlib import Path
from bs4 import BeautifulSoup

def test_run_py_window_dimensions():
    run_py = Path("run.py")
    assert run_py.exists()
    content = run_py.read_text(encoding="utf-8")
    assert "height=840" in content
    assert "min_size=(1024, 660)" in content

def test_right_pane_bottom_spacer_and_css():
    right_pane_path = Path("app/ui/components/right_pane.html")
    assert right_pane_path.exists()
    content = right_pane_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(content, "html.parser")

    spacer = soup.find(class_="inspector-bottom-spacer")
    assert spacer is not None, "inspector-bottom-spacer must be present in right_pane.html"

    style_path = Path("app/ui/css/style.css")
    assert style_path.exists()
    style_content = style_path.read_text(encoding="utf-8")
    assert ".inspector-bottom-spacer" in style_content
    assert "min-height: 0;" in style_content
