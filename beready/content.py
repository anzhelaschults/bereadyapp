"""Editorial draft, not signed-off route advice.

Grounded in the route descriptions linked by trails.py and supplied design notes.
Training level changes preparation emphasis, never the underlying terrain or risk.
"""

# Each crux has a sentence for not training, sometimes active, and training regularly.
_DRAFTS = {
    'dalsnuten': (
        'A short climb above Stavanger opens out over the surrounding hills and fjords when the weather is clear. The payoff comes without a full day on the mountain.',
        ('The final climb', 'hill', (
            'The short uphill finish may feel sustained if you are not used to walking uphill.',
            'A steady pace on the final climb matters more than rushing the short distance.',
            'Keep a comfortable pace on the uphill finish rather than treating it as a workout.')),
        ('Footing changes', 'footsteps', (
            'Use local walks to get used to uneven and wet ground before the summit path.',
            'Practise staying controlled on uneven descents, especially when the ground is wet.',
            'Regular training does not remove the need to slow down on wet or icy ground.')),
    ),
    'gaustatoppen': (
        'The climb leads onto a broad rocky summit with long views over the surrounding landscape in clear weather. Cloud can hide those views, so the walk itself needs to be worth your day.',
        ('A sustained climb', 'hill', (
            'The continuous uphill asks for a walking base that a short local stroll may not provide.',
            'Build comfort with sustained uphill walking rather than relying on occasional short sessions.',
            'Keep enough energy for the descent after the sustained climb.')),
        ('Rocky upper ground', 'footsteps', (
            'Uneven rock near the top makes slow, deliberate steps important when you are tired.',
            'Practise controlled descents so rocky footing does not become a surprise late in the day.',
            'Good fitness does not replace careful foot placement on the rocky upper section.')),
    ),
    'laugavegur': (
        'The route crosses volcanic highlands, dark lava and pale rhyolite before reaching the greener valley of Thorsmork. Over four days the landscape changes under your feet, with the work of each day carried into the next.',
        ('Four days in a row', 'calendar', (
            'Consecutive walking days are the main preparation gap when regular activity is not yet a habit.',
            'One active day is different from four, so recovery between walking days needs practice.',
            'Regular training helps, but repeated days with a pack still deserve a rehearsal.')),
        ('Rivers and weather', 'water', (
            'Cold river crossings and highland weather need local advice and judgment beyond a fitness plan.',
            'Practise using your kit, but check river and weather advice locally rather than treating training as protection.',
            'Strong fitness does not make river crossings or poor highland weather safe.')),
    ),
    'preikestolen': (
        'The path ends on a rock plateau above Lysefjord. You do not need to approach the edge to appreciate the view, and the route still asks for care on the way back.',
        ('Steep sections', 'hill', (
            'The steeper stretches can feel hard without a walking base, despite the day-hike length.',
            'Build steady uphill walking so the steep stretches do not use all your energy early.',
            'Pace the climbs with enough energy left for a controlled descent.')),
        ('An unguarded edge', 'ridge', (
            'The summit has unguarded drops, which fitness preparation cannot remove.',
            'Comfort with exercise is separate from comfort around the unguarded summit drops.',
            'Stay deliberate around the unguarded edge even if the walking feels easy.')),
    ),
    'besseggen': (
        'The ridge gives views between the mountain lakes Gjende and Bessvatnet. The exposed section is part of the route, not an optional challenge added to an easy walk.',
        ('The exposed ridge', 'ridge', (
            'The narrow ridge needs confidence on exposed ground as well as a base for the walking.',
            'Being sometimes active does not tell you how the exposed ridge will feel, so consider that separately.',
            'Fitness does not replace balance and calm movement on the exposed ridge.')),
        ('A full mountain day', 'calendar', (
            'A long day on uneven ground asks for more endurance than the distance alone suggests.',
            'Practise a sustained day on uneven ground and check the ferry plan before committing.',
            'Leave room for slower ridge travel and the ferry schedule rather than planning around your fastest pace.')),
    ),
    'fimmvorduhals': (
        'The crossing links Skogar and Thorsmork through high ground between the glaciers. Waterfalls, volcanic terrain and the valley descent make it a varied day, but the length is real.',
        ('A long crossing', 'hill', (
            'The long climb and descent require a sustained walking base before adding trail-specific practice.',
            'Build tolerance for a long day with both climbing and controlled downhill walking.',
            'Regular activity helps with endurance, but the long descent can still expose gaps in downhill preparation.')),
        ('The airy descent', 'ridge', (
            'Snow on the pass and the airy chained ridge on the descent need judgment that a training plan cannot supply.',
            'Check the pass and ridge conditions locally, separate from how your preparation is going.',
            'The Kattarhryggur ridge remains exposed regardless of fitness, and lingering snow can change the route.')),
    ),
    'kjeragbolten': (
        'The high ground above Lysefjord offers a view of the boulder and surrounding cliffs. Stepping onto the boulder is not a requirement of the walk and should not be the measure of a successful day.',
        ('Repeated steep ground', 'hill', (
            'The steep sections ask for a walking and strength base before you tackle a full mountain day.',
            'Prepare for repeated climbing and descending rather than one steady uphill effort.',
            'Save energy for the return across the steep sections, not just the outward climb.')),
        ('Chains and drops', 'ridge', (
            'Chain-assisted scrambling and unguarded drops are technical and exposure questions, not only fitness questions.',
            'Local terrain practice may help confidence, but it does not remove the chain scrambles or drops.',
            'A high training level is not a clearance for exposed scrambling or stepping onto the boulder.')),
    ),
    'trolltunga': (
        'The route reaches a rock ledge above Ringedalsvatnet after a substantial mountain approach. The viewpoint is only the halfway point of the day in practical terms, since you still need to return.',
        ('Time on your feet', 'calendar', (
            'The long approach leaves a large endurance gap if regular walking is not already part of your week.',
            'Occasional activity needs to become sustained walking preparation for the long outward and return journey.',
            'Even with regular training, rehearse a long day and protect enough energy for the return.')),
        ('Weather and the ledge', 'ridge', (
            'Mountain weather and unguarded drops remain outside what a fitness plan can make safe.',
            'Build kit familiarity and check local advice, without confusing preparation with favorable conditions.',
            'Strong fitness does not remove exposure at the ledge or the effect of changing mountain weather.')),
    ),
    'romsdalseggen': (
        'The ridge looks across Romsdalen and the surrounding mountains in clear weather. Its narrow sections are central to the route, so wanting the view is not a substitute for being comfortable with exposure.',
        ('Sustained ridge travel', 'hill', (
            'The climb and ridge travel need an endurance base before a full exposed day is realistic.',
            'Prepare for climbing followed by careful ridge movement, not just a fast uphill session.',
            'Pace the climb so fatigue does not undermine careful movement along the ridge.')),
        ('Exposure and chains', 'ridge', (
            'A narrow exposed ridge with chain scrambles needs skills and confidence beyond a training-level choice.',
            'Consider your comfort with exposure independently of the fitness verdict and check current route advice.',
            'Regular training does not remove the narrow ridge, chain scrambles or wind exposure.')),
    ),
}


def trail_content(trail_id: str, typical_conditions: str) -> dict:
    payoff, *cruxes = _DRAFTS[trail_id]
    return {
        'challenges': {
            str(level): [{'title': title, 'icon': icon, 'text': sentences[level - 1]}
                         for title, icon, sentences in cruxes]
            for level in (1, 2, 3)
        },
        'worth_it': payoff,
        'typical_conditions': typical_conditions,
        'review_status': 'review pending',
    }
