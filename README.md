# CLO (Command-Line Odoo)

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

## Installation

```sh
pip3 install clo
```

## Usage

```sh
clo [--model MODEL] [--env FILE] [--inst URL] [--db NAME] [--user NAME] [--demo] [--out FILE] [--log LEVEL] [--dry-run] [--help] [--version] ACTION ...
```

### Globals

The following parameters apply to any [Action](#actions).

#### Options

| Flag(s) | Argument | Required | Description                                                                         . | Default |
| :--- | :--: | :--: | :--- | :--- |
| `‑‑model`<br>`‑m` | `MODEL` | NO | The Odoo model to perform an action on. Run `clo explain models [-v]` to list                             available options. | `"res.users"` |
| `‑‑env` | `FILE` | NO | Path to a `.clorc` file. See [Requisites](#requisites) below for details. | `"/Users/arian/.clorc"` |
| `‑‑inst`<br>`‑‑instance` | `URL` | NO | The address of the Odoo instance. See [Requisites](#requisites) below for details. | `"http://localhost:8069"` |
| `‑‑db`<br>`‑‑database` | `NAME` | NO | The application database to perform operations on. See [Requisites](#requisites) below                             for details. | `""` |
| `‑‑user` | `NAME` | NO | The user to perform operations as. See [Requisites](#requisites) below for details. | `""` |
| `‑‑demo` |  | NO | Generate and use a demo instance from Odoo Cloud. |  |
| `‑‑out` | `FILE` | NO | Where to stream the output. |  |
| `‑‑log` | `LEVEL` | NO | The level (`OFF`, `FATAL`, `ERROR`, `WARN`, `INFO`, `DEBUG`, `TRACE`) of logs to produce. | `"ERROR"` |
| `‑‑dry‑run` |  | NO | Perform a "practice" run of the action; implies `--log=DEBUG`. | `false` |
| `‑‑help`<br>`‑h` |  | NO | Show this help message and exit. |  |
| `‑‑version` |  | NO | Show version of this program. |  |

> #### Requisites
> 
> 
> The following inputs are **required**, but have multiple or special specifications. In                     the absense of these inputs, the program will ask for input:
> 
>   - `--instance` can be specified using environment variable **`OD_INST`**.
>   - `--database` can be specified using environment variable **`OD_DATA`**.
>   - `--username` can be specified using environment variable **`OD_USER`**.
>   - The `password` (or `API-key`) **MUST BE** specified using environment variable                     **`OD_PASS`**.
### Actions

The Odoo instance is queried, or operated on, using `ACTIONS`. Each `ACTION` has it's                     own set of arguements; run `clo ACTION --help` for specific details.

#### Search

```sh
clo search [[-o|-n|-a] -d FIELD OPERATOR VALUE [-d ...]] [--offset POSITION]                                 [--limit AMOUNT] [--order FIELD] [--count] [-h]
```

Searches for record IDs based on the search domain.

##### Options

| Flag(s) | Argument | Required | Description                                                                         . | Default |
| :--- | :--: | :--: | :--- | :--- |
| `‑‑domain`<br>`‑d` | `FIELD`<br>`OPERATOR`<br>`VALUE` | NO | A set of criterion to filter the search by (run `clo explain domains` for                         details). This option can be specified multiple times. | `[]` |
| `‑‑or`<br>`‑o` |  | NO | A logical `OR`, placed before two or more domains (arity 2). Run `clo explain                         logic` for more details. |  |
| `‑‑and`<br>`‑a` |  | NO | A logical `AND` to place before two or more domains (arity 2). Run `clo explain                         logic` for more details. |  |
| `‑‑not`<br>`‑n` |  | NO | A logical `OR` to place before a signle domain (arity 1). Run `clo explain                         logic` for more details. |  |
| `‑‑offset` | `POSITION` | NO | Number of results to ignore. | `0` |
| `‑‑limit` | `AMOUNT` | NO | Maximum number of records to return. |  |
| `‑‑order` | `FIELD` | NO | The field to sort the records by. |  |
| `‑‑raw`<br>`‑r` |  | NO | Format output as space-separated IDs rather than pretty JSON. | `false` |
| `‑‑help`<br>`‑h` |  | NO | Show this help message and exit. |  |

#### Count

```sh
clo count [--domain FIELD OPERATOR VALUE] [--or] [--and] [--not] [--limit AMOUNT] [--help]
```

Returns the number of records in the current model matching the provided                                 domain.

##### Options

| Flag(s) | Argument | Required | Description                                                                         . | Default |
| :--- | :--: | :--: | :--- | :--- |
| `‑‑domain`<br>`‑d` | `FIELD`<br>`OPERATOR`<br>`VALUE` | NO | A set of criterion to filter the search by (run `clo explain domains` for                         details). This option can be specified multiple times. | `[]` |
| `‑‑or`<br>`‑o` |  | NO | A logical `OR`, placed before two or more domains (arity 2). Run `clo explain                         logic` for more details. |  |
| `‑‑and`<br>`‑a` |  | NO | A logical `AND` to place before two or more domains (arity 2). Run `clo explain                         logic` for more details. |  |
| `‑‑not`<br>`‑n` |  | NO | A logical `OR` to place before a signle domain (arity 1). Run `clo explain                         logic` for more details. |  |
| `‑‑limit` | `AMOUNT` | NO | Maximum number of records to return. |  |
| `‑‑help`<br>`‑h` |  | NO | Show this help message and exit. |  |

#### Read

```sh
clo read --ids ID [ID ...] [--fields FIELD [FIELD ...]] [--csv] [--help]
```

Retrieves the details for the records at the ID(s) specified.

##### Options

| Flag(s) | Argument | Required | Description                                                                         . | Default |
| :--- | :--: | :--: | :--- | :--- |
| `‑‑ids`<br>`‑i` | `ID` | YES | The ID number(s) of the record(s) to perform the action on. Specifying "-" expects a                     speace-separated list from STDIN. |  |
| `‑‑fields`<br>`‑f` | `FIELD` | NO | Field names to return (default is all fields). | `[]` |
| `‑‑csv` |  | NO | If `True`, outputs records in CSV format. | `false` |
| `‑‑help`<br>`‑h` |  | NO | Show this help message and exit. |  |

#### Find

```sh
clo find [[-o|-n|-a] -d FIELD OPERATOR VALUE [-d ...]] [-f FIELD ...]                                 [--offset POSITION] [--limit AMOUNT] [--order FIELD] [--csv [FILE]] [--help]
```

A shortcut that combines `search` and `read` into one execution.

##### Options

| Flag(s) | Argument | Required | Description                                                                         . | Default |
| :--- | :--: | :--: | :--- | :--- |
| `‑‑domain`<br>`‑d` | `FIELD`<br>`OPERATOR`<br>`VALUE` | NO | A set of criterion to filter the search by (run `clo explain domains` for                         details). This option can be specified multiple times. | `[]` |
| `‑‑or`<br>`‑o` |  | NO | A logical `OR`, placed before two or more domains (arity 2). Run `clo explain                         logic` for more details. |  |
| `‑‑and`<br>`‑a` |  | NO | A logical `AND` to place before two or more domains (arity 2). Run `clo explain                         logic` for more details. |  |
| `‑‑not`<br>`‑n` |  | NO | A logical `OR` to place before a signle domain (arity 1). Run `clo explain                         logic` for more details. |  |
| `‑‑fields`<br>`‑f` | `FIELD` | NO | Field names to return (default is all fields). | `[]` |
| `‑‑offset` | `POSITION` | NO | Number of results to ignore. | `0` |
| `‑‑limit` | `AMOUNT` | NO | Maximum number of records to return. |  |
| `‑‑order` | `FIELD` | NO | The field to sort the records by. |  |
| `‑‑csv` |  | NO | If `True`, outputs records in CSV format. | `false` |
| `‑‑help`<br>`‑h` |  | NO | Show this help message and exit. |  |

#### Create

```sh
clo create --value FIELD VALUE [--help]
```

Creates new records in the current model.

##### Options

| Flag(s) | Argument | Required | Description                                                                         . | Default |
| :--- | :--: | :--: | :--- | :--- |
| `‑‑value`<br>`‑v` | `FIELD`<br>`VALUE` | YES | Key/value pair(s) that correspond to the field and assigment to be made, respectively. |  |
| `‑‑help`<br>`‑h` |  | NO | Show this help message and exit. |  |

#### Write

```sh
clo write --ids ID [ID ...] --value FIELD VALUE [--help]
```

Updates existing records in the current model.

##### Options

| Flag(s) | Argument | Required | Description                                                                         . | Default |
| :--- | :--: | :--: | :--- | :--- |
| `‑‑ids`<br>`‑i` | `ID` | YES | The ID number(s) of the record(s) to perform the action on. Specifying "-" expects a                     speace-separated list from STDIN. |  |
| `‑‑value`<br>`‑v` | `FIELD`<br>`VALUE` | YES | Key/value pair(s) that correspond to the field and assigment to be made, respectively. |  |
| `‑‑help`<br>`‑h` |  | NO | Show this help message and exit. |  |

#### Delete

```sh
clo delete --ids ID [ID ...] [--help]
```

Deletes the records from the current model.

##### Options

| Flag(s) | Argument | Required | Description                                                                         . | Default |
| :--- | :--: | :--: | :--- | :--- |
| `‑‑ids`<br>`‑i` | `ID` | YES | The ID number(s) of the record(s) to perform the action on. Specifying "-" expects a                     speace-separated list from STDIN. |  |
| `‑‑help`<br>`‑h` |  | NO | Show this help message and exit. |  |

#### Fields

```sh
clo fields [--attributes NAME [NAME ...]] [--help]
```

Retrieves raw details of the fields available in the current model.
For                                 user-friendly formatting, run `clo fields explain fields`.

##### Options

| Flag(s) | Argument | Required | Description                                                                         . | Default |
| :--- | :--: | :--: | :--- | :--- |
| `‑‑attributes`<br>`‑‑attr`<br>`‑a` | `NAME` | NO | Attribute(s) to return for each field, all if empty or not provided |  |
| `‑‑help`<br>`‑h` |  | NO | Show this help message and exit. |  |

#### Explain

```sh
clo explain [--verbose] [--help] {models,domains,logic,fields}
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

