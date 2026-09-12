"""A deliberately bounded natural-language tool. The model is not a policy boundary.

Supported intents are trail assessment and catalog discovery. Uncertain inputs ask
for clarification instead of inferring a more favorable fitness level or timeframe.
"""
import re
import unicodedata
from .core import assess, discover
from .trails import TRAILS
from .telemetry import event

_WORDS = dict(zip(
    'one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty'.split(),
    range(1, 21),
))


def _normalize(text: str) -> str:
    text = text.lower().replace('’', "'").replace('ð', 'd').replace('þ', 'th')
    return ''.join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c))


def _fitness(q: str) -> int | None:
    if re.search(r"\b(don't train|dont train|do not train|no training|never train|not training|sedentary|beginner|not fit|unfit|out of shape)\b", q):
        return 1
    # A negative statement is not permission to upgrade the user.
    if re.search(r"\b(not|never|hardly|don't|dont|do not|cannot|can't|cant|unable|rarely)\b", q):
        return None
    regular = bool(re.search(r"\b(i train regularly|i am training regularly|i'm training regularly|i am very fit|i am athletic|i train a lot|i am in good shape)\b", q))
    sometimes = bool(re.search(r'\b(sometimes active|occasionally active|somewhat active|moderately active|i train sometimes|i sometimes train)\b', q))
    if regular and (sometimes or re.search(r'\b(or|sometimes|occasionally|somewhat|moderately)\b', q)):
        return None
    return 3 if regular else 2 if sometimes else None


def _weeks(q: str) -> int | None:
    if re.search(r'\b(ago|last|previous|every|since|already|was|were|or)\b', q):
        return None
    for word, value in _WORDS.items():
        q = re.sub(rf'\b{word}\b', str(value), q)
    # Do not pick the last number out of a range or alternatives.
    if re.search(r'\d\s*(?:or|to|and|[-–—/])\s*\d', q) or re.search(r'\bfor\s+\d+\s*(weeks?|months?)\b', q):
        return None
    matches = re.findall(r'(?<!\w)([-+]?\d+(?:[.,]\d+)?)\s*(weeks?|months?)\b', q)
    if len(matches) != 1:
        return None
    raw, unit = matches[0]
    try:
        value = float(raw.replace(',', '.')) * (4 if unit.startswith('month') else 1)
    except ValueError:
        return None
    return int(value) if value.is_integer() and 1 <= value <= 52 else None


def answer(query: str) -> dict:
    q = _normalize(query.strip())
    if re.search(r'\b(injur\w*|pain|hurt|sick|illness|prescri\w*|treatment|medication|pregnan\w*|medical|health|doctor|asthma|broken|fractur\w*|diabet\w*|surgery|operation|heart condition)\b|\bis it safe\b', q):
        return {'message': "I cannot give medical advice. Please talk to a doctor about health concerns before hiking. No trail verdict is a medical clearance."}
    if re.search(r'\b(ignore|override|pretend|bypass|disregard)\b|say (?:i am|i.m|you are|you.re) ready', q):
        return {'message': 'I cannot override the readiness rules. Tell me the trail, your training level, and the weeks you have.'}
    ids = [key for key in TRAILS if re.search(rf'\b{re.escape(_normalize(key))}\b', q)]
    discovery = bool(re.search(r'\b(discover|compare|recommend|which trails?|what trails?|what can i|where can i|find (?:me )?(?:a )?(?:trail|hike))\b', q))
    if len(ids) > 1:
        return {'message': 'Use the comparison view to compare two or three trails with the same training level and weeks.'}
    # Explicit unsupported places do not silently become an all-regions search.
    regions = [name for name in ('Norway', 'Iceland') if re.search(rf'\b{name.lower()}\b', q)]
    place = re.search(r'\bin\s+([a-z]+)(?:\s|[?.!,]|$)', q)
    if discovery and place and place[1] not in {'norway', 'iceland', 'a', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'twelve', 'twenty', 'good', 'the'}:
        event('catalog_demand', kind='unknown_region')
        return {'message': 'That region is not covered yet. I have verified catalog routes in Norway and Iceland.'}
    if not ids and not discovery:
        event('catalog_demand', kind='unknown_trail')
        return {'message': 'That trail is not covered yet. Choose a catalog trail, or ask what you can handle in Norway or Iceland.'}
    fit = _fitness(q)
    if fit is None:
        return {'message': "What is your training level? Choose I don't train, Sometimes active, or I train regularly."}
    weeks = _weeks(q)
    if weeks is None:
        return {'message': 'How many weeks do you have? Give one whole number from 1 to 52 weeks.'}
    # A keyword blacklist cannot identify every medical condition or qualification.
    # Fail closed on text outside the small supported request vocabulary instead
    # of discarding context and turning it into an affirmative readiness answer.
    remainder = q
    # Consume complete supported phrases, not individual words. Unconsumed text
    # (including non-Latin text and extra numbers) must not be silently dropped.
    for name in [*TRAILS, 'norway', 'iceland']:
        remainder = re.sub(rf'\b{re.escape(name)}\b', ' ', remainder)
    phrases = [
        "i don't train regularly", "i dont train regularly", "i do not train regularly",
        "i don't train", "i dont train", "i do not train", "i am not training",
        "no training", "not training", "i am sedentary", "i am a beginner",
        "i am out of shape", "i am not fit", "i am unfit",
        "i train regularly", "i am training regularly", "i'm training regularly",
        "i am very fit", "i am athletic", "i train a lot", "i am in good shape",
        "i am sometimes active", "i'm sometimes active", "sometimes active",
        "occasionally active", "somewhat active", "moderately active", "i train sometimes", "i sometimes train",
        "what can i handle", "what trails can i handle", "which trails can i handle",
        "which trails", "what trails", "where can i hike", "find me a trail", "find a trail",
        "recommend trails", "recommend", "discover", "compare",
    ]
    for phrase in sorted(phrases, key=len, reverse=True):
        remainder = re.sub(rf'\b{re.escape(phrase)}\b', ' ', remainder)
    for word, value in _WORDS.items():
        remainder = re.sub(rf'\b{word}\b', str(value), remainder)
    remainder = re.sub(r'\b(?:i have |with |in )?\d+(?:[.,]\d+)?\s*(?:weeks?|months?)\b', ' ', remainder)
    remainder = re.sub(r'\b(?:in|and|please)\b', ' ', remainder)
    if remainder.strip(' ,.!?():\t\n\r'):
        return {'message': 'I cannot confidently interpret the extra context. Use the training level and weeks controls for a fitness-only check. For any health concern, ask a doctor.'}
    if ids and not discovery:
        assessment = assess(ids[0], fit, weeks)
        return {'message': assessment['head'] + '. ' + assessment['why'], 'assessment': assessment, 'trail_id': ids[0]}
    filters = {'region': regions[0]} if len(regions) == 1 else {}
    rows = discover(fit, weeks, filters)
    return {'message': 'Ranked by your readiness in the weeks you have. Trails that need more time stay visible.', 'trails': rows}
