#!/bin/sh
set -e

echo "Waiting for database..."
while ! python -c "
import asyncio
from sqlalchemy import text
from app.db.session import engine

async def check():
    async with engine.connect() as conn:
        await conn.execute(text('SELECT 1'))

asyncio.run(check())
" 2>/dev/null; do
    sleep 1
done
echo "Database is ready."

# Try to upgrade; if no migrations exist, stamp with current head
alembic upgrade head 2>/dev/null || {
    echo "No migrations found, creating tables directly..."
    python -c "
import asyncio
from app.db.session import engine
from app.db.base import Base
from app.models.models import *  # noqa

async def create():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

asyncio.run(create())
print('Tables created successfully.')
"
    # Generate initial migration and stamp
    alembic stamp head 2>/dev/null || true
}

# Seed database with initial data
echo "Seeding database..."
python -m app.seed

echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000