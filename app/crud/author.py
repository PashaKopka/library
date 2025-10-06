from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.author import Author


async def get_or_create_authors(
    db: AsyncSession,
    author_names: list[str],
) -> list[Author]:
    existing_authors = await db.execute(
        select(Author).filter(Author.name.in_(author_names))
    )
    existing_authors = list(existing_authors.scalars().all())

    existing_names = {str(author.name) for author in existing_authors}
    new_names = set(author_names) - existing_names

    new_authors = [Author(name=name) for name in new_names]
    db.add_all(new_authors)

    if new_authors:
        await db.commit()

        for author in new_authors:
            await db.refresh(author)

    return existing_authors + new_authors
