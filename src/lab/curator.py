"""GUIDE Phần 3 - Người tuyển chọn skill (skill curator): tự viết skill từ các lần chạy thất bại.   >>> SINH VIÊN CÀI ĐẶT curate_skills <<<

Pseudo-code: guides/pseudocode/04_curator.md
Kiểm tra:    pytest tests/test_04_curator.py
Chạy thật:   python -m lab.curator
"""
import json
import re
from pathlib import Path

from .model import make_model
from .tasks import ROOT, eval_markers   # có sẵn: định danh của tác vụ đánh giá, tính lúc chạy

# ---- CÓ SẴN, KHÔNG SỬA: kiểm tra và tách khối skill (phần dễ sai và liên quan bảo mật) ----------------
SAFE_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def validate_skill(text: str, expected_name: str | None = None) -> list[str]:
    """Kiểm tra nội dung một SKILL.md. Trả về danh sách vấn đề (rỗng = hợp lệ).

    Quy tắc: có khối YAML frontmatter; `name` chữ thường/số/gạch ngang (tối đa 64 ký tự) và bằng `expected_name`
    nếu được truyền; có `description` (tối đa 1024 ký tự); phần thân tối đa 80 dòng; không chứa chuỗi nào của
    `eval_markers()`. Quy tắc về `name` cũng là biện pháp bảo mật: tên khối do LLM sinh ra được dùng để tạo
    đường dẫn, nên `../evil` không được lọt qua.
    """
    problems = []
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text.strip() + "\n", re.S)
    if not m:
        return ["missing YAML frontmatter"]
    front, body = m.groups()
    name = re.search(r"^name:\s*(.+)$", front, re.M)
    desc = re.search(r"^description:\s*(.+)$", front, re.M)
    n = name.group(1).strip() if name else ""
    if not SAFE_NAME.fullmatch(n) or len(n) > 64:
        problems.append("invalid name")
    elif expected_name is not None and n != expected_name:
        problems.append("name differs from the block name")
    if not desc or len(desc.group(1).strip()) > 1024:
        problems.append("missing or too long description")
    if len(body.strip().splitlines()) > 80:
        problems.append("body longer than 80 lines")
    low = text.lower()
    for marker in eval_markers():
        if marker in low:
            problems.append(f"mentions evaluation material: {marker}")
    return problems


def parse_skill_blocks(reply: str) -> list[tuple[str, str]]:
    """Tách câu trả lời của LLM thành danh sách (name, nội dung SKILL.md).

    Khuôn dạng: `=== SKILL: <name> ===` ... `=== END ===`. Một khối kết thúc ở điểm nào đến trước trong ba điểm:
    `=== END ===`, tiêu đề `=== SKILL:` kế tiếp, hoặc cuối văn bản (LLM đôi khi quên dòng END).
    """
    pattern = re.compile(r"^=== SKILL: (\S+) ===[ \t]*\n(.*?)(?=^=== END ===|^=== SKILL: |\Z)", re.S | re.M)
    return [(name, text.strip()) for name, text in pattern.findall(str(reply))]
# --------------------------------------------------------------------------------------------------


def curate_skills(results_dir="results", source_condition="baseline", out_dir=None, model=None, max_skills: int = 3) -> list[Path]:
    """Đọc các lần chạy của TÁC VỤ HỌC (role == "learn") trong `source_condition`, nhờ LLM viết skill, ghi file.

    Các bước: nạp run.json + trace.md -> (nếu không có check nào thất bại: in cảnh báo và trả về [] mà KHÔNG gọi LLM)
    -> dựng prompt -> model.invoke(prompt) -> parse_skill_blocks -> validate_skill(text, expected_name=name)
    -> ghi `<out_dir>/<name>/SKILL.md`. Mặc định `out_dir` = <gốc lab>/skills/auto (dùng `ROOT` từ lab.tasks).
    Giữ tối đa `max_skills` skill hợp lệ; skill không hợp lệ bị bỏ qua.
    Prompt chứa, với mỗi check thất bại, TÊN và trường `detail` (lời nhận xét của bot đánh giá: phát biểu quy tắc bị vi phạm)
    cùng phần cuối của vết (trace). Với tác vụ học, `detail` chỉ phát biểu quy tắc, không chứa đáp án.
    Tuyệt đối KHÔNG đưa dữ liệu của tác vụ đánh giá (role == "eval") vào prompt.
    model mặc định: make_model() (lab.model).
    Trả về: danh sách đường dẫn SKILL.md đã ghi.
    """
    target_out_dir = Path(out_dir) if out_dir is not None else (ROOT / "skills" / "auto")
    cond_dir = Path(results_dir) / source_condition

    runs_with_failures = []
    if cond_dir.exists():
        for task_path in sorted(cond_dir.iterdir()):
            run_file = task_path / "run.json"
            if not run_file.exists():
                continue
            try:
                r = json.loads(run_file.read_text(encoding="utf-8"))
            except Exception:
                continue

            if r.get("role") != "learn":
                continue

            failed_checks = []
            for c in r.get("checks", []):
                if not c.get("passed"):
                    failed_checks.append((c.get("name", "unknown"), c.get("detail", "")))

            if not failed_checks:
                continue

            trace_file = task_path / "trace.md"
            trace_content = ""
            if trace_file.exists():
                try:
                    full_trace = trace_file.read_text(encoding="utf-8")
                    trace_content = full_trace[-6000:]
                except Exception:
                    trace_content = ""

            runs_with_failures.append({
                "task": r.get("task", task_path.name),
                "failed_checks": failed_checks,
                "trace": trace_content,
            })

    if not runs_with_failures:
        print("Cảnh báo: không có check thất bại ở tác vụ học")
        return []

    sections = []
    for r in runs_with_failures:
        checks_text = "\n".join(f"- Check '{name}': {detail}" for name, detail in r["failed_checks"])
        sections.append(
            f"### Task: {r['task']}\n"
            f"Failed checks:\n{checks_text}\n"
            f"Trace excerpt:\n```\n{r['trace']}\n```"
        )

    prompt = (
        f"You are curating procedural skills for an engineering and data agent.\n"
        f"Below are the failed checks (check name and evaluation feedback/rule) and execution traces from learning tasks.\n"
        f"Identify common procedural gaps, organizational rule violations, or missing verification steps.\n"
        f"Write at most {max_skills} concise skills to prevent these failures in similar tasks.\n\n"
        f"Rules for skills:\n"
        f"- Skills must be general: do not mention specific learning task IDs, specific input filenames, or benchmark numbers.\n"
        f"- Standard organizational conventions (e.g. Acme naming rules like clean.csv, meta fields, regression tests) ARE general conventions.\n"
        f"- Each skill must have YAML frontmatter with 'name' (lowercase alphanumeric with hyphens, max 64 chars) and 'description' (one sentence: WHEN to use this skill).\n"
        f"- Body should be actionable instructions or a checklist (maximum 40 lines).\n"
        f"- Format each skill strictly as:\n"
        f"=== SKILL: <name> ===\n"
        f"---\n"
        f"name: <name>\n"
        f"description: <when to use>\n"
        f"---\n"
        f"<skill body>\n"
        f"=== END ===\n\n"
        f"Failed learning runs:\n"
        + "\n\n".join(sections)
    )

    chat_model = model or make_model()
    res = chat_model.invoke(prompt)
    content = res.content
    if isinstance(content, list):
        reply_text = "".join(str(part.get("text", part)) if isinstance(part, dict) else str(part) for part in content)
    else:
        reply_text = str(content)

    blocks = parse_skill_blocks(reply_text)
    written = []

    for name, skill_text in blocks:
        if len(written) >= max_skills:
            break
        problems = validate_skill(skill_text, expected_name=name)
        if problems:
            print(f"Skipping skill '{name}': {', '.join(problems)}")
            continue

        skill_dir = target_out_dir / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(skill_text.strip() + "\n", encoding="utf-8")
        written.append(skill_file)

    return written


if __name__ == "__main__":
    for p in curate_skills():
        print("wrote", p)
