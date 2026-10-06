"""GUIDE Phần 1 - Định nghĩa subagent (tác tử con).   >>> SINH VIÊN CÀI ĐẶT <<<

Pseudo-code: guides/pseudocode/02_subagents.md
Kiểm tra:    pytest tests/test_02_agent.py
"""


def get_subagents() -> list[dict]:
    """Trả về danh sách subagent (ít nhất 2, tên khác nhau).

    Mỗi phần tử là một dict có các khóa bắt buộc:
      "name":          tên duy nhất (chữ thường, có thể có dấu gạch ngang)
      "description":   khi nào tác tử chính nên giao việc cho subagent này (viết như một hướng dẫn hành động)
      "system_prompt": chỉ dẫn cho subagent
    Gợi ý vai trò: explorer (đọc và báo cáo), implementer (thực hiện), reviewer (kiểm tra độc lập).
    """
    return [
        {
            "name": "explorer",
            "description": (
                "Use to explore the repository structure, read documentation/docstrings, "
                "or inspect raw data and log files before planning or making changes. "
                "Reports factual findings clearly without modifying any files."
            ),
            "system_prompt": (
                "You are an exploration subagent. Your role is to inspect workspace files, "
                "read documentation, and summarize observations. "
                "Do not create, modify, or delete any files; report factual details clearly."
            ),
        },
        {
            "name": "implementer",
            "description": (
                "Use to implement code fixes, write data processing logic, or perform log analysis "
                "strictly according to task instructions. Can execute Python commands and run tests "
                "to verify the solution before reporting back."
            ),
            "system_prompt": (
                "You are an implementation subagent. Your role is to write clean code, solve bugs, "
                "and generate required output files adhering strictly to specifications. "
                "Always run Python tests or validation commands to verify your work."
            ),
        },
        {
            "name": "reviewer",
            "description": (
                "Use to independently review completed outputs, verify files against requirements, "
                "check edge cases, and confirm that all rules are satisfied. Does not edit files."
            ),
            "system_prompt": (
                "You are an independent verification and review subagent. Your role is to inspect "
                "the created or modified files, check them against task rules, and verify correctness. "
                "Do not edit files; only report validation results and any discrepancies."
            ),
        },
    ]
