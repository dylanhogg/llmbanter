# LLM Banter

[![PyPI version](https://badge.fury.io/py/llmbanter.svg?1)](https://badge.fury.io/py/llmbanter)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Build](https://github.com/dylanhogg/llmbanter/workflows/build/badge.svg)](https://github.com/dylanhogg/llmbanter/actions/workflows/python-poetry-app.yml)
[![Latest Tag](https://img.shields.io/github/v/tag/dylanhogg/llmbanter)](https://github.com/dylanhogg/llmbanter/tags)

<!-- [![Downloads](https://static.pepy.tech/badge/llmbanter)](https://pepy.tech/project/llmbanter)
[![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/dylanhogg/llmbanter/blob/master/notebooks/llmbanter_colab_custom_story.ipynb) -->

LLM Banter: See 2 large language models (LLMs) banter, debate and chat with each other.

NOTE: This project is currently a WIP. Aiming for v1.0 release by end of March 2024.

![Two AI Robots in discussion](https://github.com/dylanhogg/llmbanter/blob/main/docs/img/header.jpg?raw=true)

## Installation

You can install [llmbanter](https://pypi.org/project/llmbanter/) using pip, ideally into a Python [virtual environment](https://realpython.com/python-virtual-environments-a-primer/#create-it).

```bash
pip install llmbanter
```

## Usage Examples

Have 2 bots chat with each other:

```bash
llmbanter expert/psychiatrist famous/einstein
```

Talk to a Python programming expert:

```bash
llmbanter expert/python human
```

Try jail breaking a bot to get it's system prompt etc:

```bash
llmbanter system/jailbreaker expert/python
```

Run a bot under a different LLM provider:

```bash
llmbanter TODO --TODO
```

This project is [MIT](https://github.com/dylanhogg/llmbanter/blob/main/LICENSE) licensed.
