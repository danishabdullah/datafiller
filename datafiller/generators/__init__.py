from __future__ import print_function, unicode_literals

from datafiller.generators.array import ArrayGenerator
from datafiller.generators.base import CatGenerator, AltGenerator, NULLGenerator, ValueGenerator, \
    TupleGenerator, ReduceGenerator
from datafiller.generators.binary import BoolGenerator, BitGenerator
from datafiller.generators.ean import EANGenerator
from datafiller.generators.file import FileGenerator
from datafiller.generators.location import InetGenerator, MACGenerator
from datafiller.generators.luhn import LuhnGenerator
from datafiller.generators.numeric import FloatGenerator, IntGenerator, CountGenerator
from datafiller.generators.pattern import PatternGenerator, UUIDGenerator
from datafiller.generators.reapeated import RepeatGenerator
from datafiller.generators.temporal import TimestampGenerator, DateGenerator, IntervalGenerator
from datafiller.generators.textual import ConstGenerator, WordGenerator, StringGenerator, CharsGenerator, TextGenerator, \
    BlobGenerator

__author__ = "danishabdullah"

# all user-visible generators
GENERATORS = {
    'cat': CatGenerator, 'alt': AltGenerator, 'timestamp': TimestampGenerator,
    'repeat': RepeatGenerator, 'float': FloatGenerator, 'date': DateGenerator,
    'pattern': PatternGenerator, 'int': IntGenerator, 'bool': BoolGenerator,
    'interval': IntervalGenerator, 'const': ConstGenerator, 'word': WordGenerator,
    'string': StringGenerator, 'chars': CharsGenerator, 'text': TextGenerator,
    'blob': BlobGenerator, 'inet': InetGenerator, 'mac': MACGenerator,
    'ean': EANGenerator, 'luhn': LuhnGenerator, 'count': CountGenerator,
    'file': FileGenerator, 'uuid': UUIDGenerator, 'bit': BitGenerator,
    'array': ArrayGenerator, 'tuple': TupleGenerator, 'isnull': NULLGenerator,
    'reduce': ReduceGenerator, 'value': ValueGenerator
}
