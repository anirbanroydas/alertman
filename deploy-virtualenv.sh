#!/bin/sh

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

rmvenv() {
	# remove the virtualenv
	echo "Removing virtual environment trash files"
	rm -rf venv
}

cleanup() {
	# deactivate the virtual environemt
	echo "Cleaning up vitualenv"
	echo "Deactivating...."
	deactivate
	rmvenv
}

# trap 'cleanup ; printf "${RED}Error happened while deploying${NC}\n"' HUP INT QUIT PIPE TERM


# first remove previous venv if at all
rmvenv
# now begine new deployment
virtualenv --python=python3 venv
if [ $? -ne 0 ]; then
	echo "Unable to create virtualenv"
else
	echo "Activating virtual environment venv"
	source venv/bin/activate
	if [ $? -ne 0 ]; then
		echo "Unable to activate virtual environment venv"
		rmvenv
	else
		# Install pip dependencies
		pip install -r requirements.txt
		if [ $? -ne 0 ]; then
			cleanup
		else
			pip install -r requirements-dev.txt
			if [ $? -ne 0 ]; then
				cleanup
			else
				# initialize the environment variables
				set -a
				source .env
				set +a
				if [ $? -ne 0 ]; then
					cleanup
				else
					# install the service
					echo "Deployment environment : $DEPLOYMENT_ENVIRONMENT"
					echo "pip install"
					if [ "$DEPLOYMENT_ENVIRONMENT" = "prod" ]; then
						echo "pip install --no-deps ."
						pip install --no-deps .
					else
						echo "pip install --no-deps -e ."
						pip install --no-deps -e .
					fi
					if [ $? -ne 0 ]; then
						cleanup
					else
						# Run the server
						echo "Starting server..."	
						python alertman/worker.py
						# supervisord -c supervisor/supervisor.conf
					fi
				fi
			fi
		fi		
	fi
fi












