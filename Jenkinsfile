pipeline {
    agent any

    environment {
        PYPI_TOKEN = credentials('pypi_token')
    }

    stages {
        stage('Checkout'){
            steps {
                checkout scm
            }
        }
        stage('Build and publish pypi package') {
            when { expression { sh([returnStdout: true, script: "git tag -l --contains $GIT_COMMIT | grep '^v' || true"]) } }
            steps {
                sh '''
                # If we are within docker, we need to hack around to get the volume mount path on the host system for our docker runs down below
                if docker inspect `hostname` 2>/dev/null; then
                    DOCKER_VOLUME_ROOT=$(docker inspect `hostname` | jq -r '.[0].Mounts | .[] | select(.Destination=="/home/jenkins") | .Source')
                    REAL_PWD=$(echo $PWD | sed "s|/home/jenkins|$DOCKER_VOLUME_ROOT|")
                else
                    REAL_PWD=$PWD
                fi
                docker run --rm -v $REAL_PWD:/app -w /app python:3.10-slim-buster bash -c "pip install poetry && poetry build -f sdist && poetry publish -n -u __token__ -p $PYPI_TOKEN"
                '''
            }
        }
    }
}