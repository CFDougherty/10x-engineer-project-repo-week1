TEST_DB_URL := postgresql+asyncpg://promptlab:promptlab@localhost:5432/promptlab_test

.PHONY: test test-down help

## Run the full test suite (starts the database if needed)
test:
	@echo "Starting database..."
	docker-compose up db -d
	@echo "Waiting for database to be ready..."
	@until docker-compose exec -T db pg_isready -U promptlab > /dev/null 2>&1; do sleep 1; done
	@echo "Running tests..."
	@set +e; cd backend && TEST_DATABASE_URL=$(TEST_DB_URL) python -m pytest tests/ -v $(ARGS); \
	EXIT_CODE=$$?; \
	cd ..; \
	docker-compose down; \
	exit $$EXIT_CODE

## Stop and remove the database container
test-down:
	docker-compose down

## Show this help
help:
	@grep -E '^##' Makefile | sed 's/## //'
