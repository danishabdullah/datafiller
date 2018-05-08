from __future__ import print_function, unicode_literals

from datafiller.generators import GENERATORS, IntGenerator
from datafiller.globals import df_macro
from datafiller.scripts.cli import db, opts

__author__ = "danishabdullah"
__all__ = ('strDict', 'findGenerator', 'findGeneratorType', 'createGenerator', 'macroGenerator')


def strDict(d):
    return '{' + \
           ', '.join("{0!r}: {1!r}".format(k, d[k]) for k in sorted(d)) + '}'


def findGenerator(obj, params):
    """Get generator from parameters."""
    found = None
    for k in sorted(params):
        if k in sorted(GENERATORS):
            assert not found, \
                "{0}: multiple generators '{1}' and '{2}'".format(obj, found, k)
            found = k
    return found


def findGeneratorType(type):
    """Get generator based on SQL type"""
    return \
        'array' if db.arrayType(type) else \
            'int' if db.intType(type) else \
                'string' if db.textType(type) else \
                    'bool' if db.boolType(type) else \
                        'date' if db.dateType(type) else \
                            'timestamp' if db.timestampType(type) else \
                                'interval' if db.intervalType(type) else \
                                    'float' if db.floatType(type) else \
                                        'blob' if db.blobType(type) else \
                                            'inet' if db.inetType(type) else \
                                                'mac' if db.macAddrType(type) else \
                                                    'ean' if db.eanType(type) else \
                                                        'uuid' if db.uuidType(type) else \
                                                            'bit' if db.bitType(type) else \
                                                                None


def createGenerator(a, t, params=None, msg=None):
    """Create a generator from specified type.

    - Attribute a: target attribute, may be None
    - str t: name of generator, may be None
    - {} p: additional parameters, may be None
    """
    if params == None: params = a.params
    if not t:
        t = findGenerator(msg, params)
    if not t and 'type' in params:
        t = findGeneratorType(params['type'])
    assert t, "no generator in {0}".format(msg if msg else a)
    assert t in GENERATORS, \
        "unexpected generator '{0}' in {1}".format(t, msg if msg else a)
    gen = GENERATORS[t](a, params)
    # check that all directives have been used
    gen.params.pop(t, None)
    gen.params.pop('type', None)
    assert not gen.params, \
        "unexpected '{0}' directives: {1}".format(t, strDict(gen.params))
    return gen


def macroGenerator(name, att=None):
    assert name in df_macro, \
        "{0}: '{1}' must be a macro".format(att if att else 'Macro', name)
    gen = createGenerator(att, None, params=df_macro[name], msg=name)
    if isinstance(gen, IntGenerator) and gen.size == None:  # ???
        gen.setSize(opts.size if opts.size else 1000)  # ???
    return gen
