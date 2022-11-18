# Pong

## Deploying

- Build the Docker image for running the Flask app: `docker build .`
- Create a network for the docker containers to communicate to each other within: `docker network create pong`
- Check for any currently running containers: `docker ps`, `docker stop <CONTAINER>`
- Run the webapp container in the background: `docker run -d --rm --net pong -p 5001:5001 <IMAGE>`
- Pull the memcached Docker image: `docker pull memcached`
- Run a container for the memcached image: `docker run -d --rm --net pong --name memcached memcached`

## Deploying locally without Docker

### Linux
- sudo apt install memcached
- service memcached start

### Mac
- memcached -d

