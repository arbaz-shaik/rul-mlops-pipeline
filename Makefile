.PHONY: install lint test up down clean

install:
    pip install -r requirements.txt

lint:
    ruff check src/ tests/ pipeline/ experiments/

test:
    pytest tests/ -v

up:
    docker-compose up --build

down:
    docker-compose down

clean:
    docker-compose down -v
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type d -name .pytest_cache -exec rm -rf {} +
