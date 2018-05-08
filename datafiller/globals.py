from __future__ import print_function, unicode_literals

import re

from datafiller.models import Model
from datafiller.utils import getParams

__author__ = "danishabdullah"

# global tuple counter
tuple_count = 0
generator_count = 0

# macros: { 'name':{...} }
df_macro = {}
# some example predefined macros
df_macro['cfr'] = getParams("gen=int:scale rate=0.17")
df_macro['french'] = getParams("chars='esaitnrulodcpmvqfbghjxyzwk' cgen=cfr")
df_macro['cen'] = getParams("gen=int:scale rate=0.15")
df_macro['english'] = getParams("chars='etaonrishdlfcmugypwbvkjxqz' cgen=cen")

# list of tables in occurrence order, for regeneration
tables = []
all_tables = {}

# parser status
current_table = None
current_attribute = None
current_enum = None
dfstuff = None
att_number = 0

# enums
all_enums = {}
re_enums = ''

# custom types management
re_types = ''
column_type = None

# schema stores global parameters
schema = Model('df')

re_quoted = re.compile(r"[^']*'(([^']|'')*)'(.*)")
