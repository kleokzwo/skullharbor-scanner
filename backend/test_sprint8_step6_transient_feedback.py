from pathlib import Path


def test_page_navigation_clears_transient_feedback():
    src = (Path(__file__).resolve().parents[1] / "frontend" / "src" / "main.jsx").read_text()
    assert 'useEffect(()=>{\n    setError("");\n    setTargetMessage("");\n  },[page]);' in src


if __name__ == "__main__":
    test_page_navigation_clears_transient_feedback()
    print("sprint8 step6 transient feedback tests: OK")
