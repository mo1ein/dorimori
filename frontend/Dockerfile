FROM node:14.21.3
# Set working directory
WORKDIR /app

# Copy package.json and install dependencies
COPY . .

RUN npm i --loglevel verbose

# Expose port 3000 for the app
EXPOSE 3000

# Command to run the app
CMD ["npm", "start"]