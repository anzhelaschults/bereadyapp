from beready.core import adapt_plan, build_plan


def test_old_missed_week_does_not_keep_repeating_after_recovery():
    plan = build_plan('laugavegur', 1, '2026-01-05', '2026-03-02')
    recovered = next(s for s in plan['sessions'] if s['week'] == 2 and s['kind'] == 'base')
    logs = [{'session_id': recovered['id'], 'done_at': recovered['date']}]
    adapted = adapt_plan(plan, logs, '2026-01-13')
    assert not any(s['adapted'] for s in adapted['sessions'])


def test_final_week_recovery_does_not_erase_lighter_instruction():
    plan = build_plan('laugavegur', 1, '2026-01-05', '2026-01-19')
    adapted = adapt_plan(plan, [], '2026-01-12')
    session = next(s for s in adapted['sessions'] if s['adapted'])
    assert session['label'].startswith('Lighter')


def test_previously_missed_week_is_not_reapplied_after_later_completed_week():
    plan = build_plan('laugavegur', 1, '2026-01-05', '2026-03-02')
    logs = [{'session_id': s['id'], 'done_at': s['date']} for s in plan['sessions'] if s['week']==2]
    assert not any(s['adapted'] for s in adapt_plan(plan, logs, '2026-01-19')['sessions'])
