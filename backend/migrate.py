from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE users ALTER COLUMN password DROP NOT NULL;"))
    except Exception as e:
        print('Password column alter failed:', e)
    
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN auth_provider VARCHAR DEFAULT 'email' NOT NULL;"))
    except Exception as e:
        print('auth_provider add failed:', e)

    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN google_id VARCHAR UNIQUE;"))
    except Exception as e:
        print('google_id add failed:', e)
    
    conn.commit()
    print("Migration successful")
