pipeline {
	agent any

	options {
		ansiColor('xterm')
		disableConcurrentBuilds()
	}


	environment {
		PYPI_TOKEN = credentials('pypi_token')
	}

	stages {
		stage('Checkout'){
			steps {
				checkout scm
			}
		}
		stage('Get Jenkins home source volume') {
			steps {
				script {
					env.JENKINS_HOME_VOL_SRC = getJenkinsDockerHomeVolumeSource();
				}
			}
		}
		stage('Build') {
			steps {
				sh '''
				# If we are within docker, we need to hack around to get the volume mount path on the host system for our docker runs down below
				if docker inspect `hostname` 2>/dev/null; then
					REAL_PWD=$(echo $PWD | sed "s|$AGENT_WORKDIR|$JENKINS_HOME_VOL_SRC|")
				else
					REAL_PWD=$PWD
				fi
				docker run --rm -v $REAL_PWD:/app -w /app python:3-slim-buster bash -c "pip install poetry && poetry build"
				'''
			}
		}
		stage('Publish pypi package') {
			steps {
				sh '''
				# If we are within docker, we need to hack around to get the volume mount path on the host system for our docker runs down below
				if docker inspect `hostname` 2>/dev/null; then
					REAL_PWD=$(echo $PWD | sed "s|$AGENT_WORKDIR|$JENKINS_HOME_VOL_SRC|")
				else
					REAL_PWD=$PWD
				fi
				docker run --rm -v $REAL_PWD:/app -w /app python:3-slim-buster bash -c "pip install poetry && poetry publish -n -u __token__ -p $PYPI_TOKEN"
				'''
			}
		}
	}
	post {
		always {
			sh "sudo rm -rf ./dist"
		}
	}
}