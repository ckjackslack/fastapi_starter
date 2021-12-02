docker kill $(docker ps -aq)
docker rm $(docker ps -aq)
docker container rm -f $(docker ps -aq)
#docker rmi $(docker images -q)
