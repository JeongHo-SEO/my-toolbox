#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
학점 계산기 (GPA Calculator)
- 4.3 / 4.5 만점 체계 지원
- 평점 미반영 과목 처리 (학점교류, P/F 등)
- 재수강 및 성적 상한 처리
- 백분률 지원 (포털 입력값 기반 선형 보간)
- 포털 검증 출력
"""

# ─────────────────────────────────────────────────────────
#  유틸리티
# ─────────────────────────────────────────────────────────

def sep(title=""):
    width = 58
    if title:
        pad = (width - len(title) - 2) // 2
        extra = width - pad - len(title) - 2
        print(f"\n{'─' * pad} {title} {'─' * extra}")
    else:
        print("─" * width)

def get_grade_map(scale: str) -> dict:
    if scale == "4.3":
        return {
            "A+": 4.3, "A0": 4.0, "A-": 3.7,
            "B+": 3.3, "B0": 3.0, "B-": 2.7,
            "C+": 2.3, "C0": 2.0, "C-": 1.7,
            "D+": 1.3, "D0": 1.0, "D-": 0.7,
            "F":  0.0,
        }
    else:  # 4.5
        return {
            "A+": 4.5, "A": 4.0,
            "B+": 3.5, "B": 3.0,
            "C+": 2.5, "C": 2.0,
            "D+": 1.5, "D": 1.0,
            "F":  0.0,
        }

def ask_grade(prompt: str, grade_map: dict) -> str:
    hint = "/".join(grade_map.keys())
    while True:
        raw = input(f"    {prompt} [{hint}]: ").strip().upper()
        normalized = raw.replace("O", "0")
        if normalized in grade_map:
            return normalized
        if raw in grade_map:
            return raw
        print("      ⚠  유효하지 않은 성적입니다. 다시 입력해주세요.")

def ask_float(prompt: str, min_val=None, max_val=None) -> float:
    while True:
        try:
            val = float(input(f"    {prompt}: ").strip())
            if min_val is not None and val < min_val:
                print(f"      ⚠  {min_val} 이상의 값을 입력해주세요.")
                continue
            if max_val is not None and val > max_val:
                print(f"      ⚠  {max_val} 이하의 값을 입력해주세요.")
                continue
            return val
        except ValueError:
            print("      ⚠  숫자를 입력해주세요.")

def ask_float_optional(prompt: str):
    raw = input(f"    {prompt} (모르면 Enter 스킵): ").strip()
    if raw == "":
        return None
    try:
        return float(raw)
    except ValueError:
        print("      ⚠  숫자가 아니어서 건너뜁니다.")
        return None

def ask_int(prompt: str, min_val: int = 0) -> int:
    while True:
        try:
            val = int(input(f"    {prompt}: ").strip())
            if val < min_val:
                print(f"      ⚠  {min_val} 이상의 정수를 입력해주세요.")
                continue
            return val
        except ValueError:
            print("      ⚠  정수를 입력해주세요.")

def ask_credits(prompt: str = "학점 수 (예: 3)") -> float:
    return ask_float(prompt, min_val=0.5)

# ─────────────────────────────────────────────────────────
#  백분률 변환
#  두 기준점으로 선형 함수 결정:
#    (cur_gpa, cur_pct)  ← 포털 입력값
#    (max_gpa, 100.0)    ← A+ = 100점 고정 앵커
# ─────────────────────────────────────────────────────────
def make_pct_fn(cur_gpa: float, cur_pct: float, max_gpa: float):
    if abs(max_gpa - cur_gpa) < 1e-9:
        return lambda gpa: cur_pct
    slope = (100.0 - cur_pct) / (max_gpa - cur_gpa)
    intercept = cur_pct - slope * cur_gpa
    def fn(gpa: float) -> float:
        return max(0.0, min(100.0, slope * gpa + intercept))
    return fn

def fmt_gpa(gpa: float, max_gpa: float, pct_fn=None) -> str:
    base = f"{gpa:.3f} / {max_gpa}"
    if pct_fn is not None:
        return f"{base}  ({pct_fn(gpa):.1f}%)"
    return base

# ─────────────────────────────────────────────────────────
#  메인
# ─────────────────────────────────────────────────────────

def main():
    print("\n" + "═" * 58)
    print("           🎓  학점 계산기  (GPA Calculator)")
    print("═" * 58)

    # ── STEP 1 : GPA 체계 선택 ──────────────────────────────
    sep("STEP 1 │ GPA 체계 선택")
    print("  [1]  4.3 만점  (A+ / A0 / A-  구조)")
    print("  [2]  4.5 만점  (A+ / A  구조, 0.5 단위)")
    while True:
        ch = input("    선택 (1 또는 2): ").strip()
        if ch in ("1", "2"):
            scale = "4.3" if ch == "1" else "4.5"
            break
        print("      ⚠  1 또는 2를 입력해주세요.")

    grade_map = get_grade_map(scale)
    max_gpa   = float(scale)
    print(f"  ✓  {scale} 만점 체계 선택됨")
    print(f"     유효 성적: {', '.join(grade_map.keys())}")

    # ── STEP 2 : 기존 평점 미반영 과목 ───────────────────────
    sep("STEP 2 │ 기존 평점 미반영 과목")
    print("  (지금까지 수강한 학점교류 / P·F 등, GPA 미포함 과목)")

    nc_count   = ask_int("미반영 과목 수 (없으면 0)")
    nc_credits = 0.0
    if nc_count > 0:
        nc_credits = ask_float("총 학점 수 (예: 6)")
    print(f"  ✓  기존 미반영 과목: {nc_count}개 / {nc_credits:.1f}학점")

    # ── STEP 3 : 현재 누적 수강 이력 ─────────────────────────
    sep("STEP 3 │ 현재 누적 수강 이력 (포털 기준)")
    print("  학교 포털의 이수학점·평점평균·백분률을 입력하세요.")

    cur_credits = ask_float("이수 학점 합계 (취득학점, 예: 122)")
    cur_gpa     = ask_float(f"현재 누적 GPA / 평점평균 (0.0 ~ {max_gpa})",
                            min_val=0.0, max_val=max_gpa)
    cur_pct     = ask_float_optional("현재 백분률 (평점평균 백분률, 예: 89.8)")

    cur_gp = cur_gpa * cur_credits
    pct_fn = make_pct_fn(cur_gpa, cur_pct, max_gpa) if cur_pct is not None else None

    # ── 포털 검증 ────────────────────────────────────────────
    sep("🔍 포털 검증")
    print(f"  입력된 이수학점    :  {cur_credits:.1f}")
    print(f"  입력된 평점평균    :  {cur_gpa:.3f}  / {max_gpa}")
    if cur_pct is not None:
        computed = pct_fn(cur_gpa)
        match = "✓ 일치" if abs(computed - cur_pct) < 0.05 else f"≈ {computed:.1f}% (근사값)"
        print(f"  입력된 백분률      :  {cur_pct:.1f} %  {match}")
        print(f"  백분률 환산 기준   :  GPA {max_gpa} → 100.0%  /  GPA {cur_gpa:.3f} → {cur_pct:.1f}%")
        print(f"  (이후 GPA 예측치의 백분률은 위 두 기준점 선형 보간으로 계산됩니다)")
    else:
        print(f"  백분률             :  (미입력 — 이후 출력에서 생략됩니다)")

    # ── STEP 4 : 재수강 예정 과목 ────────────────────────────
    sep("STEP 4 │ 재수강 예정 과목")

    retake_list    = []
    retake_cap     = None
    retake_cap_str = ""

    rt_count = ask_int("재수강 예정 과목 수 (없으면 0)")

    if rt_count > 0:
        retake_cap_str = ask_grade("재수강 성적 상한선 (학교 규정)", grade_map)
        retake_cap     = grade_map[retake_cap_str]
        print(f"  ✓  성적 상한: {retake_cap_str}  ({retake_cap}점)")

        for i in range(rt_count):
            print(f"\n  [재수강 {i+1}]")
            name   = input("    과목명: ").strip()
            creds  = ask_credits()
            orig_g = ask_grade("기존 취득 성적", grade_map)
            exp_g  = ask_grade("예상 재수강 성적", grade_map)

            raw_pts = grade_map[exp_g]
            eff_pts = min(raw_pts, retake_cap)
            capped  = raw_pts > retake_cap

            retake_list.append({
                "name":       name,
                "credits":    creds,
                "orig_grade": orig_g,
                "orig_pts":   grade_map[orig_g],
                "exp_grade":  exp_g,
                "raw_pts":    raw_pts,
                "eff_pts":    eff_pts,
                "capped":     capped,
            })
            if capped:
                print(f"      ℹ  {exp_g} 예상이지만 상한 적용 → {retake_cap_str} ({retake_cap}점)")
    else:
        print("  재수강 예정 과목 없음.")

    retake_names = {c["name"] for c in retake_list}

    # ── STEP 5 : 이번 학기 수강 예정 과목 ───────────────────
    sep("STEP 5 │ 이번 학기 수강 예정 과목")
    if retake_names:
        print(f"  ℹ  등록된 재수강 과목: {', '.join(retake_names)}")
        print("     → 과목명이 일치하면 재수강으로 자동 처리됩니다.")

    sem_count = ask_int("이번 학기 수강 과목 수", min_val=1)

    sem_courses      = []
    retakes_this_sem = []
    retakes_pending  = list(retake_list)

    for i in range(sem_count):
        print(f"\n  [이번 학기 과목 {i+1}]")
        name  = input("    과목명: ").strip()
        creds = ask_credits()

        while True:
            r = input("    GPA 반영 여부? (y = 반영 / n = 미반영·P/F·학점교류): ").strip().lower()
            if r in ("y", "n"):
                is_reflected = r == "y"
                break
            print("      ⚠  y 또는 n을 입력해주세요.")

        if not is_reflected:
            sem_courses.append({
                "name": name, "credits": creds, "grade": "미반영",
                "raw_pts": None, "eff_pts": None, "is_retake": False,
                "orig_pts": None, "capped": False, "reflected": False,
            })
            print("      ✓  GPA 미반영 과목으로 처리됨")
            continue

        exp_g      = ask_grade("예상 성적", grade_map)
        matched_rt = next((c for c in retakes_pending if c["name"] == name), None)

        if matched_rt:
            retakes_pending.remove(matched_rt)
            retakes_this_sem.append(matched_rt)
            raw_pts = grade_map[exp_g]
            eff_pts = min(raw_pts, retake_cap)
            capped  = raw_pts > retake_cap
            sem_courses.append({
                "name": name, "credits": creds, "grade": exp_g,
                "raw_pts": raw_pts, "eff_pts": eff_pts, "is_retake": True,
                "orig_pts": matched_rt["orig_pts"], "capped": capped, "reflected": True,
            })
            note = f"상한 적용: {retake_cap_str} ({retake_cap:.1f}점)" if capped else "상한 이하"
            print(f"      ✓  재수강 과목으로 처리됨  ({note})")
        else:
            if name in retake_names:
                print(f"      ℹ  '{name}'은 이미 추가되었거나 목록에 없어 일반 과목으로 처리합니다.")
            sem_courses.append({
                "name": name, "credits": creds, "grade": exp_g,
                "raw_pts": grade_map[exp_g], "eff_pts": grade_map[exp_g],
                "is_retake": False, "orig_pts": None, "capped": False, "reflected": True,
            })

    # ── 계산 ─────────────────────────────────────────────────
    sem_reflected = [c for c in sem_courses if c["reflected"]]
    sem_nc        = [c for c in sem_courses if not c["reflected"]]

    sem_credits = sum(c["credits"] for c in sem_reflected)
    sem_gp_sum  = sum(c["credits"] * c["eff_pts"] for c in sem_reflected)
    sem_gpa     = sem_gp_sum / sem_credits if sem_credits else 0.0

    new_gp      = cur_gp
    new_credits = cur_credits
    for c in sem_reflected:
        if c["is_retake"]:
            new_gp += (c["eff_pts"] - c["orig_pts"]) * c["credits"]
        else:
            new_gp      += c["eff_pts"] * c["credits"]
            new_credits += c["credits"]

    new_gpa   = new_gp / new_credits if new_credits else 0.0
    delta_sem = new_gpa - cur_gpa

    fut_gp      = new_gp
    fut_credits = new_credits
    for c in retakes_pending:
        fut_gp += (c["eff_pts"] - c["orig_pts"]) * c["credits"]

    fut_gpa   = fut_gp / fut_credits if fut_credits else 0.0
    delta_fut = fut_gpa - new_gpa

    # ── 출력 ─────────────────────────────────────────────────
    sep("📊 결과 출력")

    total_sem_credits = sum(c["credits"] for c in sem_courses)
    print(f"\n  ┌─ 이번 학기 과목별 성적 (총 {total_sem_credits:.1f}학점 수강)")
    if sem_reflected:
        print(f"  │  ▸ GPA 반영 ({sem_credits:.1f}학점)")
        for c in sem_reflected:
            tag   = " [재수강]" if c["is_retake"] else ""
            cap_t = f" ※→{retake_cap_str}" if c["capped"] else ""
            pts_s = f"{c['eff_pts']:.2f}" if c["capped"] else f"{c['raw_pts']:.2f}"
            print(f"  │     {c['name']:<20}  {c['grade']} ({pts_s})  {c['credits']:.1f}학점{tag}{cap_t}")
    if sem_nc:
        nc_total = sum(c["credits"] for c in sem_nc)
        print(f"  │  ▸ GPA 미반영 ({nc_total:.1f}학점)")
        for c in sem_nc:
            print(f"  │     {c['name']:<20}  P/F·학점교류  {c['credits']:.1f}학점")

    if sem_reflected:
        print(f"  └──► 이번 학기 GPA:  {fmt_gpa(sem_gpa, max_gpa, pct_fn)}")
    else:
        print(f"  └──► GPA 반영 과목 없음")

    arrow_s = "▲" if delta_sem >= 0 else "▼"
    print(f"\n  ┌─ 이번 학기 반영 후 누적 GPA")
    print(f"  │   이전 누적 GPA  :  {fmt_gpa(cur_gpa, max_gpa, pct_fn)}  [{cur_credits:.1f}학점]")
    print(f"  └──► 갱신 누적 GPA :  {fmt_gpa(new_gpa, max_gpa, pct_fn)}  ({arrow_s}{abs(delta_sem):.3f})  [{new_credits:.1f}학점]")

    if retakes_pending:
        arrow_f = "▲" if delta_fut >= 0 else "▼"
        print(f"\n  ┌─ 추후 재수강 완료 시 예상 (잔여 {len(retakes_pending)}개 과목)")
        for c in retakes_pending:
            cap_t = f"  ※→{retake_cap_str} ({c['eff_pts']:.2f})" if c["capped"] else ""
            print(f"  │   {c['name']:<20}  {c['orig_grade']} → {c['exp_grade']}{cap_t}")
        print(f"  └──► 재수강 완료 후 예상 GPA:  {fmt_gpa(fut_gpa, max_gpa, pct_fn)}  ({arrow_f}{abs(delta_fut):.3f})")
    else:
        msg = "모든 재수강이 이번 학기에 처리됨." if retake_list else "재수강 예정 과목 없음."
        print(f"\n  ℹ  {msg}")

    # ── 요약 ─────────────────────────────────────────────────
    sep("📋 요약")
    rows = []
    if sem_reflected:
        rows.append(("이번 학기 GPA",          fmt_gpa(sem_gpa, max_gpa, pct_fn)))
    rows.append(("갱신 누적 GPA",              fmt_gpa(new_gpa, max_gpa, pct_fn)))
    if retakes_pending:
        rows.append(("재수강 완료 후 예상 GPA", fmt_gpa(fut_gpa, max_gpa, pct_fn)))

    label_w = max(len(r[0]) for r in rows) + 2
    for label, val in rows:
        print(f"  {label:<{label_w}}│  {val}")
    sep()
    print()

if __name__ == "__main__":
    main()
