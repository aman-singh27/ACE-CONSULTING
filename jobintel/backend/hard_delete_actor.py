import asyncio
from sqlalchemy import select, delete
from app.db.session import async_session_factory
from app.models.actor_config import ActorConfig

async def main():
    async with async_session_factory() as session:
        # Check if actor exists
        stmt = select(ActorConfig).where(ActorConfig.actor_id == 'cheap_scraper/linkedin-job-scraper')
        result = await session.execute(stmt)
        actor = result.scalars().first()
        
        if actor:
            print(f"Deleting actor {actor.id}")
            # Delete dependent actor_runs first
            from sqlalchemy import text
            await session.execute(text("DELETE FROM actor_runs WHERE actor_config_id = :actor_id"), {"actor_id": actor.id})
            
            delete_stmt = delete(ActorConfig).where(ActorConfig.id == actor.id)
            await session.execute(delete_stmt)
            await session.commit()
            print("Successfully hard deleted.")
        else:
            print("Actor not found in database.")

if __name__ == "__main__":
    asyncio.run(main())
