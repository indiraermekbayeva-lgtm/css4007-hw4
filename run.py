"""Execute HW4 experiments; do not send gold answers to the model."""
import argparse
import json
import os
from pathlib import Path
from openai import OpenAI
from strategies import run_strategy, MODEL

ROOT = Path(__file__).resolve().parent


def grade(pred, gold):
    try:
        name_ok = str(pred['answer']).strip().casefold() == str(gold['answer']).strip().casefold()
        value_ok = round(float(pred['value']), int(gold['decimals'])) == round(float(gold['value']), int(gold['decimals']))
        return {'answer_correct': name_ok, 'value_correct': value_ok, 'both_correct': name_ok and value_ok}
    except (KeyError, ValueError, TypeError, OverflowError):
        return {'answer_correct': False, 'value_correct': False, 'both_correct': False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=20, help='Number of questions; use 1 for cheap smoke test')
    parser.add_argument('--repeats', type=int, default=2)
    parser.add_argument('--strategies', nargs='+', default=['S1', 'S2', 'S3'], choices=['S1', 'S2', 'S3'])
    parser.add_argument('--model', default=MODEL)
    parser.add_argument('--ablation', action='store_true', help='Five S3 questions with shortened lookup description')
    args = parser.parse_args()
    if not os.getenv('OPENAI_API_KEY'):
        raise SystemExit('Missing OPENAI_API_KEY. Set it securely; never commit it.')
    client = OpenAI()
    questions = json.loads((ROOT / 'questions.json').read_text(encoding='utf-8'))
    output = ROOT / 'outputs'
    output.mkdir(exist_ok=True)
    if args.ablation:
        questions = questions[:5]
        strategies = ['S3']
        repeats = 1
        variant = 'short'
        prefix = 'ablation'
    else:
        questions = questions[:args.limit]
        strategies = args.strategies
        repeats = args.repeats
        variant = 'normal'
        prefix = 'experiment'
    results = []
    for strategy in strategies:
        for repeat in range(1, repeats + 1):
            for q in questions:
                print(f'{strategy} repeat {repeat}: {q["id"]}', flush=True)
                try:
                    outcome = run_strategy(client, q['question'], strategy, args.model, variant)
                    outcome['grading'] = grade(outcome['prediction'], q)
                except Exception as e:
                    outcome = {'prediction': {'error': str(e)}, 'grading': {'both_correct': False},
                               'usage': {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0},
                               'error': str(e)}
                # Gold fields used for grading only; never included in model messages.
                results.append({'id': q['id'], 'question': q['question'], 'strategy': strategy,
                                'repeat': repeat, 'gold': {k: q[k] for k in ('answer', 'value', 'unit', 'decimals')},
                                **outcome})
                (output / f'{prefix}.jsonl').write_text(
                    ''.join(json.dumps(r, ensure_ascii=False, default=str) + '\n' for r in results), encoding='utf-8')
    summary = {}
    for strategy in strategies:
        subset = [r for r in results if r['strategy'] == strategy]
        summary[strategy] = {
            'runs': len(subset),
            'accuracy_both': round(sum(r['grading']['both_correct'] for r in subset) / len(subset), 4) if subset else None,
            'total_input_tokens': sum(r.get('usage', {}).get('input_tokens', 0) for r in subset),
            'total_output_tokens': sum(r.get('usage', {}).get('output_tokens', 0) for r in subset),
            'total_tokens': sum(r.get('usage', {}).get('total_tokens', 0) for r in subset),
            'seconds': round(sum(r.get('seconds', 0) for r in subset), 2)
        }
    (output / f'{prefix}_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
