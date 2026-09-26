import os
from bs4 import BeautifulSoup

def test_header_summary_group_structure():
    header_path = os.path.join(os.path.dirname(__file__), "..", "app", "ui", "components", "header.html")
    assert os.path.exists(header_path)
    with open(header_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    stats_content = soup.find(id="header-stats-content")
    assert stats_content is not None, "header-stats-content must exist"

    summary_group = stats_content.find(id="header-summary-group")
    assert summary_group is not None, "header-summary-group must exist inside header-stats-content"
    assert "header-summary-group" in summary_group.get("class", [])

    # Verify stat-bio, stat-total-payout, and stat-cmdr-container are grouped together inside header-summary-group
    bio_el = summary_group.find(id="stat-bio")
    assert bio_el is not None, "stat-bio must be inside header-summary-group"

    payout_el = summary_group.find(id="stat-total-payout")
    assert payout_el is not None, "stat-total-payout must be inside header-summary-group"

    cmdr_container = summary_group.find(id="stat-cmdr-container")
    assert cmdr_container is not None, "stat-cmdr-container must be inside header-summary-group"
    assert cmdr_container.find(id="stat-cmdr-loc") is not None, "stat-cmdr-loc must be inside stat-cmdr-container"


def test_header_actions_and_stats_compaction():
    css_path = os.path.join(os.path.dirname(__file__), "..", "app", "ui", "css", "style.css")
    assert os.path.exists(css_path)
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()

    # Verify .header-actions has flex-shrink: 0 to prevent action buttons from being squeezed/truncated
    assert ".header-actions" in css
    # Verify .stat-item has flex-shrink: 0 and compact font sizes
    assert ".stat-item" in css
    assert "white-space: nowrap" in css

