# 1. Use Python Slim
FROM python:3.11-slim

# 2. Set env variables
ENV PYTHONUNBUFFERED=1

# Create workdir for code
WORKDIR /app

# 3. Install dependencies
COPY ./apirequirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# 4. Copy app
# This puts main.py and schemas.py DIRECTLY inside /app
COPY ./project/app /app

# 5. Launch
# FIX: Change "app/main.py" to "main.py"
# Since WORKDIR is /app, we execute relative to that folder.
# Added --host 0.0.0.0 to ensure it is accessible outside the container.
CMD ["fastapi", "run", "main.py", "--port", "8080", "--host", "0.0.0.0"]