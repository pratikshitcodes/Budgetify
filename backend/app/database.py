from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
import os
#pythons os module let us access the enviroment variables
from dotenv import load_dotenv

load_dotenv()
# load_dotenv() reads DATABASE_URL from the .env file
# and adds it to environment variables.
# os.getenv("DATABASE_URL") then reads that value.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Database Connection Failed")
#creating the connection with DATABASE
engine=create_engine(DATABASE_URL)

#creating session factory.Sesssions helps us to query
SessionLocal=sessionmaker(autoflush=False,autocommit=False,bind=engine)
#bind this bind the session with the database think of this like binding the driver to the car(database)
Base=declarative_base()

def get_db():
    #1 request=1 session
    db=SessionLocal()
    try:
        #sends the session to the API router which requests for it
        yield db
    finally:
        db.close()
