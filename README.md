# CLO (Command-Line Odoo)

[![Build Status][build_status_badge]][build_status_link]
[![Coverage][coverage_badge]][coverage_link]
[![PyPI version][pypi_badge]][pypi_link]

Perform API operations on Odoo instances via the command-line.

## Contents

* [Installation](#installation)
* [Usage](#usage)
  * [Globals](#globals)
    * [Options](#options)
    * [Requisites](#requisites)
  * [Actions](#actions)
    * [Search](#search)
    * [Count](#count)
    * [Read](#read)
    * [Find](#find)
    * [Create](#create)
    * [Write](#write)
    * [Delete](#delete)
    * [Fields](#fields)
    * [Explain](#explain)
  * [Concepts](#concepts)
* [See Also](#see-also)

## Installation

```sh
pip3 install clo
```

## Usage

```sh
clo [OPTIONS] ACTION ...
```

### Globals

The following parameters apply to any [Action](#actions).

#### Options

| Flag(s) | Argument | Required | Description                                                                         . | Default |
| :--- | :--: | :--: | :--- | :--- |
| `‑‑model`<br>`‑m` | `MODEL` | NO | The Odoo model to perform an action on. Run `clo explain models [-v]` to list                             available options. | `"res.users"` |
| `‑‑env` | `FILE` | NO | Path to a `.clorc` file. See [Requisites](#requisites) below for details. | `".clorc"` |
| `‑‑inst`<br>`‑‑instance` | `URL` | NO | The address of the Odoo instance. See [Requisites](#requisites) below for details. |  |
| `‑‑db`<br>`‑‑database` | `NAME` | NO | The application database to perform operations on. See [Requisites](#requisites) below                             for details. |  |
| `‑‑user` | `NAME` | NO | The user to perform operations as. See [Requisites](#requisites) below for details. |  |
| `‑‑demo` | `FILE` | NO | Generate a demo instance from Odoo Cloud and save the connection properties to `FILE`. | `".clorc"` |
| `‑‑out` | `FILE` | NO | Where to stream the output. |  |
| `‑‑log` | `LEVEL` | NO | The level (_`OFF`, `FATAL`, `ERROR`, `WARN`, `INFO`, `DEBUG`, `TRACE`_) of logs to produce. | `"WARN"` |
| `‑‑dry‑run` |  | NO | Perform a "practice" run of the action; implies `--log=DEBUG`. | `false` |
| `‑‑help`<br>`‑h` |  | NO | Show this help message and exit. |  |
| `‑‑version` |  | NO | Show version of this program. |  |

> #### Requisites
> 
> 
> The following inputs are **required**, but have multiple or special specifications. In the absense of these inputs, the program will ask for input:
> 
> - `--instance` can be specified using environment variable **`CLO_INSTANCE`**.
> - `--database` can be specified using environment variable **`CLO_DATABASE`**.
> - `--username` can be specified using environment variable **`CLO_USERNAME`**.
> - The `password` (_or `API-key`_) **MUST BE** specified using environment variable                 **`CLO_PASSWORD`**.
### Actions

The Odoo instance is queried, or operated on, using `ACTIONS`. Each `ACTION` has it's own set of arguements; run `clo ACTION --help` for specific details.

#### Search

```sh
clo [OPTIONS] ACTION ... search [[-o|-n|-a] -d FIELD OPERATOR VALUE [-d ...]] [--offset POSITION] [--limit AMOUNT] [--order FIELD] [--count] [-h]
```

Searches for record IDs based on the search domain.

##### Options

| Flag(s) | Argument | Required | Description                                                                         . | Default |
| :--- | :--: | :--: | :--- | :--- |
| `‑‑domain`<br>`‑d` | `FIELD`<br>`OPERATOR`<br>`VALUE` | NO | A set of criterion to filter the search by (_run `clo explain domains` for details_). This option can be specified multiple times. | `[]` |
| `‑‑or`<br>`‑o` |  | NO | A logical `OR`, placed before two or more domains (_arity 2_). Run `clo explain logic` for more details. |  |
| `‑‑and`<br>`‑a` |  | NO | A logical `AND` to place before two or more domains (_arity 2_). Run `clo explain logic` for more details. |  |
| `‑‑not`<br>`‑n` |  | NO | A logical `OR` to place before a signle domain (_arity 1_). Run `clo explain logic` for more details. |  |
| `‑‑offset` | `POSITION` | NO | Number of results to ignore. | `0` |
| `‑‑limit` | `AMOUNT` | NO | Maximum number of records to return. |  |
| `‑‑order` | `FIELD` | NO | The field to sort the records by. |  |
| `‑‑raw`<br>`‑r` |  | NO | Format output as space-separated IDs rather than pretty JSON. | `false` |
| `‑‑help`<br>`‑h` |  | NO | Show this help message and exit. |  |

#### Count

```sh
clo [OPTIONS] ACTION ... count [--domain FIELD OPERATOR VALUE] [--or] [--and] [--not] [--limit AMOUNT] [--help]
```

Returns the number of records in the current model matching the provided domain.

##### Options

| Flag(s) | Argument | Required | Description                                                                         . | Default |
| :--- | :--: | :--: | :--- | :--- |
| `‑‑domain`<br>`‑d` | `FIELD`<br>`OPERATOR`<br>`VALUE` | NO | A set of criterion to filter the search by (_run `clo explain domains` for details_). This option can be specified multiple times. | `[]` |
| `‑‑or`<br>`‑o` |  | NO | A logical `OR`, placed before two or more domains (_arity 2_). Run `clo explain logic` for more details. |  |
| `‑‑and`<br>`‑a` |  | NO | A logical `AND` to place before two or more domains (_arity 2_). Run `clo explain logic` for more details. |  |
| `‑‑not`<br>`‑n` |  | NO | A logical `OR` to place before a signle domain (_arity 1_). Run `clo explain logic` for more details. |  |
| `‑‑limit` | `AMOUNT` | NO | Maximum number of records to return. |  |
| `‑‑help`<br>`‑h` |  | NO | Show this help message and exit. |  |

#### Read

```sh
clo [OPTIONS] ACTION ... read --ids ID [ID ...] [--fields FIELD [FIELD ...]] [--csv] [--help]
```

Retrieves the details for the records at the ID(s) specified.

##### Options

| Flag(s) | Argument | Required | Description                                                                         . | Default |
| :--- | :--: | :--: | :--- | :--- |
| `‑‑ids`<br>`‑i` | `ID` | YES | The ID number(_s_) of the record(_s_) to perform the action on. Specifying `-` expects a space-separated list from STDIN. |  |
| `‑‑fields`<br>`‑f` | `FIELD` | NO | Field names to return (_default is all fields_). | `[]` |
| `‑‑csv` |  | NO | If `True`, outputs records in CSV format. | `false` |
| `‑‑help`<br>`‑h` |  | NO | Show this help message and exit. |  |

#### Find

```sh
clo [OPTIONS] ACTION ... find [[-o|-n|-a] -d FIELD OPERATOR VALUE [-d ...]] [-f FIELD ...] [--offset POSITION] [--limit AMOUNT] [--order FIELD] [--csv [FILE]] [--help]
```

A shortcut that combines `search` and `read` into one execution.

##### Options

| Flag(s) | Argument | Required | Description                                                                         . | Default |
| :--- | :--: | :--: | :--- | :--- |
| `‑‑domain`<br>`‑d` | `FIELD`<br>`OPERATOR`<br>`VALUE` | NO | A set of criterion to filter the search by (_run `clo explain domains` for details_). This option can be specified multiple times. | `[]` |
| `‑‑or`<br>`‑o` |  | NO | A logical `OR`, placed before two or more domains (_arity 2_). Run `clo explain logic` for more details. |  |
| `‑‑and`<br>`‑a` |  | NO | A logical `AND` to place before two or more domains (_arity 2_). Run `clo explain logic` for more details. |  |
| `‑‑not`<br>`‑n` |  | NO | A logical `OR` to place before a signle domain (_arity 1_). Run `clo explain logic` for more details. |  |
| `‑‑fields`<br>`‑f` | `FIELD` | NO | Field names to return (_default is all fields_). | `[]` |
| `‑‑offset` | `POSITION` | NO | Number of results to ignore. | `0` |
| `‑‑limit` | `AMOUNT` | NO | Maximum number of records to return. |  |
| `‑‑order` | `FIELD` | NO | The field to sort the records by. |  |
| `‑‑csv` |  | NO | If `True`, outputs records in CSV format. | `false` |
| `‑‑help`<br>`‑h` |  | NO | Show this help message and exit. |  |

#### Create

```sh
clo [OPTIONS] ACTION ... create --value FIELD VALUE [--help]
```

Creates new records in the current model.

##### Options

| Flag(s) | Argument | Required | Description                                                                         . | Default |
| :--- | :--: | :--: | :--- | :--- |
| `‑‑value`<br>`‑v` | `FIELD`<br>`VALUE` | YES | Key/value pair(_s_) that correspond to the field and assigment to be made, respectively. |  |
| `‑‑help`<br>`‑h` |  | NO | Show this help message and exit. |  |

#### Write

```sh
clo [OPTIONS] ACTION ... write --ids ID [ID ...] --value FIELD VALUE [--help]
```

Updates existing records in the current model.

##### Options

| Flag(s) | Argument | Required | Description                                                                         . | Default |
| :--- | :--: | :--: | :--- | :--- |
| `‑‑ids`<br>`‑i` | `ID` | YES | The ID number(_s_) of the record(_s_) to perform the action on. Specifying `-` expects a space-separated list from STDIN. |  |
| `‑‑value`<br>`‑v` | `FIELD`<br>`VALUE` | YES | Key/value pair(_s_) that correspond to the field and assigment to be made, respectively. |  |
| `‑‑help`<br>`‑h` |  | NO | Show this help message and exit. |  |

#### Delete

```sh
clo [OPTIONS] ACTION ... delete --ids ID [ID ...] [--help]
```

Deletes the records from the current model.

##### Options

| Flag(s) | Argument | Required | Description                                                                         . | Default |
| :--- | :--: | :--: | :--- | :--- |
| `‑‑ids`<br>`‑i` | `ID` | YES | The ID number(_s_) of the record(_s_) to perform the action on. Specifying `-` expects a space-separated list from STDIN. |  |
| `‑‑help`<br>`‑h` |  | NO | Show this help message and exit. |  |

#### Fields

```sh
clo [OPTIONS] ACTION ... fields [--attributes NAME [NAME ...]] [--help]
```

Retrieves raw details of the fields available in the current model.
For user-friendly formatting, run `clo [OPTIONS] ACTION ... fields explain fields`.

##### Options

| Flag(s) | Argument | Required | Description                                                                         . | Default |
| :--- | :--: | :--: | :--- | :--- |
| `‑‑attributes`<br>`‑‑attr`<br>`‑a` | `NAME` | NO | Attribute(_s_) to return for each field, all if empty or not provided. |  |
| `‑‑help`<br>`‑h` |  | NO | Show this help message and exit. |  |

#### Explain

```sh
clo [OPTIONS] ACTION ... explain [--verbose] [--help] {models,domains,logic,fields}
```

Display documentation on a specified topic.

##### Positional

| Argument | Required | Description                                                                         . | Default |
| :--- | :--: | :--- | :--- |
| `{models,domains,logic,fields}` | YES | A topic to get further explanation on. |  |

##### Options

| Flag(s) | Argument | Required | Description                                                                         . | Default |
| :--- | :--: | :--: | :--- | :--- |
| `‑‑verbose`<br>`‑v` |  | NO | Display more details. | `false` |
| `‑‑help`<br>`‑h` |  | NO | Show this help message and exit. |  |

### Concepts

The following breakdowns apply to search-style `ACTIONS`.


#### DOMAINS

A domain is a set of criteria, each criterion being a throuple of `(FIELD, OPERATOR, VALUE)` where:

`FIELD`:      A field name of the current model, or a relationship traversal through a `Many2one`
              using dot-notation.

`OPERATOR`:   An operand used to compare the `FIELD` with the value. Valid operators are:

              =, !=, >, >=, <, <=   Standard comparison operators.

              =?                    Unset or equals to (_returns true if value is either None or
                                    False, otherwise behaves like `=`_).

              =[i]like              Matches `FIELD` against the value pattern. An underscore (_`_`_)
                                    in the pattern matches any single character; a percent sign
                                    (_`%`_) matches any string of zero or more characters. `=ilike`
                                    makes the search case-insensitive.

              [not ][i]like         Matches (_or inverse-matches_) `FIELD` against the %value%
                                    pattern. Similar to `=[i]like` but wraps value with `%` before
                                    matching.

              [not ]in              Is—or is not—equal to any of the items from value, value should
                                    be a list of items.

              child_of              Is a child (_descendant[2m_) of a value record (_[2mvalue can
                                    be either one item or a list of items_). Takes the semantics
                                    of the model into account (_i.e following the relationship
                                    `FIELD` named by `VALUE`_).

              parent_of             Is a child (_ascendant[2m_) of a value record (_[2mvalue can
                                    be either one item or a list of items_). Takes the semantics
                                    of the model into account (_i.e following the relationship
                                    `FIELD` named by `VALUE`_).

`VALUE`:      Variable type, must be comparable (_through `OPERATOR`_) to the named `FIELD`.

#### LOGIC

Domain criteria can be combined using logical operators in prefix form:

    --or -d login = user -d name = "John Smith" -d email = user@domain.com

is equivalent to `login == "user" || name == "John Smith" || email == "user@domain.com"`

    --not -d login = user` or `-d login '!=' user

are equivalent to `login != "user"`. `--not` is generally unneeded, save for negating the OPERATOR, `child_of`, or `parent_of`.

    --and -d login = user -d name = "John Smith"

is equivalent to `login == "user" && name == "John Smith"`; though, successive domainsimply `--and`.

## See Also


* [Changelog](https://github.com/LeShaunJ/clo/blob/main/CHANGELOG.md)
* [Contributing](https://github.com/LeShaunJ/clo/blob/main/CONTRIBUTING.md)
* [Code of Conduct](https://github.com/LeShaunJ/clo/blob/main/CODE_OF_CONDUCT.md)
* [Security](https://github.com/LeShaunJ/clo/blob/main/SECURITY.md)

![Banner][banner]

[banner]: https://leshaunj.github.io/clo/assets/images/logo-social.png
[build_status_badge]: https://github.com/LeShaunJ/clo/actions/workflows/test.yml/badge.svg
[build_status_link]: https://github.com/LeShaunJ/clo/actions/workflows/test.yml
[coverage_badge]: https://raw.githubusercontent.com/LeShaunJ/clo/main/docs/assets/images/coverage.svg
[coverage_link]: https://raw.githubusercontent.com/LeShaunJ/clo/main/docs/assets/images/coverage.svg
[pypi_badge]: https://badge.fury.io/py/clo.svg
[pypi_link]: https://badge.fury.io/py/clo
