from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def get_or_create(
    db: AsyncSession,
    model,
    defaults: dict | None = None,
    **kwargs
):
    """
    Generic get_or_create

    Usage:
        await get_or_create(db, Organization, name="OpenAI")
        await get_or_create(db, User, email="test@test.com", defaults={"role": "admin"})
    """

    # 1. Try to get existing
    stmt = select(model).filter_by(**kwargs)
    instance = await db.scalar(stmt)

    if instance:
        return instance, False

    # 2. Create new
    params = {**kwargs, **(defaults or {})}
    instance = model(**params)
    db.add(instance)

    try:
        await db.flush()
        return instance, True
    except IntegrityError:
        await db.rollback()

        # Fetch again (created by another transaction)
        instance = await db.scalar(stmt)
        return instance, False