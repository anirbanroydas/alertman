#!/bin/bash
#
# NOTE: When the ci job is triggered due to a pull request,
# this script will not be run, since we only want to see if the tests ran successfully
# in case of pull requests
# AFter tests pass, we merge the pull request, and only then we will execute this script

set -e

DOCKER="docker"
DOCKER_COMPOSE="docker-compose"

REGISTRY="hub.docker.com"
DOCKER_USERNAME="aroyd"
PROJECT="$1"
BRANCH="$2"
COMMIT="$3"
BUILD_DATE=$(date +%Y%m%dH%HM%MS%S)

if [ ! -z "$COMMIT" -a "$COMMIT"  != " " ] ; then
    echo "COMMIT is not empty, removing date and time for tag value "
    BUILD_DATE=""
fi

BUILD_TAG="${BRANCH}.${COMMIT}${BUILD_DATE}"
DOCKER_REPO="${DOCKER_USERNAME}/${PROJECT}"


function push() {
    # now push
    DOCKER_PUSH=1;
    while [ $DOCKER_PUSH -gt 0 ] ; do
        echo "Pushing $DOCKER_REPO";
        $DOCKER push "$DOCKER_REPO";
        DOCKER_PUSH=$(echo $?);
        if [ "$DOCKER_PUSH" -gt 0 ] ; then
            echo "Docker push failed with exit code $DOCKER_PUSH";
        fi;
    done;

    if [ $DOCKER_PUSH -gt 0 ]; then
        exit $DOCKER_PUSH
    fi
}


function build() {
    # build image
    echo "Building Image $DOCKER_REPO:$BUILD_TAG and $DOCKER_REPO:latest"
    $DOCKER build -t ${DOCKER_REPO}:"$BUILD_TAG" -t ${DOCKER_REPO}:latest .
}

function buildtagpush() {
    # build and tag
    build

    # push
    # finally push all the tagged images
    echo "Pushing to docker repo"
    push
}

buildtagpush


##############################################
#           Not using these                 #
#############################################

function login() {
    # login to docker registry
    echo "Docker Loggin in to registry"
    $DOCKER login -e $DOCKER_EMAIL -u $DOCKER_USER -p $DOCKER_PASS
}


function tag() {
    if [ -z "$1" ] ; then
        echo "Please pass the tag"
        exit 1
    else
        TAG=$1
    fi
    
    if [ "$COMMIT" != "$TAG" ]; then
        $DOCKER tag ${DOCKER_REPO}:${INITIAL_TAG} ${DOCKER_REPO}:${TAG}
    fi
}



