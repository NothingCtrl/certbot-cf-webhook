import os
from apps import app
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", '9000')))
