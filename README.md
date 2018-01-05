# PC Deal Miner

Tool that mines and filters PC part deals from
[/r/buildapcsales](https://reddit.com/r/buildapcsales). Built
primarily as part of a tool that can quickly inform me of ongoing PC
part deals. I don't want to be flooded with notifications, so this
also allows filtering out deals for products of interest. Examples 
are included in the [filters.txt](filters.txt) file and described
in detail below.

## Setup

You will need to write a `filters.txt` and `secrets.py` file for this
to work.

### `filters.txt`

Simple CSV text file where each line specifies a particular filter. An
item (in a Reddit post) will be emailed if it matches at least one
filter. Each line is formatted as follows:

    [product-type] ## <[maximum-cost] ## [additional-filters]

`[product-type]` species the desired part that is generally included
at the beginning of each post -- for example, `[cpu]` would match
posts containing `[CPU]` initially and so on.

`[maximum-cost]` specifies the maximum cost you would like to filter
for. Note that the number checked is the first number with the format
`$[price]`, so this does misses the uncommon incorrectly-formatted
post.

`[additiona-filters]` are applied to the title and any meta-data
included in the deal URL. This is a boolean expression with the
following syntax:

| Command | Description |
| ------- | ----------- |
| `{<str>}` | Match filters. Checks if `<str>` is contained in the description. |
| `[<op><amount><unit>]` | Comparison filter. Compares any numeric amount with `<unit>` proceeding it with `<op>` to `<amount>`. `<op>` can be `<`, `>`, `<=`, `>=` or `==`. |
| `and(<filters>)` | Conjunction filter. Combines multiple filters together, returning `True` iff all sub-filters return `True`. |
| `or(<filters>)` | Disjunction filter. Returns `True` if any of the sub-filters return `True`. |

If multiple expressions are provided at the top level without an
`and()` or `or()` surrounding them, it is assumed they are conjunctive
(that is, `and()` is added around all filters). These filters apply
recursively, so you can have nested `and()` or `or()` operators.

Some notes: If you want to check for monitor lengths, use the unit
`in`. This checks for as `"` or `''` as well. You can also use regex
for the unit, as long as there are no capture groups.

### secrets.py

A basic Python file that specifies some important details to get the
script working. The current format is:

    #!/usr/bin/env python3
    
    CLIENT_ID = ...
    CLIENT_SECRET = ...
    
    SMTP_USER = ...
    SMTP_PASS = ...
    SMTP_FROM = ...
    SMTP_SEND_TO = ...

where `CLIENT_ID`, `CLIENT_SECRET` and the OAuth ID and secret for
Reddit's API, and the `SMTP` variables are used to send emails to
the `SMTP_SEND_TO` address.
