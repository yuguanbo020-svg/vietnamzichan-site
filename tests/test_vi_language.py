import re
from pathlib import Path

def test_vi_language_no_cjk():
    root = Path(__file__).resolve().parents[1]
    vi_dir = root / "vi"
    assert vi_dir.exists(), "vi directory does not exist"

    # CJK Unified Ideographs range and common CJK block
    cjk_pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')

    violations = []
    for html_file in vi_dir.glob("**/*.html"):
        content = html_file.read_text(encoding="utf-8")
        # SEO attributes and the Chinese-language switch are navigation metadata,
        # not Vietnamese body copy.
        content = re.sub(r'<head>.*?</head>', '', content, flags=re.DOTALL)
        content = re.sub(r'<a href="/zh/[^"]*">中文</a>', '', content)
        matches = cjk_pattern.findall(content)
        if matches:
            # find snippets with context
            for line_no, line in enumerate(content.splitlines(), 1):
                if cjk_pattern.search(line):
                    violations.append((str(html_file.relative_to(root)), line_no, line.strip()))

    if violations:
        msg = f"Found CJK characters in {len(violations)} places under vi/**/*.html:\n"
        for path, line_no, snippet in violations:
            msg += f"  - {path}:{line_no} -> {snippet}\n"
        raise AssertionError(msg)


def test_language_switch_keeps_equivalent_path():
    root = Path(__file__).resolve().parents[1]
    sample = (root / "vi/categories/hotel/index.html").read_text(encoding="utf-8")
    assert 'href="/zh/categories/hotel/">中文</a>' in sample
    assert 'href="/en/categories/hotel/">English</a>' in sample
    assert 'hreflang="zh-CN" href="https://vietnamzichan.com/zh/categories/hotel/"' in sample
    assert 'hreflang="en" href="https://vietnamzichan.com/en/categories/hotel/"' in sample
