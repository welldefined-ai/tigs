#!/bin/bash
set -e

uv sync
uv pip install -e python/
uv run pytest "$@"