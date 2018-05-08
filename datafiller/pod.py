from __future__ import print_function, unicode_literals

__author__ = "danishabdullah"

# plain old embedded documentation... Yes, the perl thing;-)
# could use pandoc/markdown, but it seems that pandoc cannot display
# a manual page interactively as pod2usage, and as a haskell script
# it is not installed by default. However, this POD thing breaks pydoc
# without a clear message about the issue...
POD = """

=pod

=head1 NAME

B<{name}> - generate random data from database schema extended with directives

=head1 SYNOPSIS

B<{name}> [--help --man ...] [schema.sql ...] > data.sql

=head1 DESCRIPTION

This script generates random data from a database schema enriched with
simple directives in SQL comments to drive {NGENS} data generators which
cover typical data types and their combination.
Reasonable defaults are provided, especially based on key and type constraints,
so that few directives should be necessary. The minimum setup is to specify the
relative size of tables with directive B<mult> so that data generation can
be scaled.

See the L</TUTORIAL> section below. Also, run with C<--validate=comics> or
C<--validate=library> and look at the output for didactic examples.

=head1 OPTIONS

=over 4

=item C<--debug> or C<-D>

Set debug mode.
Repeat for more.

Default is no debug.

=item C<--drop>

Drop tables before recreating them.
This implies option C<--filter>, otherwise there would be no table to fill.

Default is not to.

=item C<--encoding=enc> or C<-e enc>

Set this encoding for input and output files.

Default is no explicit encoding.

=item C<--filter> or C<-f>, reverse with C<--no-filter>

Work as a filter, i.e. send the schema input script to stdout and then
the generated data.
This is convenient to pipe the result of the script directly for
execution to the database command.

Default is to only ouput generated data.

=item C<--freeze>, reverse with C<--no-freeze>

Whether to use PostgreSQL C<COPY> C<FREEZE> option.

Default is to use it, as it allows better performance.

=item C<--help> or C<-h>

Show basic help.

=item C<--man> or C<-m>

Show full man page based on POD. Yes, the perl thing:-)

=item C<--null RATE> or C<-n RATE>

Probability to generate a null value for nullable attributes.

Default is 0.01, which can be overriden by the B<null> directive at
the schema level, or per-attributes provided B<null> rate.

=item C<--offset OFFSET> or C<-O OFFSET>

Set default offset for integer generators on I<primary keys>.
This is useful to extend the already existing content of a database
for larger tests.

Default is 1, which can be overriden by the B<offset> directive at
the schema level, or per-attribute provided B<offset>.

=item C<--pod COMMAND>

Override pod conversion command used by option C<--man>.

Default is 'pod2usage -verbose 3'.

=item C<--quiet> or C<-q>

Generate less verbose SQL output.

Default is to generate one echo when starting to fill a table.

=item C<--seed SEED> or C<-S SEED>

Seed overall random generation with provided string.

Default uses OS supplied randomness or current time.

=item C<--size SIZE>

Set overall scaling. The size is combined with the B<mult> directive value
on a table to compute the actual number of tuples to generate in each table.

Default is 100, which can be overriden with the B<size> directive at the
schema level.

=item C<--target (postgresql|mysql|csv)> or C<-t ...>

Target database engine.
MySQL support is really experimental.
CSV support is partial.

Default is to target PostgreSQL.

=item C<--test='directives...'>

Run tests for any generator with some directives.
If the directives start with B<!>, show an histogram.
If the directives start with B<->, show results on one-line.
This is convenient for unit testing, or to check what would
be the output of a set of directives.

Examples:
C<--size=100 --test='int size=10 mangle'> would show 100 integers
between 1 and 10 drawn uniformly.
C<--test='!bool rate=0.3'> may show I<False: 69.32%, True: 30.68%>,
stating the rate at which I<True> and I<False> were seen during the test.

Directive B<type> can be used within C<--test=...> to provide the target
SQL type when testing.

=item C<--transaction> or C<-T>

Use a global transaction.

Default is not to.

=item C<--tries=NUM>

How hard to try to satisfy a compound unique constraint before giving up
on a given tuple.

Default is 10.

=item C<--truncate>

Delete table contents before filling.

Default is not to.

=item C<--type=CUSTOM>

Add a custom type. The default generator for this type will rely
on a macro of the same name, if it exists. This option can be repeated
to add more custom types. See also the B<type> directive at the schema level.

=item C<--validate=(unit|internal|comics|library|pgbench)>

Output validation test cases. All but the C<unit> tests can
be processed with C<psql>.

  sh> {name} --validate=internal | psql

This option sets C<--filter> automatically, although it can
be forced back with C<--no-filter>.

Default is to process argument files or standard input.

=item C<--version>, C<-v> or C<-V>

Show script version.

=back

=head1 ARGUMENTS

Files containing SQL schema definitions. Standard input is processed if empty.

=head1 TUTORIAL

This tutorial introduces how to use DataFiller to fill a PostgreSQL database
for testing functionalities and performances.

=head2 DIRECTIVES IN COMMENTS

The starting point of the script to generate test data is the SQL schema
of the database taken from a file. It includes important information that
will be used to generate data: attribute types, uniqueness, not-null-ness,
foreign keys... The idea is to augment the schema with B<directives> in
comments so as to provide additional hints about data generation.

A datafiller.py directive is a special SQL comment recognized by the script, with
a C<df> marker at the beginning. A directive must appear I<after> the object
about which it is applied, either directly after the object declaration,
in which case the object is implicit, or much later, in which case the
object must be explicitely referenced:

  -- this directive sets the default overall size
    -- df: size=10
  -- this directive defines a macro named "fn"
    -- df fn: word=/path/to/file-containing-words
  -- this directive applies to table "Foo"
  CREATE TABLE Foo( -- df: mult=10.0
    -- this directive applies to attribute "fid"
    fid SERIAL -- df: offset=1000
    -- use defined macro, choose "stuff" from the list of words
  , stuff TEXT NOT NULL -- df: use=fn
  );
  -- ... much later
  -- this directive applies to attribute "fid" in table "Foo"
  -- df T=Foo A=fid: null=0.8

=head2 A SIMPLE LIBRARY EXAMPLE

Let us start with a simple example involving a library where
I<readers> I<borrow> I<books>.
Our schema is defined in file C<library.sql> as follows:

{library}

The first and only information you really need to provide is the relative
or absolute size of relations. For scaling, the best way is to specify a
relative size multiplier with the C<mult> directive on each table, which will
be multiplied by the C<size> option to compute the actual size of data to
generate in each table. Let us say we want 100 books in stock per reader,
with 1.5 borrowed books per reader on average:

  CREATE TABLE Book( -- df: mult=100.0
  ...
  CREATE TABLE Borrow( --df: mult=1.5

The default multiplier is 1.0, it does not need to be set on C<Reader>.
Then you can generate a data set with:

  sh> {name} --size=1000 library.sql > library_test_data.sql

Note that I<explicit> constraints are enforced on the generated data,
so that foreign keys in *Borrow* reference existing *Books* and *Readers*.
However the script cannot guess I<implicit> constraints, thus if an attribute
is not declared C<NOT NULL>, then some C<NULL> values I<will> be generated.
If an attribute is not unique, then the generated values will probably
not be unique.

=head2 IMPROVING GENERATED VALUES

In the above generated data, some attributes may not reflect the reality
one would expect from a library. Changing the default with per-attribute
directives will help improve this first result.

First, book titles are all quite short, looking like I<title_number>,
with some collisions. Indeed the default is to generate strings with a
common prefix based on the attribute name and a number drawn uniformly
from the expected number of tuples.
We can change to texts composed of between 1 and 7 English words taken
from a dictionary:

  title TEXT NOT NULL
  -- df English: word=/etc/dictionaries-common/words
  -- df: text=English length=4 lenvar=3

Also, we may have undesirable collisions on the ISBN attribute, because
the default size of the set is the number of tuples in the table. We
can extend the size at the attribute level so as to avoid this issue:

  isbn ISBN13 NOT NULL -- df: size=1000000000

If we now look at readers, the result can also be improved.
First, we can decide to keep the prefix and number form, but make the
statistics more in line with what you can find. Let us draw from 1000
firstnames, most frequent 3%, and 10000 lastnames, most frequent 1%:

  firstname TEXT NOT NULL,
     -- df: sub=power prefix=fn size=1000 rate=0.03
  lastname TEXT NOT NULL,
     -- df: sub=power prefix=ln size=10000 rate=0.01

The default generated dates are a few days around now, which does not make
much sense for our readers' birth dates. Let us set a range of birth dates.

  birth DATE NOT NULL, -- df: start=1923-01-01 end=2010-01-01

Most readers from our library are female: we can adjust the rate
so that 25% of readers are male, instead of the default 50%.

  gender BOOLEAN NOT NULL, -- df: rate=0.25

Phone numbers also have a I<prefix_number> structure, which does not really
look like a phone number. Let us draw a string of 10 digits, and adjust the
nullable rate so that 1% of phone numbers are not known.
We also set the size manually to avoid too many collisions, but we could
have chosen to keep them as is, as some readers do share phone numbers.

  phone TEXT
    -- these directives could be on a single line
    -- df: chars='0-9' length=10 lenvar=0
    -- df: null=0.01 size=1000000

The last table is about currently borrowed books.
The timestamps are around now, we are going to spread them on a period of
50 days, that is 24 * 60 * 50 = 72000 minutes (precision is 60 seconds).

  borrowed TIMESTAMP NOT NULL -- df: size=72000 prec=60

Because of the primary key constraint, the borrowed books are the first ones.
Let us mangle the result so that referenced book numbers are scattered.

  bid INTEGER REFERENCES Book -- df: mangle

Now we can generate improved data for our one thousand readers library,
and fill it directly to our B<library> database:

  sh> {name} --size=1000 --filter library.sql | psql library

Our test database is ready.
If we want more users and books, we only need to adjust the C<size> option.
Let us query our test data:

  -- show firstname distribution
  SELECT firtname, COUNT(*) AS cnt FROM Reader
  GROUP BY firstname ORDER BY cnt DESC LIMIT 3;
    -- fn_1_... | 33
    -- fn_2_... | 15
    -- fn_3_... | 12
  -- compute gender rate
  SELECT AVG(gender::INT) FROM Reader;
    -- 0.246

=head2 DISCUSSION

We could go on improving the generated data so that it is more realistic.
For instance, we could skew the I<borrowed> timestamp so that there are less
old borrowings, or skew the book number so that old books (lower numbers) are
less often borrowed, or choose firtnames and lastnames from actual lists.

When to stop improving is not obvious:
On the one hand, real data may show particular distributions which impact
the application behavior and performance, thus it may be important to reflect
that in the test data.
On the other hand, if nothing is really done about readers, then maybe the
only relevant information is the average length of firstnames and lastnames
because of the storage implications, and that's it.

=head2 ADVANCED FEATURES

Special generators allow to combine or synchronize other generators.

Let us consider an new C<email> attribute for our I<Readers>, for which we
want to generate gmail or yahoo addresses. We can use a B<pattern> generator
for this purpose:

  email TEXT NOT NULL CHECK(email LIKE '%@%')
    -- df: pattern='[a-z]{{3,8}}\.[a-z]{{3,8}}@(gmail|yahoo)\.com'

The pattern sets 3 to 8 lower case characters, followed by a dot, followed
by 3 to 8 characters again, followed by either gmail or yahoo domains.
With this approach, everything is chosen uniformly: letters in first and last
names appear 1/26, their six possible sizes between 3 to 8 are equiprobable,
and each domain is drawn on average by half generated email addresses.

In order to get more control about these distributions, we could rely on
the B<chars> or B<alt> generators which can be skewed or weighted,
as illustrated in the next example.

Let us now consider an ip address for the library network.  We want that
20% comes from librarian subnet '10.1.0.0/16' and 80% from reader subnet
'10.2.0.0/16'. This can be achieved with directive B<alt> which tells to
make a weighted choice between macro-defined generators:

  -- define two macros
  -- df librarian: inet='10.1.0.0/16'
  -- df reader: inet='10.2.0.0/16'
  ip INET NOT NULL
  -- df: alt=reader:8,librarian:2
  -- This would do as well: --df: alt=reader:4,librarian

Let us finally consider a log table for data coming from a proxy, which
stores correlated ethernet and ip addresses, that is ethernet address always
get the same ip addess, and we have about 1000 distinct hosts:

     -- df distinct: int size=1000
  ,  mac MACADDR NOT NULL -- df share=distinct
  ,  ip INET NOT NULL -- df share=distinct inet='10.0.0.0/8'

Because of the B<share> directive, the same C<mac> and C<ip> will be generated
together in a pool of 1000 pairs of addresses.

=head2 TUTORIAL CONCLUSION

There are many more directives to drive data generation, from simple type
oriented generators to advanced combinators. See the documentation and
examples below.

For very application-specific constraints that would not fit any generator,
it is also possible to apply updates to modify the generated data afterwards.

=head1 DIRECTIVES AND DATA GENERATORS

Directives drive the data sizes and the underlying data generators.
They must appear in SQL comments I<after> the object on which they apply,
although possibly on the same line, introduced by S<'-- df: '>.

  CREATE TABLE Stuff(         -- df: mult=2.0
    id SERIAL PRIMARY KEY,    -- df: step=19
    data TEXT UNIQUE NOT NULL -- df: prefix=st length=30 lenvar=3
  );

In the above example, with option C<--size=1000>, 2000 tuples
will be generated I<(2.0*1000)> with B<id> I<1+(i*19)%2000> and
unique text B<data> of length about 30+-3 prefixed with C<st>.
The sequence for B<id> will be restarted at I<2001>.

The default size is the number of tuples of the containing table.
This implies many collisions for a I<uniform> generator.

=head2 DATA GENERATORS

There are {NGENS} data generators which are selected by the attribute type
or possibly directives. Most generators are subject to the B<null>
directive which drives the probability of a C<NULL> value.
There is also a special shared generator.

Generators are triggered by using directives of their names.
If none is specified, a default is chosen based on the attribute type.

=over 4

=item B<alt generator>

This generator aggregates other generators by choosing one.
The list of sub-generators must be specified as a list of comma-separated
weighted datafiller.py macros provided by directive B<alt>, see below.
These generator definition macros must contain an explicit directive
to select the underlying generator.

=item B<array generator>

This generator generates an SQL array from another generator.
The sub-generator is specified as a macro name with the B<array> directive.
It takes into account the B<length>, B<lenvar>, B<lenmin> and
B<lenmax> directives.

=item B<bit generator>

This generator handles BIT and VARBIT data to store sequences of bits.
It takes into account the B<length>, B<lenvar>, B<lenmin> and
B<lenmax> directives.

=item B<blob generator>

This is for blob types, such as PostgreSQL's C<BYTEA>.
It uses an B<int generator> internally to drive its extent.
It takes into account the B<length>, B<lenvar>, B<lenmin> and
B<lenmax> directives.
This generator does not support C<UNIQUE>, but uniqueness is very likely
if the blob B<length> is significant and the B<size> is large.

=item B<bool generator>

This generator is used for the boolean type.
It is subject to the B<rate> directive.

=item B<cat generator>

This generator aggregates other generators by I<concatenating> their textual
output.
The list of sub-generators must be specified as a list of comma-separated
datafiller.py macros provided by a B<cat> directive, see below.

=item B<chars generator>

This alternate generator for text types generates random string of characters.
It is triggered by the B<chars> directive.
In addition to the underlying B<int generator> which allows to select values,
another B<int generator> is used to build words from the provided list
of characters,
The B<cgen> directives is the name of a macro which specifies the
B<int generator> parameters for the random character selection.
It also takes into account the B<length>, B<lenvar>, B<lenmin> and
B<lenmax> directives.
This generator does not support C<UNIQUE>.

=item B<const generator>

This generator provides a constant text value.
It is driven by the B<const> directive.

=item B<count generator>

This generator provides a simple counter.
It takes into account directives B<start>, B<step> and B<format>.

=item B<date generator>

This generator is used for the date type.
It uses an B<int generator> internally to drive its extent.
Its internal working is subject to directives B<start>, B<end> and B<prec>.

=item B<ean generator>

This is for International Article Number (EAN!) generation.
It uses an B<int generator> internally, so the number of distinct numbers
can be adjusted with directive B<size>.
It takes into account the B<length> and B<prefix> directives.
Default is to generate EAN-13 numbers.
This generator does not support C<UNIQUE>, but uniqueness is very likely.

=item B<file generator>

Inline file contents.
The mandatory list of files is specified with directive B<files>.
See also directive B<mode>.

=item B<float generator>

This generator is used for floating point types.
The directive allows to specify the sub-generator to use,
see the B<float> directive below.
Its configuration also relies on directives B<alpha> and B<beta>.
It does not support C<UNIQUE>, but uniqueness is very likely.

=item B<inet generator>

This is for internet ip types, such as PostgreSQL's C<INET> and C<CIDR>.
It uses an B<int generator> internally to drive its extent.
It takes into account the B<network> directive to specify the target network.
Handling IPv6 networks requires module B<netaddr>.

=item B<int generator>

This generator is used directly for integer types, and indirectly
by other generators such as B<text>, B<word> and B<date>.
Its internal working is subject to directives: B<sub>, B<size> (or B<mult>),
B<offset>, B<shift>, B<step>, B<xor> and B<mangle>.

=item B<interval generator>

This generator is used for the time interval type.
It uses the B<int generator> internally to drive its extent.
See also the B<unit> directive.

=item B<isnull generator>

Generates the special NULL value.

=item B<luhn generator>

This is for numbers which use a Luhn's algorithm checksum, such
as bank card numbers.
It uses an B<int generator> internally, so the number of distinct numbers
can be adjusted with directive B<size>.
It takes into account the B<length> and B<prefix> directives.
Default B<length> is 16, default B<prefix> is empty.
This generator does not support C<UNIQUE>, but uniqueness is very likely.

=item B<mac generator>

This is for MAC addresses, such as PostgreSQL's C<MACADDR>.
It uses an B<int generator> internally, so the number of generated addresses
can be adjusted with directive B<size>.

=item B<pattern generator>

This alternative generator for text types generates text based on a regular
expression provided with the B<pattern> directive. It uses internally the
B<alt>, B<cat>, B<repeat>, B<const> and B<chars> generators.

=item B<reduce generator>

This generator applies the reduction operation specified by directive B<op>
to generators specified with B<reduce> as a comma-separated list of macros.

=item B<repeat generator>

This generator aggregates the repetition of another generator.
The repeated generator is specified in a macro with a B<repeat> directive,
and the number of repetitions relies on the B<extent> directive.
It uses an B<int generator> internally to drive the number of repetitions,
so it can be skewed by specifying a subtype with the B<sub> directive.

=item B<string generator>

This generator is used by default for text types.
This is a good generator for filling stuff without much ado.
It takes into account B<prefix>, and the length can be specified with
B<length>, B<lenvar> B<lenmin> and B<lenmax> directives.
The generated text is of length B<length> +- B<lenvar>,
or between B<lenmin> and B<lenmax>.
For C<CHAR(n)> and C<VARCHAR(n)> text types, automatic defaults are set.

=item B<text generator>

This aggregate generator generates aggregates of words drawn from
any other generator specified by a macro in directive B<text>.
It takes into account directives B<separator> for separator (default C< >),
B<prefix> and B<suffix> (default empty).
It also takes into account the B<length>, B<lenvar>, B<lenmin> and
B<lenmax> directives which handle the number of words to generate.
This generator does not support C<UNIQUE>, but uniqueness is very likely
for a text with a significant length drawn from a dictionary.

=item B<timestamp generator>

This generator is used for the timestamp type.
It is similar to the date generator but at a finer granularity.
The B<tz> directive allows to specify the target timezone.

=item B<tuple generator>

This aggregate generator generates composite types.
The list of sub-generators must be specified with B<tuple>
as a list of comma-seperated macros.

=item B<uuid generator>

This generator is used for the UUID type.
It is really a B<pattern> generator with a predefined pattern.

=item B<value generator>

This generator uses per-tuple values from another generator specified as a
macro name in the B<value> directive. If the same B<value> is specified more
than once in a tuple, the exact same value is generated.

=item B<word generator>

This alternate generator for text types is triggered by the B<word> directive.
It uses B<int generator> to select words from a list or a file.
This generator handles C<UNIQUE> if enough words are provided.

=back

=head2 GLOBAL DIRECTIVES

A directive macro can be defined and then used later by inserting its name
between the introductory C<df> and the C<:>. The specified directives are
stored in the macro and can be reused later.
For instance, macros B<words>, B<mangle> B<cfr> and B<cen> can be defined as:

  --df words: word=/etc/dictionaries-common/words sub=power alpha=1.7
  --df mix: offset=10000 step=17 shift=3
  --df cfr: sub=scale alpha=6.7
  --df cen: sub=scale alpha=5.9

Then they can be used in any datafiller.py directive with B<use=...>:

  --df: use=words use=mix
  --df: use=mix

Or possibly for chars generators with B<cgen=...>:

  --df: cgen=cfr chars='esaitnru...'

There are four predefined macros:
B<cfr> and B<cen> define skewed integer generators with the above parameters.
B<french>, B<english> define chars generators which tries to mimic the
character frequency of these languages.

The B<size>, B<offset>, B<null>, B<seed> and directives
can be defined at the schema level to override from the SQL script
the default size multiplier, primary key offset, null rate or seed.
However, they are ignored if the corresponding options are set.

The B<type> directive at the schema level allows to add custom types,
similarly the C<--type> option above.

=head2 TABLE DIRECTIVES

=over 4

=item B<mult=float>

Size multiplier for scaling, that is computing the number of tuples to
generate.
This directive is exclusive from B<size>.

=item B<nogen>

Do not generate data for this table.

=item B<null>

Set defaut B<null> rate for this table.

=item B<size=int>

Use this size, so there is no scaling with the C<--size> option
and B<mult> directive.
This directive is exclusive from B<mult>.

=item B<skip=float>

Skip (that is generate but do not insert) some tuples with this probability.
Useful to create some holes in data. Tables with a non-zero B<skip> cannot be
referenced.

=back

=head2 ATTRIBUTE DIRECTIVES

A specific generator can be specified by using its name in the directives,
otherwise a default is provided based on the attribute SQL type.
Possible generators are: {GLIST}.
See also the B<sub> directive to select a sub-generator to control skewness.

=over 4

=item B<alt=some:2,weighted,macros:2>

List of macros, possibly weighted (default weight is 1) defining the generators
to be used by an B<alt> generator.
These macros must include an explicit directive to select a generator.

=item B<array=macro>

Name of the macro defining an array built upon this generator for
the B<array> generator.
The macro must include an explicit directive to select a generator.

=item B<cat=list,of,macros>

List of macros defining the generators to be used by a B<cat> generator.
These macros must include an explicit directive to select a generator.

=item B<chars='0123456789A-Z\\n' cgen=macro>

The B<chars> directive triggers the B<chars generator> described above.
Directive B<chars> provides a list of characters which are used to build words,
possibly including character intervals with '-'. A leading '-' in the list
means the dash character as is.
Characters can be escaped in octal (e.g. C<\\041> for C<!>) or
in hexadecimal (e.g. C<\\x3D> for C<=>).
Unicode escapes are also supported: eg C<\\u20ac> for the Euro symbol
and C<\\U0001D11E> for the G-clef.
Also special escaped characters are: null C<\\0> (ASCII 0), bell C<\\a> (7),
backspace C<\\b> (8), formfeed C<\\f> (12), newline C<\\n> (10),
carriage return C<\\r> (13), tab C<\\t> (9) and vertical tab C<\\v> (11).
The macro name specified in directive B<cgen> is used to setup the character
selection random generator.

For exemple:

  ...
  -- df skewed: sub=power rate=0.3
  , stuff TEXT -- df: chars='a-f' sub=uniform size=23 cgen=skewed

The text is chosen uniformly in a list of 23 words, each word being
built from characters 'abcdef' with the I<skewed> generator described
in the corresponding macro definition on the line above.

=item B<const=str>

Specify the constant text to generate for the B<const> generator.
The constant text can contains the escaped characters described
with the B<chars> directive above.

=item B<extent=int> or B<extent=int-int>

Specify the extent of the repetition for the I<repeat> generator.
Default is 1, that is not to repeat.

=item B<files=str>

Path-separated patterns for the list for files used by the B<file> generator.
For instance to specify image files in the C<./img> UN*X subdirectory:

  files='./img/*.png:./img/*.jpg:./img/*.gif'

=item B<float=str>

The random sub-generators for floats are those provided by Python's C<random>:

=over 4

=item B<beta>

Beta distribution, B<alpha> and B<beta> must be >0.

=item B<exp>

Exponential distribution with mean 1.0 / B<alpha>

=item B<gamma>

Gamma distribution, B<alpha> and B<beta> must be >0.

=item B<gauss>

Gaussian distribution with mean B<alpha> and stdev B<beta>.

=item B<log>

Log normal distribution, see B<normal>.

=item B<norm>

Normal distribution with mean B<alpha> and stdev B<beta>.

=item B<pareto>

Pareto distribution with shape B<alpha>.

=item B<uniform>

Uniform distribution between B<alpha> and B<beta>.
This is the default distribution.

=item B<vonmises>

Circular data distribution, with mean angle B<alpha> in radians
and concentration B<beta>.

=item B<weibull>

Weibull distribution with scale B<alpha> and shape B<beta>.

=back

=item B<format=str>

Format output for the B<count> generator.
Default is C<d>.
For instance, setting C<08X> displays the counter as 0-padded 8-digits
uppercase hexadecimal.

=item B<inet=str>

Use to specify in which IPv4 or IPv6 network to generate addresses.
For instance, B<inet=10.2.14.0/24> chooses ip addresses between
C<10.2.14.1> and C<10.2.14.254>, that is network and broadcast addresses
are not generated.
Similarily, B<inet=fe80::/112> chooses addresses between
C<fe80::1> and C<fe80::ffff>.
The default subnet limit is B<24> for IPv4 and B<64> for IPv6.
A leading C<,> adds the network address,
a leading C<.> adds the broadcast address,
and a leading C<;> adds both, thus B<inet=';10.2.14.0/24'> chooses
ip addresses between C<10.2.14.0> and C<10.2.14.255>.

=item B<length=int lenvar=int lenmin=int lenmax=int>

Specify length either as length and variation or length bounds, for
generated characters of string data, number of words of text data
or blob.

=item B<mangle>

Whether to automatically choose random B<shift>, B<step> and B<xor> for
an B<int> generator.

=item B<mode=str>

Mode for handling files for the B<file> generator. The value is either
C<blob> for binaries or C<text> for text file in the current encoding.
Default is to use the binary format, as it is safer to do so.

=item B<mult=float>

Use this multiplier to compute the generator B<size>.
This directive is exclusive from B<size>.

=item B<nogen>

Do not generate data for this attribute, so it will get its default value.

=item B<null=float>

Probability of generating a null value for this attribute.
This applies to all generators.

=item B<offset=int shift=int step=int>

Various parameters for generated integers.
The generated integer is B<offset+(shift+step*i)%size>.
B<step> must not be a divider of B<size>, it is ignored and replaced
with 1 if so.

Defaults: offset is 1, shift is 0, step is 1.

=item B<op=(+|*|min|max|cat)>

Reduction operation for B<reduce> generator.

=item B<pattern=str>

Provide the regular expression for the B<pattern> generator.

They can involve character sequences like C<calvin>,
character escape sequences (octal, hexadecimal, unicode, special) as
in directive B<chars> above,
character classes like C<[a-z]> and C<[^a-z]> (exclusion),
character classes shortcuts like C<.> C<\\d> C<\\h> C<\\H> C<\\s> and C<\\w>
which stand for C<[{DOT}]> C<[0-9]> C<[0-9a-f]> C<[0-9A-F]>
C<[ \\f\\n\\r\\t\\v]> and C<[0-9a-zA-Z_]> respectively,
as well as POSIX character classes within C<[:...:]>,
for instance C<[:alnum:]> for C<[0-9A-Za-z]> or C<[:upper:]> for C<[A-Z]>.

Alternations are specified with C<|>, for instance C<(hello|world)>.
Repetitions can be specified after an object with C<{{3,8}}>,
which stands for repeat between 3 and 8 times.
The question mark C<?> is a shortcut for C<{{0,1}}>,
the star sign C<*> for C<{{0,8}}> and the plus sign C<+> for C<{{1,8}}>.

For instance:

  stuff TEXT NOT NULL -- df: pattern='[a-z]{{3,5}} ?(!!|\\.{{3}}).*'

means 3 to 5 lower case letters, maybe followed by a space, followed by
either 2 bangs or 3 dots, and ending with any non special character.

The special C<[:GEN ...:]> syntax allow to embedded a generator within
the generated pattern, possibly including specific directives. For
instance the following would generate unique email addresses because
of the embedded counter:

  email TEXT UNIQUE NOT NULL
    -- df: pattern='\w+\.[:count format=X:]@somewhere\.org'

=item B<prefix=str>

Prefix for B<string> B<ean> B<luhn> and B<text> generators.

=item B<rate=float>

For the bool generator, rate of generating I<True> vs I<False>.
Must be in [0, 1]. Default is I<0.5>.

For the int generator, rate of generating value 0 for generators
B<power> and B<scale>.

=item B<repeat=macro>

Macro which defines the generator to repeat for the repeat generator.
See also the B<extent> directive.

=item B<seed=str>

Set default global seed from the schema level.
This can be overriden by option C<--seed>.
Default is to used the default random generator seed, usually
relying on OS supplied randomness or the current time.

=item B<separator=str>

Word separator for B<text> generator. Default is C< > (space).

=item B<share=macro>

Specify the name of a macro which defines an int generator used for
synchronizing other generators. If several generators B<share> the
same macro, their values within a tuple are correlated between tuples.

=item B<size=int>

Number of underlying values to generate or draw from, depending on the
generator. For keys (primary, foreign, unique) , this is necessarily the
corresponding number of tuples.
This directive is exclusive from B<mult>.

=item B<start=date/time> , B<end=date/time>, B<prec=int>

For the B<date> and B<timestamp> generators,
issue from B<start> up to B<end> at precision B<prec>.
Precision is in days for dates and seconds for timestamp.
Default is to set B<end> to current date/time and B<prec> to
1 day for dates et 60 seconds for timestamps.
If both B<start> and B<end> are specified, the underlying size is
adjusted.

For example, to draw from about 100 years of dates ending on
January 19, 2038:

  -- df: end=2038-01-19 size=36525

=item B<sub=SUGENERATOR>

For integer generators, use this underlying sub-type generator.

The integer sub-types also applies to all generators which inherit from the
B<int> generator, namely B<blob> B<date> B<ean> B<file> B<inet> B<interval>
B<luhn> B<mac> B<string> B<text> B<timestamp> B<repeat> and B<word>.

The sub-generators for integers are:

=over 4

=item B<serial>

This is really a counter which generates distinct integers,
depending on B<offset>, B<shift>, B<step> and B<xor>.

=item B<uniform>

Generates uniform random number integers between B<offset> and B<offset+size-1>.
This is the default.

=item B<serand>

Generate integers based on B<serial> up to B<size>, then use B<uniform>.
Useful to fill foreign keys.

=item B<power> with parameter B<alpha> or B<rate>

Use probability to this B<alpha> power.
When B<rate> is specified, compute alpha so that value 0 is drawn
at the specified rate.
Uniform is similar to B<power> with B<alpha=1.0>, or I<B<rate>=1.0/size>
The higher B<alpha>, the more skewed towards I<0>.

Example distribution with C<--test='!int sub=power rate=0.3 size=10'>:

  value     0   1   2   3   4   5   6   7   8   9
  percent  30  13  10   9   8   7   6   6   5   5

=item B<scale> with parameter B<alpha> or B<rate>

Another form of skewing. The probability of increasing values drawn
is less steep at the beginning compared to B<power>, thus the probability
of values at the end is lower.

Example distribution with C<--test='!int sub=scale rate=0.3 size=10'>:

  value     0   1   2   3   4   5   6   7   8   9
  percent  30  19  12   9   7   6   5   4   3   2

=back

=item B<suffix=str>

Suffix for B<text> generator. Default is empty.

=item B<text=macro>

Macro which defines the word provided generator for the B<text> generator.

=item B<type=str>

At the schema level, add a custom type which will be recognized as such
by the schema parser.
At the attribute level, use the generator for this type.

=item B<unit=str>

The B<unit> directive specifies the unit of the generated intervals.
Possible values include B<s m h d mon y>. Default is B<s>, i.e. seconds.

=item B<word=file> or B<word=:list,of,words>

The B<word> directive triggers the B<word generator> described above,
or is used as a source for words by the B<text generator>.
Use provided word list or lines of file to generate data.
The default B<size> is the size of the word list.

If the file contents is ordered by word frequency, and the int generator is
skewed (see B<sub>), the first words can be made to occur more frequently.

=item B<xor=int>

The B<xor> directive adds a non-linear xor stage for the B<int> generator.

=back

=head1 EXAMPLES

The first example is taken from B<pgbench>.
The second example is a didactic schema to illustrate directives.
See also the B<library> example in the tutorial above.
As these schemas are embedded into this script, they can be invoked
directly with the C<--test> option:

  sh> {name} --test=pgbench -T --size=10 | psql pgbench
  sh> {name} --test=comics -T --size=10 | psql comics
  sh> {name} --test=library -T --size=1000 | psql library

=head2 PGBENCH SCHEMA

This schema is taken from the TCP-B benchmark.
Each B<Branch> has B<Tellers> and B<Accounts> attached to it.
The B<History> records operations performed when the benchmark is run.

{pgbench}

The integer I<*balance> figures are generated with a skewed generator
defined in macro B<regress>. The negative B<offset> setting on I<abalance>
will help generate negative values, and the I<regress> skewed generator
will make small values more likely.

If this is put in a C<tpc-b.sql> file, then working test data can be
generated and loaded with:

  sh> {name} -f -T --size=10 tpc-b.sql | psql bench

=head2 COMICS SCHEMA

This schema models B<Comics> books written in a B<Language> and
published by a B<Publisher>. Each book can have several B<Author>s
through B<Written>. The B<Inventory> tells on which shelf books are
stored. Some of the books may be missing and a few may be available
twice or more.

{comics}

=head1 WARNINGS, BUGS, FEATURES AND GRUMBLING

All software has bug, this is a software, hence it has bugs.

If you find one, please sent a report, or even better a patch that fixes it!

BEWARE, you may loose your hairs or your friends by using this script.
Do not use this script on a production database and without dumping
your data somewhere safe beforehand.

There is no SQL parser, table and attributes are analysed with
optimistic regular expressions.

Foreign keys cannot reference compound keys.
That is a good thing, because you should not have compound foreign keys.

Handling of quoted identifiers is partial and may not work at all.

Beware that unique constraint checks for big data generation may require
a lot of memory.

The script works more or less with Python versions 2.6, 2.7, 3.2, 3.3 and 3.4.
However Python compatibility between major or even minor versions is not the
language's I<forte>. The script tries to remain agnostic with respect to
this issue at the price of some hacks. Sometimes it fails. Complain to
Python's developers who do not care about script stability, and in some
way do not respect other people work. See discussion in PEP387, which
in my opinion is not always implemented.

Python is quite paradoxical, as it can achieve I<forward> compatibility
(C<from __future__ import ...>) but often fails miserably at I<backward>
compatibility.  Guido, this is the other way around!  The useful feature
is to make newer versions handle older scripts.

=head1 LICENSE

=for html
<img src="https://www.gnu.org/graphics/gplv3-127x51.png"
alt="GNU GPLv3" align="right" />

Copyright 2013-{year} Fabien Coelho <fabien at coelho dot net>.

This is free software, both inexpensive and with sources.

The GNU General Public License v3 applies, see
L<http://www.gnu.org/copyleft/gpl.html> for details.

The summary is: you get as much as you paid for, and I am not responsible
for anything.

If you are happy with this software, feel free to send me a postcard saying so!
See my web page for current address L<http://www.coelho.net/>.

If you have ideas or patches to improve this script, send them to me!

=head1 DOWNLOAD

This is F<{name}> version {version}.

Latest version and online documentation should be available from
L<http://www.coelho.net/datafiller.py.html>.

Download script: L<https://www.cri.ensmp.fr/people/coelho/datafiller.py>.

=head1 VERSIONS

History of versions:

=over 4

=item B<version {version}>

In development.

Make C<--drop> option to cascade with PostgreSQL.
Add C<--freeze> and C<--no-freeze> options to trigger PostgreSQL COPY FREEZE option.
Add license information in generated output.
Add some support to generate CSV.
Improved documentation and comments.

=item B<version 2.0.0 (r792 on 2014-03-23)>

=over 4

=item New generators

Add regular expression B<pattern> generator.
Add B<luhn> generator for data which use Luhn's algorithm checksum,
such as bank card numbers.
Add B<ean> generator for supporting B<EAN13>, B<ISBN13>, B<ISSN13>, B<ISMN13>,
B<UPC>, B<ISBN>, B<ISSN> and B<ISMN> types.
Add B<file> generator to inline file contents.
Add B<uuid> generator for Universally Unique IDentifiers.
Add B<bit> generator for BIT and VARBIT types.
Add aggregate generators B<alt>, B<array>, B<cat>, B<reduce>, B<repeat>
and B<tuple>.
Add simple B<isnull>, B<const> and B<count> generators.
Add special B<share> generator synchronizer, which allow to generate
correlated values within a tuple. Add special B<value> generator which
allow to generate the exact same value within a tuple.

=item Changes

Simplify and homogenize per-attribute generator selection, and possibly
its subtype for B<int> and B<float>.
Remove B<nomangle> directive.
Remove B<mangle> directive from table and schema levels.
Remove B<--mangle> option.
Improve B<chars> directive to support character intervals with '-'
and various escape characters (octal, hexadecimal, unicode...).
Use B<--test=...> for unit testing and B<--validate=...> for the
validation test cases.
These changes are incompatible with prior versions and may require modifying
some directives in existing schemas or scripts.

=item Enhancements

Add a non-linear B<xor> stage to the B<int> generator.
Integer mangling now relies on more and larger primes.
Check that directives B<size> and B<mult> are exclusive.
Add the B<type> directive at the schema level.
Improve B<inet> generator to support IPv6 and not to generate
by default network and broadcast addresses in a network;
adding leading characters C<,.;> to the network allows to change this behavior.
Add B<lenmin> and B<lenmax> directives to specify a length.
Be more consistent about seeding to have deterministic results for some tests.

=item Options

Add C<--quiet>, C<--encoding> and C<--type> options.
Make C<--test=...> work for all actual data generators.
Make C<--validate=...> handle all validation cases.
Add internal self-test capabilities.

=item Bug fixes

Check directives consistency.
Do ignore commented out directives, as they should be.
Generate escaped strings where appropriate for PostgreSQL.
Handle size better in generators derived from B<int> generator.
Make UTF-8 and other encodings work with both Python 2 and 3.
Make it work with Python 2.6 and 3.2.

=item Documentation

Improved documentation and examples, including a new L</ADVANCED FEATURES>
Section in the L</TUTORIAL>.

=back

=item B<version 1.1.5 (r360 on 2013-12-03)>

Improved user and code documentations.
Improved validation.
Add C<--no-filter> option for some tests.
Add some support for INET, CIDR and MACADDR types.

=item B<version 1.1.4 (r326 on 2013-11-30)>

Improved documentation, in particular add a L</TUTORIAL> section and
reorder some other sections.
Add some C<pydoc> in the code.
Memoize enum regular expression.
Raise an error if no generator can be created for an attribute,
instead of silently ignoring it.
Fix a bug which could generate primary key violations when handling
some unique constraints.

=item B<version 1.1.3 (r288 on 2013-11-29)>

Improved documentation, including a new L</KEYWORDS> section.
Check consistency of parameters in B<float generator>.
Add some partial support for C<ALTER TABLE>.
Multiple C<--debug> increases verbosity, especially in the parser stage.
Support settings directives out of declarations.
Better support of PostgreSQL integer types.
Add separate L</VERSIONS> section.
One fix for python 3.3...

=item B<version 1.1.2 (r268 on 2013-06-30)>

Improved and simplified code, better comments and validation.
Various hacks for python 2 & 3 compatibility.
Make validations stop on errors.
Check that B<lenvar> is less than B<length>.
Fixes for B<length> and B<lenvar> overriding in B<string generator>.

=item B<version 1.1.1 (r250 on 2013-06-29)>

Minor fix to the documentation.

=item B<version 1.1.0 (r248 on 2013-06-29)>

Improved documentation, code and comments.
Add C<--test> option for demonstration and checks,
including an embedded validation.
Add C<--validate> option as a shortcut for script validation.
Add B<seed>, B<skip>, B<mangle> and B<nomangle> directives.
Add B<null> directive on tables.
Add B<nogen> and B<type> directives on attributes.
Accept size 0.
Change B<alpha> behavior under B<float sub=scale> so that the higher B<alpha>,
the more skewed towards 0.
Add alternative simpler B<rate> specification for B<scale> and B<power>
integer generators.
Deduce B<size> when both B<start> and B<end> are specified for the
date and timestamp generators.
Add B<tz> directive for the timestamp generator.
Add float, interval and blob generators.
Add some support for user-defined enum types.
Add C<--tries> option to control the effort to satisfy C<UNIQUE> constraints.
Add support for non integer foreign keys.
Remove B<square> and B<cube> integer generators.
Change macro definition syntax so as to be more intuitive.
Add C<-V> option for short version.
Some bug fixes.

=item B<version 1.0.0 (r128 on 2013-06-16)>

Initial distribution.

=back

=head1 KEYWORDS

Automatically populate, fill PostgreSQL database with test data.
Generate test data with a data generation tool (data generator) for PostgreSQL.
Import test data into PostgreSQL.

=head1 SEE ALSO

Relational data generation tools are often GUI or even Web applications,
possibly commercial. I did not find a simple filter-oriented tool driven
by directives, and I wanted to do something useful to play with python.

=over 4

=item L<http://en.wikipedia.org/wiki/Test_data_generation>

=item L<http://generatedata.com/> PHP/MySQL

=item L<https://github.com/francolaiuppa/datafiller.py> unrelated PHP/* project.

=item L<http://www.databasetestdata.com/> generate one table

=item L<http://www.mobilefish.com/services/random_test_data_generator/random_test_data_generator.php>

=item L<http://www.sqledit.com/dg/> Win GUI/MS SQL Server, Oracle, DB2

=item L<http://sourceforge.net/projects/spawner/> Pascal, GUI for MySQL

=item L<http://sourceforge.net/projects/dbmonster/> 2005 - Java from XML
for PostgreSQL, MySQL, Oracle

=item L<http://sourceforge.net/projects/datagenerator/> 2006, alpha in Pascal, Win GUI

=item L<http://sourceforge.net/projects/dgmaster/> 2009, Java, GUI

=item L<http://sourceforge.net/projects/freshtrash/> 2007, Java

=item L<http://www.gsapps.com/products/datagenerator/> GUI/...

=item L<http://rubyforge.org/projects/datagen>

=item L<http://msdn.microsoft.com/en-us/library/dd193262%28v=vs.100%29.asp>

=item L<http://stackoverflow.com/questions/3371503/sql-populate-table-with-random-data>

=item L<http://databene.org/databene-benerator>

=item L<http://www.daansystems.com/datagen/> GUI over ODBC

=item Perl (Data::Faker Data::Random), Ruby (Faker ffaker), Python random

=back

=cut

"""
