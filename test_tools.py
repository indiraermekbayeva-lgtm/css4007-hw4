import pytest
from tools import lookup, calculate

@pytest.mark.parametrize('expression,expected', [
    ('10+5', 15), ('20-8', 12), ('6*7', 42), ('20/4', 5), ('(3+4)*2', 14), ('-5+8', 3)
])
def test_calculate_valid(expression, expected):
    assert calculate(expression)['result'] == expected

@pytest.mark.parametrize('expression', [
    '10/0', "__import__('os').system('echo hi')", '(1).__class__', '9**9**9',
    'x+1', '1e309', '', '1+' 
])
def test_calculate_reject(expression):
    assert 'error' in calculate(expression)

@pytest.mark.parametrize('district,field,expected', [
    ('Brightwater','population',44675), ('Brightwater','area',921.4),
    ('Millbrook','population',37203), ('Lindenmoor','water',2151.4),
    ('Ossbridge','2020 population',48317), ('Coldharbour','founded',1845),
    ('Ashgrove','schools',24), ('Tarnvale','budget',12960.3),
    ('Redfen','roads',244.6), ('Kelmarsh','pupils',3268),
])
def test_lookup_valid(district, field, expected):
    assert lookup(district, field)['value'] == pytest.approx(expected)

def test_correction_source():
    assert lookup('Brightwater','area')['source'] == 'NR-16'

def test_archived_not_used():
    assert lookup('Tarnvale','population')['value'] == 71388

@pytest.mark.parametrize('district,field', [('Unknown','area'), ('Brightwater','unknown'), (123,'area'), ('','area')])
def test_lookup_reject(district,field):
    assert 'error' in lookup(district,field)
def test_calculate_required_number():
    assert calculate('48317 * 1.0947')['result'] == pytest.approx(52892.7299)


def test_similar_district_names():
    assert lookup('Ossbridge', 'population')['value'] == 52904
    assert lookup('Ossford', 'population')['value'] == 30982


def test_misspelled_district():
    assert 'error' in lookup('Ossbrdge', 'population')
