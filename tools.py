"""HW4: source-grounded district lookup and safe arithmetic."""
import ast
import json
import math
import operator
import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent


def _corpus():
    with (DATA_DIR / 'corpus.jsonl').open(encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]


def _number(s):
    return float(s.replace(',', ''))


def _extract(text):
    """Parse the three prose layouts used by the 2025 district profiles."""
    patterns = {
        'founded': [r'founded in (\d{4})'],
        'area': [r'([\d,]+(?:\.\d+)?) square kilometres'],
        'budget': [r'budget (?:for 2025 was set at|amounted to|was) ([\d,]+(?:\.\d+)?) million tenge',
                   r"2025 budget amounted to ([\d,]+(?:\.\d+)?) million tenge",
                   r'2025 budget was ([\d,]+(?:\.\d+)?) million tenge'],
        'water': [r'(?:water use in 2025 came to|Households used) ([\d,]+(?:\.\d+)?) (megalitres|cubic metres)',
                  r'Households used ([\d,]+(?:\.\d+)?) (megalitres|cubic metres) of water'],
        'schools': [r'(\d+) schools'],
        'pupils': [r'([\d,]+) pupils'],
        'roads': [r'([\d,]+(?:\.\d+)?) km (?:of paved road|long)',
                  r'([\d,]+(?:\.\d+)?) km of paved road',
                  r'paved road network is ([\d,]+(?:\.\d+)?) km'],
    }
    result = {}
    for key, variants in patterns.items():
        for pattern in variants:
            m = re.search(pattern, text, re.I)
            if m:
                value = _number(m.group(1))
                if key == 'water' and m.group(2).lower() == 'cubic metres':
                    value /= 1000  # normalize to megalitres
                result[key] = int(value) if key in ('founded', 'schools', 'pupils') else value
                break

    # Three distinct census phrasings
    census_patterns = [
        r'2025 census recorded ([\d,]+) residents; the 2020 census had recorded ([\d,]+)',
        r'Census population:\s*([\d,]+) in 2020 and ([\d,]+) in 2025',
        r'2025 census counted ([\d,]+) residents, up from ([\d,]+) at the 2020 census',
    ]
    for i, pattern in enumerate(census_patterns):
        m = re.search(pattern, text, re.I)
        if m:
            a, b = int(m.group(1).replace(',', '')), int(m.group(2).replace(',', ''))
            result['population_2025'], result['population_2020'] = (b, a) if i == 1 else (a, b)
            break
    return result


ALIASES = {
    'population': 'population_2025', '2025 population': 'population_2025',
    'population 2025': 'population_2025', '2020 population': 'population_2020',
    'population 2020': 'population_2020', 'census 2020': 'population_2020',
    'area': 'area', 'land area': 'area', 'budget': 'budget',
    'water': 'water', 'water use': 'water', 'household water': 'water',
    'schools': 'schools', 'pupils': 'pupils', 'students': 'pupils',
    'roads': 'roads', 'paved road': 'roads', 'road length': 'roads',
    'founded': 'founded', 'founding year': 'founded', 'year founded': 'founded',
}
UNITS = {'population_2025': 'residents', 'population_2020': 'residents',
         'area': 'km2', 'budget': 'million tenge', 'water': 'megalitres',
         'schools': 'schools', 'pupils': 'pupils', 'roads': 'km', 'founded': 'year'}


def lookup(district, field):
    """Return one 2025 district fact with source, or a structured error."""
    if not isinstance(district, str) or not isinstance(field, str):
        return {'error': 'district and field must be strings'}
    district, field = district.strip(), field.strip().lower().replace('_', ' ')
    if not district or not field:
        return {'error': 'district and field are required'}
    canonical = ALIASES.get(field)
    if canonical is None:
        return {'error': 'unsupported field', 'supported_fields': sorted(ALIASES)}
    try:
        docs = _corpus()
    except (OSError, ValueError) as e:
        return {'error': 'corpus unavailable or invalid', 'detail': str(e)}
    profiles = [d for d in docs if 'district profile (2025)' in d['title'].lower()]
    doc = next((d for d in profiles if d['title'].split(' district profile')[0].casefold() == district.casefold()), None)
    if doc is None:
        return {'error': 'district not found', 'district': district}
    values = _extract(doc['text'])
    if canonical not in values:
        return {'error': 'fact not found', 'district': district, 'field': canonical, 'source': doc['id']}
    value, source = values[canonical], doc['id']
    # Read the correction notice instead of trusting a hard-coded corrected area.
    for correction in docs:
        if 'correction notice' not in correction['title'].lower():
            continue
        if canonical == 'area' and district.casefold() in correction['title'].casefold():
            match = re.search(r'correct area is ([\d,]+(?:\.\d+)?) square kilometres', correction['text'], re.I)
            if match:
                value, source = _number(match.group(1)), correction['id']
    return {'district': doc['title'].split(' district profile')[0], 'field': canonical,
            'value': value, 'unit': UNITS[canonical], 'source': source}


_BINARY = {ast.Add: operator.add, ast.Sub: operator.sub,
           ast.Mult: operator.mul, ast.Div: operator.truediv}
_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def calculate(expression):
    """Safe bounded +, -, *, / and parentheses; never executes Python code."""
    if not isinstance(expression, str) or not expression.strip() or len(expression) > 200:
        return {'error': 'invalid expression'}
    try:
        tree = ast.parse(expression, mode='eval')
        if sum(1 for _ in ast.walk(tree)) > 100:
            raise ValueError('expression too complex')

        def solve(node, depth=0):
            if depth > 30:
                raise ValueError('expression too deep')
            if isinstance(node, ast.Constant) and type(node.value) in (int, float):
                value = node.value
            elif isinstance(node, ast.BinOp) and type(node.op) in _BINARY:
                value = _BINARY[type(node.op)](solve(node.left, depth + 1), solve(node.right, depth + 1))
            elif isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
                value = _UNARY[type(node.op)](solve(node.operand, depth + 1))
            else:
                raise ValueError('unsupported expression')
            if not math.isfinite(value) or abs(value) > 1e12:
                raise ValueError('result too large or non-finite')
            return value

        return {'result': solve(tree.body)}
    except (SyntaxError, ValueError, ZeroDivisionError, OverflowError, TypeError) as e:
        return {'error': str(e)}
