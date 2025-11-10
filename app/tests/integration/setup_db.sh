#!/bin/bash
set -e

echo "⏳ Waiting for PostgreSQL to be ready..."

# Wait for PostgreSQL to be available
until docker exec tyriavault-postgres-test pg_isready -U test_user -d tyriavault_test > /dev/null 2>&1; do
  echo "PostgreSQL is not ready yet, waiting..."
  sleep 2
done

echo "✅ PostgreSQL is ready"

echo "📄 Running SQL schema (TyriaVault_Model.sql)..."
docker exec -i tyriavault-postgres-test psql -U test_user -d tyriavault_test < TyriaVault_Model.sql

echo "✅ Database initialized successfully"

