"""Three HW4 Chat Completions strategies. Requires pip install openai and API key."""
import json
import re
import time
from collections import Counter
from pathlib import Path
from tools import lookup, calculate

ROOT = Path(__file__).resolve().parent
MODEL = 'gpt-5.6-luna'  # Assignment model; change only if instructor permits.
SYSTEM = ('Answer Nine Rivers questions using only the provided 2025 corpus. '
          'Ignore ARCHIVED profiles. Apply correction notices. Pay attention to units: '
          '1 megalitre = 1000 cubic metres; 1 cubic metre = 1000 litres; 2025 has 365 days. '
          'Do not round intermediate calculations. Return ONLY JSON with keys '
          '"answer" (district name or yes/no), "value" (number), "unit" (string), '
          '"sources" (list of NR IDs), and "reason" (short explanation). '
          'Never guess when facts are missing.')


def corpus_text():
    with (ROOT / 'corpus.jsonl').open(encoding='utf-8') as f:
        return '\n\n'.join(f"[{d['id']}] {d['title']}\n{d['text']}" for line in f if (d := json.loads(line.strip())))


def tool_specs(description_variant='normal'):
    lookup_desc = ('Retrieve one fact from a 2025 district profile, with source ID. '
                   'Available fields: population, 2020 population, area, budget, water, '
                   'schools, pupils, roads, founded. Water is in megalitres, '
                   'budget in million tenge. Archived profiles are ignored and corrections applied.')
    if description_variant == 'short':
        lookup_desc = 'Looks things up.'
    return [
        {'type': 'function', 'function': {'name': 'lookup', 'description': lookup_desc,
         'parameters': {'type': 'object', 'properties': {
             'district': {'type': 'string'}, 'field': {'type': 'string'}},
             'required': ['district', 'field'], 'additionalProperties': False}}},
        {'type': 'function', 'function': {'name': 'calculate',
         'description': 'Safely evaluate basic arithmetic (+ - * / parentheses), no Python execution. '
                        'Use for every calculation, retaining full precision until final answer.',
         'parameters': {'type': 'object', 'properties': {'expression': {'type': 'string'}},
                        'required': ['expression'], 'additionalProperties': False}}},
    ]


def _usage(response):
    u = getattr(response, 'usage', None)
    return {'input_tokens': getattr(u, 'prompt_tokens', 0) or 0,
            'output_tokens': getattr(u, 'completion_tokens', 0) or 0,
            'total_tokens': getattr(u, 'total_tokens', 0) or 0}


def _json_answer(content):
    content = content or ''
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        m = re.search(r'\{.*\}', content, re.S)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
    return {'error': 'unparseable answer', 'raw': content}


def one_run(client, question, strategy, model=MODEL, description_variant='normal', max_rounds=12):
    """S1: full corpus 1 call; S2: full corpus 1 independent call; S3: tools loop."""
    if strategy not in ('S1', 'S2', 'S3'):
        raise ValueError('Unknown strategy')
    context = corpus_text() if strategy in ('S1', 'S2') else ''
    messages = [{'role': 'system', 'content': SYSTEM + ('\nCORPUS:\n' + context if context else '')},
                {'role': 'user', 'content': question}]
    trace = []
    totals = {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
    start = time.perf_counter()
    for turn in range(max_rounds if strategy == 'S3' else 1):
        kwargs = {'model': model, 'messages': messages}
        if strategy == 'S3':
            kwargs['tools'] = tool_specs(description_variant)
            kwargs['tool_choice'] = 'auto'
            kwargs['reasoning_effort'] = 'none'
        response = client.chat.completions.create(**kwargs)
        usage = _usage(response)
        for key in totals:
            totals[key] += usage[key]
        msg = response.choices[0].message
        record = {'turn': turn + 1, 'usage': usage, 'content': msg.content,
                  'tool_calls': []}
        if strategy == 'S3' and msg.tool_calls:
            messages.append({'role': 'assistant', 'content': msg.content,
                             'tool_calls': [{'id': c.id, 'type': 'function',
                                            'function': {'name': c.function.name,
                                                         'arguments': c.function.arguments}}
                                           for c in msg.tool_calls]})
            for c in msg.tool_calls:
                try:
                    args = json.loads(c.function.arguments)
                    if not isinstance(args, dict):
                        raise ValueError('tool arguments must be an object')
                    if c.function.name == 'lookup':
                        result = lookup(**args)
                    elif c.function.name == 'calculate':
                        result = calculate(**args)
                    else:
                        result = {'error': 'unknown tool'}
                except (ValueError, TypeError) as e:
                    result = {'error': 'invalid tool arguments', 'detail': str(e)}
                messages.append({'role': 'tool', 'tool_call_id': c.id,
                                 'content': json.dumps(result)})
                record['tool_calls'].append({'id': c.id, 'name': c.function.name,
                                             'arguments': c.function.arguments, 'result': result})
            trace.append(record)
            continue
        trace.append(record)
        return {'prediction': _json_answer(msg.content), 'raw_answer': msg.content,
                'usage': totals, 'seconds': round(time.perf_counter() - start, 3),
                'trace': trace, 'strategy': strategy}
    return {'prediction': {'error': 'tool round limit exceeded'}, 'raw_answer': '',
            'usage': totals, 'seconds': round(time.perf_counter() - start, 3),
            'trace': trace, 'strategy': strategy}


def run_strategy(client, question, strategy, model=MODEL, description_variant='normal'):
    if strategy != 'S2':
        return one_run(client, question, strategy, model, description_variant)
    trials = [one_run(client, question, 'S2', model) for _ in range(5)]
    def vote_key(t):
        p = t['prediction']
        return (str(p.get('answer', '')).strip().lower(), str(p.get('value', '')))
    counts = Counter(vote_key(t) for t in trials)
    winning = counts.most_common(1)[0][0]
    selected = next(t for t in trials if vote_key(t) == winning)
    return {'strategy': 'S2', 'prediction': selected['prediction'],
            'votes': [{'answer': a, 'value': v, 'count': n} for (a, v), n in counts.items()],
            'trials': trials,
            'usage': {k: sum(t['usage'][k] for t in trials) for k in ('input_tokens', 'output_tokens', 'total_tokens')},
            'seconds': sum(t['seconds'] for t in trials)}
