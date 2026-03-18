#!/bin/bash

# Останавливать выполнение, если любая команда завершилась с ошибкой
set -e

echo "--- Running flake8 ---"
flake8 src/ tests/

echo "--- Running black ---"
black src/ tests/

echo "--- Running isort ---"
isort src/ tests/

echo "--- Running mypy ---"
mypy src/ tests/

echo "--- All checks passed! ---"
