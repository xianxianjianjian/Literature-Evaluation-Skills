#!/usr/bin/env python3
"""Build and validate v1.4.2 role-aware exact-mirror style evidence."""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import sys
from pathlib import Path
from typing import Any

from exact_mirror import FRAME_ROLES, TRANSLATABLE_FRAME_ROLES, frame_role, load_jsonl
from extract_text_frames_impl import font_emphasis


class StyleFidelityError(ValueError):
    pass


def style_fingerprint(frame: dict[str, Any]) -> dict[str, Any]:
    """Normalize source styling that must survive translation."""
    color = frame.get("text_rgb", [0, 0, 0])
    return {
        "font_family": str(frame.get("source_font") or ""),
        "font_size_pt": round(float(frame.get("source_font_size_pt", 0)), 3),
        "leading_pt": round(float(frame.get("source_leading_pt", 0)), 3),
        "weight": str(frame.get("weight") or "regular").lower(),
        "italic": bool(frame.get("italic", False)),
        "color_rgb": [float(value) for value in color],
        "alignment": str(frame.get("alignment") or "left").lower(),
        "superscript": bool(frame.get("superscript", False)),
        "first_line_indent_pt": round(float(frame.get("first_line_indent_pt", 0.0)), 3),
        "paragraph_spacing_before_pt": round(float(frame.get("paragraph_spacing_before_pt", 0.0)), 3),
        "paragraph_spacing_after_pt": round(float(frame.get("paragraph_spacing_after_pt", 0.0)), 3),
        "baseline_offset_pt": round(float(frame.get("baseline_offset_pt", 0.0)), 3),
    }


def default_style_map(frames: list[dict[str, Any]]) -> dict[str, Any]:
    """Create a reusable CJK map while preserving each source role's hierarchy."""
    role_sizes: dict[str, list[float]] = {}
    for frame in frames:
        role_sizes.setdefault(frame_role(frame), []).append(
            float(frame.get("source_font_size_pt", 0))
        )
    styles: dict[str, dict[str, Any]] = {}
    for role in sorted({frame_role(frame) for frame in frames}):
        sizes = sorted(value for value in role_sizes.get(role, []) if value > 0)
        source_median = sizes[len(sizes) // 2] if sizes else 10.0
        styles[role] = {
            "cjk_font_family": "SimHei" if role in {'TITLE', 'H1', 'H2', 'H3'} else "SimSun",
            "source_median_size_pt": round(source_median, 3),
            "size_ratio_range": [0.95, 1.10],
            "leading_ratio_range": [1.15, 1.45],
            "preserve_weight": True,
            "preserve_italic": True,
            "preserve_color": True,
            "preserve_alignment": True,
            "preserve_superscript": True,
        }
    return {
        "schema_version": 1,
        "contract_version": "1.4.2",
        "roles": styles,
    }


def validate_style_map(style_map: dict[str, Any], frames: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(style_map, dict) or style_map.get("schema_version") != 1:
        raise StyleFidelityError("style_map.json schema_version must be 1.")
    roles = style_map.get("roles")
    if not isinstance(roles, dict):
        raise StyleFidelityError("style_map.json requires a roles object.")
    used_roles = {frame_role(frame) for frame in frames}
    unknown = used_roles - FRAME_ROLES
    missing = used_roles - set(roles)
    if unknown:
        raise StyleFidelityError(f"Unknown frame roles: {sorted(unknown)}")
    if missing:
        raise StyleFidelityError(f"Style map is missing roles: {sorted(missing)}")
    for role in used_roles:
        rule = roles[role]
        if not isinstance(rule, dict) or rule.get("cjk_font_family") not in {'SimSun', 'SimHei'}:
            raise StyleFidelityError(f"Role {role}: renderer supports embedded SimSun/SimHei only.")
        for field, lower, upper in (
            ("size_ratio_range", 0.95, 1.10),
            ("leading_ratio_range", 1.15, 1.45),
        ):
            values = rule.get(field)
            if (
                not isinstance(values, list) or len(values) != 2
                or not all(isinstance(value, (int, float)) and math.isfinite(value) for value in values)
                or values[0] < lower or values[1] > upper or values[0] > values[1]
            ):
                raise StyleFidelityError(
                    f"Role {role} has invalid {field}; allowed envelope is {lower}-{upper}."
                )
        for field in (
            "preserve_weight", "preserve_italic", "preserve_color",
            "preserve_alignment", "preserve_superscript",
        ):
            if rule.get(field) is not True:
                raise StyleFidelityError(f"Role {role} must declare {field}=true.")
    if "BODY" in roles and any(role in roles for role in {"TITLE", "H1", "H2", "H3"}):
        body = float(roles["BODY"].get("source_median_size_pt", 0))
        heading_sizes = [
            float(roles[role].get("source_median_size_pt", 0))
            for role in ("TITLE", "H1", "H2", "H3") if role in roles
        ]
        if heading_sizes and max(heading_sizes) <= body:
            raise StyleFidelityError("Heading/title hierarchy must remain larger than BODY.")
    return {"used_roles": sorted(used_roles), "mapped_roles": sorted(set(roles) & used_roles)}


def validate_rendered_styles(
    frames: list[dict[str, Any]], style_map: dict[str, Any]
) -> dict[str, Any]:
    """Validate per-frame rendered-style evidence against source fingerprints."""
    validate_style_map(style_map, frames)
    failures: list[dict[str, str]] = []
    rows: list[dict[str, Any]] = []
    for frame in frames:
        role = frame_role(frame)
        source = style_fingerprint(frame)
        rendered = frame.get("rendered_style")
        frame_failures: list[str] = []
        if role in TRANSLATABLE_FRAME_ROLES:
            if not isinstance(rendered, dict):
                frame_failures.append("missing rendered_style")
            else:
                rule = style_map["roles"][role]
                if rendered.get("font_family") != rule["cjk_font_family"]:
                    frame_failures.append("CJK font mapping mismatch")
                size_ratio = float(rendered.get("font_size_pt", 0)) / max(source["font_size_pt"], 0.001)
                leading_ratio = float(rendered.get("leading_pt", 0)) / max(
                    float(rendered.get("font_size_pt", 0)), 0.001
                )
                # rendered_style is serialized to three decimals, so compare
                # against the declared envelope with one-thousandth rounding tolerance.
                epsilon = 1e-3
                if not rule["size_ratio_range"][0] - epsilon <= size_ratio <= rule["size_ratio_range"][1] + epsilon:
                    frame_failures.append("font-size ratio outside role range")
                if not rule["leading_ratio_range"][0] - epsilon <= leading_ratio <= rule["leading_ratio_range"][1] + epsilon:
                    frame_failures.append("leading ratio outside role range")
                comparisons = {
                    "weight": source["weight"], "italic": source["italic"],
                    "color_rgb": source["color_rgb"], "alignment": source["alignment"],
                    "superscript": source["superscript"],
                    "first_line_indent_pt": source["first_line_indent_pt"],
                    "paragraph_spacing_before_pt": source["paragraph_spacing_before_pt"],
                    "paragraph_spacing_after_pt": source["paragraph_spacing_after_pt"],
                    "baseline_offset_pt": source["baseline_offset_pt"],
                }
                for field, expected in comparisons.items():
                    if rendered.get(field) != expected:
                        frame_failures.append(f"{field} not preserved")
                expected_runs = [
                    {
                        "target_text": str(run.get("target_text") or ""),
                        "occurrence": int(run.get("occurrence", 1)),
                        "font_family": str(run.get("font_family") or rule["cjk_font_family"]),
                        "weight": str(run.get("weight") or source["weight"]).lower(),
                        "italic": bool(run.get("italic", source["italic"])),
                        "size_ratio": float(run.get("size_ratio", 1.0)),
                    }
                    for run in frame.get("style_runs", [])
                ]
                if rendered.get("style_runs", []) != expected_runs:
                    frame_failures.append("style_runs not preserved")
        if frame_failures:
            failures.append({"frame_id": str(frame.get("frame_id")), "detail": "; ".join(frame_failures)})
        rows.append({
            "frame_id": frame.get("frame_id"), "role": role,
            "source_fingerprint": source, "rendered_style": rendered,
            "passed": not frame_failures,
        })
    return {
        "schema_version": 1,
        "contract_version": "1.4.2",
        "passed": not failures,
        "failures": failures,
        "frames": rows,
    }


def audit_pdf_styles(output_pdf: Path, inventory: dict[str, Any], frames: list[dict[str, Any]], style_map: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    """Measure source/output glyphs; generator-declared styles cannot close this gate.

    Mixed source formatting must be resolved into reviewed frames. A uniform
    replacement of a frame containing a differently styled heading fails.
    """
    import pdfplumber
    from pypdf import PdfReader
    from contextlib import ExitStack
    failures = []
    evidence = []
    sources = {row['source_id']: row for row in inventory['sources']}
    page_map = {(row['source_id'], row['source_page']): row['output_page'] for row in inventory['pages']}
    text_states = [_pdf_text_states(page) for page in PdfReader(output_pdf).pages]
    with ExitStack() as stack:
        target = stack.enter_context(pdfplumber.open(output_pdf))
        originals = {}
        for sid, row in sources.items():
            path = Path(row['pdf_path'])
            originals[sid] = stack.enter_context(pdfplumber.open(path if path.is_absolute() else base_dir/path))
        for frame in frames:
            if frame.get('translation_action') != 'TRANSLATE':
                continue
            fid = frame['frame_id']
            x0,y0,x1,y1 = frame['bbox_pt']
            inside = lambda c: x0 <= (c['x0']+c['x1'])/2 <= x1 and y0 <= (c['y0']+c['y1'])/2 <= y1 and c['text'].strip()
            src = [c for c in originals[frame['source_id']].pages[frame['source_page']-1].chars if inside(c)]
            out = [c for c in target.pages[page_map[(frame['source_id'],frame['source_page'])]-1].chars if inside(c) and re.search(r'[\u3400-\u9fff]', c['text'])]
            details = []
            # Ignore superscript reference numbers when determining font roles.
            src_words = [c for c in src if re.search(r'[A-Za-z]', c['text'])]
            emphasis = {font_emphasis(c['fontname']) for c in src_words}
            reviewed_runs = frame.get('style_runs', [])
            declared_emphasis = {
                (str(frame.get('weight','')).startswith('bold'), bool(frame.get('italic',False)))
            } | {
                (str(run.get('weight','regular')).startswith('bold'), bool(run.get('italic',False)))
                for run in reviewed_runs
            }
            if len(emphasis) > 1:
                if not reviewed_runs:
                    details.append('mixed source bold/italic spans require separate frames or run-level style mapping')
                elif emphasis != declared_emphasis:
                    details.append('run-level style mapping does not exactly match source emphasis')
            elif emphasis:
                source_bold, source_italic = next(iter(emphasis))
                if source_bold != str(frame.get('weight','')).startswith('bold') or source_italic != bool(frame.get('italic',False)):
                    details.append('declared source emphasis differs from actual source glyphs')
            families = {
                style_map['roles'][frame_role(frame)]['cjk_font_family'].lower()
            } | {str(run.get('font_family','')).lower() for run in reviewed_runs}
            operations = [item for item in text_states[page_map[(frame['source_id'],frame['source_page'])]-1] if x0 <= item['x'] <= x1 and y0 <= item['y'] <= y1]
            expected_bold = str(frame.get('weight','')).startswith('bold')
            expected_italic = bool(frame.get('italic',False))
            if operations:
                actual_emphasis = {
                    (item['render_mode'] in {1,2,5,6}, item['italic']) for item in operations
                }
                if not declared_emphasis <= actual_emphasis:
                    details.append('actual output text operators do not realize declared emphasis')
                if frame.get('superscript') and any(item['rise'] <= 0 for item in operations):
                    details.append('actual output text rise does not preserve superscript')
            if out:
                if any(not any(family in c['fontname'].lower() for family in families) for c in out):
                    details.append('actual output font differs from role mapping')
                source_size = statistics.median(c['size'] for c in src_words) if src_words else float(frame['source_font_size_pt'])
                ratio = statistics.median(c['size'] for c in out)/source_size
                if not .945 <= ratio <= 1.105:
                    details.append('actual output/source font size ratio outside envelope')
                expected_color = tuple(float(v) for v in frame.get('text_rgb',[0,0,0]))
                for c in out:
                    value = c.get('non_stroking_color')
                    color = tuple(value) if isinstance(value,(tuple,list)) else (float(value or 0),)*3
                    if len(color)==1:
                        color=color*3
                    if len(color)==3 and any(abs(a-b)>.01 for a,b in zip(color, expected_color)):
                        details.append('actual output color differs from source mapping')
                        break
            evidence.append({
                'frame_id': fid, 'source_emphasis': sorted(emphasis),
                'declared_emphasis': sorted(declared_emphasis),
                'actual_emphasis': sorted(actual_emphasis) if operations else [],
                'allowed_output_families': sorted(families),
                'actual_cjk_count':len(out), 'failures':details,
            })
            if details:
                failures.append({'frame_id':fid,'detail':'; '.join(details)})
    return {'passed':not failures,'method':'independent source/output PDF glyph inspection','failures':failures,'frames':evidence}


def _pdf_text_states(page: Any) -> list[dict[str, Any]]:
    """Read actual CJK overlay font/emphasis operators from the PDF stream."""
    from pypdf.generic import ContentStream
    fonts = page['/Resources'].get_object().get('/Font', {}).get_object()
    mapped = {str(key) for key,value in fonts.items() if any(name in str(value.get_object().get('/BaseFont','')).lower() for name in ('simsun','simhei'))}
    state = {'cm':(1.,0.,0.,1.,0.,0.),'tm':(1.,0.,0.,1.,0.,0.),'font':'','mode':0,'rise':0.}
    stack = []
    rows = []
    for args,op in ContentStream(page.get_contents(),page.pdf).operations:
        if op == b'q': stack.append(dict(state))
        elif op == b'Q' and stack: state=stack.pop()
        elif op == b'cm':
            a,b,c,d,e,f=map(float,args); A,B,C,D,E,F=state['cm']
            state['cm']=(a*A+b*C,a*B+b*D,c*A+d*C,c*B+d*D,e*A+f*C+E,e*B+f*D+F)
        elif op == b'Tm': state['tm']=tuple(map(float,args))
        elif op == b'Tf': state['font']=str(args[0])
        elif op == b'Tr': state['mode']=int(args[0])
        elif op == b'Ts': state['rise']=float(args[0])
        elif op in {b'Tj',b'TJ'} and state['font'] in mapped:
            a,b,c,d,e,f=state['cm']; tm=state['tm']
            rows.append({'x':tm[4]*a+tm[5]*c+e,'y':tm[4]*b+tm[5]*d+f,'render_mode':state['mode'],'italic':abs(tm[2])>.01,'rise':state['rise']})
    return rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=Path, required=True)
    parser.add_argument("--style-map", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        frames = load_jsonl(args.frames, "text-frame inventory")
        style_map = json.loads(args.style_map.read_text(encoding="utf-8-sig"))
        report = validate_rendered_styles(frames, style_map)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, StyleFidelityError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    sys.exit(main())
