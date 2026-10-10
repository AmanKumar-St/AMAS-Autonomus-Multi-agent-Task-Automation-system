
FROM node:22-bookworm-slim

WORKDIR /app

# Install Python and build tools
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       python3 python3-venv python3-pip build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js dependencies
COPY package*.json ./
RUN npm ci

# Install Python dependencies in a virtual environment
COPY requirements.txt ./
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade "pip<24.1" setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Build frontend assets and the Express server
RUN npm run build

ENV NODE_ENV=production

CMD ["npm", "start"]
