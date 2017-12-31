#!/usr/bin/env python3

import re

def tokenize_match(content):
    match = ""
    i = 1
    while True:
        if content[i] == "}":
            return (content[i+1:], ['match', match])
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
            (msg, new_tokens) = tokenize_match(msg)
            tokens += new_tokens
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


class Filter:
    def __init__(self, group, bound, logic_str):
        self.group = group
        self.bound = bound
        self.logic = parse(tokenize(logic_str))

    def matches(self, item):
        return item.price and item.group.lower() == self.group.lower() \
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
