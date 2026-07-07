#!/bin/bash

set -e


export UV_CACHE_DIR="/goinfre/$USER/uv-cache"
export HF_HOME="/goinfre/$USER/hf-cache"
export TRANSFORMERS_CACHE="/goinfre/$USER/hf-cache"

echo "Cache directories configured."


uv venv "/goinfre/$USER/RAG_against_the_machine_venv"


rm -rf .venv


ln -s "/goinfre/$USER/RAG_against_the_machine_venv" .venv


source ".venv/bin/activate"

echo "Environment ready and activated!"
