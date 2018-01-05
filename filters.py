#!/usr/bin/env python3

import re


def _tokenize_until(content, until):
    match = ""
    i = 1
    while True:
        if content[i] == until:
            return (content[i+1:], match)
        match = match + content[i]
        i += 1


def tokenize(content):
    msg = content.strip()
    tokens = []
    while msg:
        if msg[:1] == "(":
            tokens += ['(']
            msg = msg[1:]
        elif msg[:1] == ")":
            tokens += [')']
            msg = msg[1:]
        elif msg[:3] == "and":
            tokens += ['and']
            msg = msg[3:]
        elif msg[:2] == "or":
            tokens += ['or']
            msg = msg[2:]
        elif msg[:1] == "{":
            (msg, match_token) = _tokenize_until(msg, '}')
            tokens += ['match', match_token]
        elif msg[:1] == "[":
            (msg, comp_token) = _tokenize_until(msg, ']')
            tokens += ['comp', comp_token]
        else:
            raise Exception("Tokenization error: Unexpected token '{}'".format(msg[:1]))
        msg = msg.strip()
    return tokens


def _parse_block(tokens):
    if not tokens:
        raise Exception("Parse error: Unexpected end of line")
    if tokens[0] == "(":
        return _parse_items(tokens)
    elif tokens[0] == "and":
        (items, tokens) = _parse_items(tokens[1:])
        tree = filter_and(items)
        return (tree, tokens)
    elif tokens[0] == "or":
        (items, tokens) = _parse_items(tokens[1:])
        tree = filter_or(items)
        return (tree, tokens)
    elif tokens[0] == "match":
        return _parse_match(tokens)
    elif tokens[0] == "comp":
        return _parse_comp(tokens)
    else:
        raise Exception("Parse error: Unexpected token '{}'".format(tokens[0]))


def _parse_items(tokens):
    if not tokens[0] == "(":
        raise Exception("Parse error: Expected '(', received '{}'".format(tokens[0]))
    items = []
    tokens = tokens[1:]
    while not tokens[0] == ")":
        (item, tokens) = _parse_block(tokens)
        items += [item]
    return (items, tokens)


def _parse_match(tokens):
    if not tokens[0] == "match":
        raise Exception("Parse error: Expected 'match', received '{}'".format(tokens[0]))
    return (filter_match(tokens[1]), tokens[2:])


import operator
_ops = {'>': operator.gt, '<': operator.lt, '>=': operator.ge, '<=': operator.le, '==': operator.eq}
def _parse_comp(tokens):
    if not tokens[0] == "comp":
        raise Exception("Parse error: Expected 'comp', received '{}'".format(tokens[0]))
    m = re.match('(>|<|>=|<=|==)(\d+(\.\d+)?)([^0-9]*)', tokens[1])
    if not m:
        raise Exception("Parse error: Could not parse comp string '{}'".format(tokens[1]))
    op = _ops[m.group(1)]
    ## i do this just for the nice formatting
    amt = int(m.group(2)) if m.group(3) else float(m.group(2))
    unit = m.group(4)
    return (filter_comp(op, amt, unit), tokens[2:])


def parse(tokens):
    ## initially assume that all items are wrapped in an and() block
    tokens = ['and', '('] + tokens + [')']
    (tree, tokens) = _parse_block(tokens)
    return tree


class filter_and:
    def __init__(self, items):
        self.items = items

    def eval(self, msg):
        if not self.items:
            return True
        else:
            return all([item.eval(msg) for item in self.items])

    def __repr__(self):
        return "and({})".format(', '.join([str(i) for i in self.items]))


class filter_or:
    def __init__(self, items):
        self.items = items

    def eval(self, msg):
        if not self.items:
            return False
        else:
            return any([item.eval(msg) for item in self.items])

    def __repr__(self):
        return "or({})".format(', '.join([str(i) for i in self.items]))


class filter_match:
    def __init__(self, match_str):
        self.match_str = match_str.replace(' ', '')

    def eval(self, msg):
        return self.match_str in msg

    def __repr__(self):
        return "matches('{}')".format(self.match_str)


class filter_comp:
    def __init__(self, op, amt, unit):
        self.op = op
        self.amt = int(amt)
        self.unit = unit.lower().replace(' ', '')
        ## replace for matching with monitors
        if self.unit == 'in':
            self.unit = '(?:in|\'\'|")'
    
    def eval(self, msg):
        for num in re.findall('(\d+(?:\.\d+)?){}'.format(self.unit), msg):
            num = float(num)
            if self.op(num, self.amt):
                return True
        return False

    def __repr__(self):
        return "{}({}{})".format(self.op.__name__, self.amt, self.unit)

class Filter:
    def __init__(self, group, bound, logic_str):
        self.group = group.lower().replace(' ', '')
        self.bound = bound
        self.logic = parse(tokenize(logic_str))

    def matches(self, item):
        return item.price and self.group in item.group \
            and item.price <= self.bound and self.logic.eval(item.content)

    def __repr__(self):
        return "Filter(group='{}', bound='{}', logic={})".format(self.group, self.bound, self.logic)


def load_filters():
    filters = []
    with open("filters.txt", 'r') as f:
        lines = f.readlines()
        for line in lines:
            m_group = re.search("\[(.+?)\]", line)
            m_bound = re.search("<([0-9\.]+)", line)
            m_logic = re.search("#(.*)$", line)
            if not m_group:
                continue
            group = m_group.group(1)
            bound = float(m_bound.group(1))
            logic = m_logic.group(1)
            f = Filter(group, bound, logic)
            # print(group,"##",bound,"##",logic)
            # print(f.logic)
            filters += [f]
    return filters


def matches(item):
    return any([f.matches(item) for f in filters])


filters = load_filters()
