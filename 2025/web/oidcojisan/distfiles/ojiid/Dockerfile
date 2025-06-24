# Use Node.js LTS version
FROM node:24.1.0-slim@sha256:5ae787590295f944e7dc200bf54861bac09bf21b5fdb4c9b97aee7781b6d95a2

# Create app directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies including dev dependencies for build
RUN npm install

# Copy app source
COPY . .

# Build TypeScript code
RUN npm run build

# Expose port
EXPOSE 36001

# Start the app
CMD ["npm", "start"]
