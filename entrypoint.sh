#!/bin/bash
python -m pip install -e .['test']

exec tail -f /dev/null
