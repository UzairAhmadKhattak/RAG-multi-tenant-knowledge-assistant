from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, delete as sa_delete
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




async def update_or_create(
    db: AsyncSession,
    model,
    defaults: dict | None = None,
    **kwargs
):
    """
    Generic update_or_create

    Usage:
        await update_or_create(
            db,
            User,
            defaults={"name": "New Name", "role": "admin"},
            email="test@test.com"
        )
    """

    stmt = select(model).filter_by(**kwargs)
    instance = await db.scalar(stmt)

    # 1. If exists → update
    if instance:
        if defaults:
            for key, value in defaults.items():
                setattr(instance, key, value)

        try:
            await db.flush()
            return instance, False  # False = not created, updated
        except IntegrityError:
            await db.rollback()
            raise

    # 2. If not exists → create
    params = {**kwargs, **(defaults or {})}
    instance = model(**params)
    db.add(instance)

    try:
        await db.flush()
        return instance, True  # True = created
    except IntegrityError:
        await db.rollback()

        # race condition fallback
        instance = await db.scalar(stmt)
        if instance and defaults:
            for key, value in defaults.items():
                setattr(instance, key, value)
            await db.flush()
            return instance, False

        return instance, False



async def delete_items(
    db: AsyncSession,
    model,
    **kwargs
) -> int:
    """
    Generic delete_items helper

    Usage:
        await delete(db, User, email="test@test.com")
        await delete(db, DocumentChunk, document_id=1)

    Returns:
        Number of rows deleted
    """

    stmt = sa_delete(model).filter_by(**kwargs).returning(model.id)
    result = await db.execute(stmt)

    deleted_ids = result.scalars().all()
    await db.commit()

    return len(deleted_ids)