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
		stage('Get package version') {
			steps {
				script {
					PACKAGE_VERSION = sh (
						script: """
						cat pyproject.toml | grep "^version" | sed -e "s/^version = \\"\\([0-9.]\\+\\)\\"/\\1/g"
						""",
						returnStdout: true
					).trim();
					echo "Building v${PACKAGE_VERSION}"
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
				docker run --rm -v $REAL_PWD:/app -w /app python:3-slim-buster bash -c "pip install uv && uv build"
				'''
			}
		}
		stage('Prep buildx') {
				steps {
						script {
								env.BUILDX_BUILDER = getBuildxBuilder();
						}
				}
		}
		stage('Build Docker image') {
				steps {
						withCredentials([usernamePassword(credentialsId: 'dockerhub', usernameVariable: 'DOCKERHUB_CREDENTIALS_USR', passwordVariable: 'DOCKERHUB_CREDENTIALS_PSW')]) {
								sh 'docker login -u $DOCKERHUB_CREDENTIALS_USR -p "$DOCKERHUB_CREDENTIALS_PSW"'
						}
						sh """
								docker buildx build \
										--pull \
										--builder \$BUILDX_BUILDER \
										--platform linux/amd64,linux/arm64 \
										-t nbr23/ydl-podcast:latest \
										-t nbr23/ydl-podcast:yt-dlp \
										-t nbr23/ydl-podcast:${GIT_COMMIT}-`date +%s`-yt-dlp \
										-t nbr23/ydl-podcast:v${PACKAGE_VERSION} \
										${ "$GIT_BRANCH" == "master" ? "--push" : ""} .
								"""
				}
		}
		stage('Publish pypi package') {
			when { branch 'master' }
			steps {
				sh '''
				# If we are within docker, we need to hack around to get the volume mount path on the host system for our docker runs down below
				if docker inspect `hostname` 2>/dev/null; then
					REAL_PWD=$(echo $PWD | sed "s|$AGENT_WORKDIR|$JENKINS_HOME_VOL_SRC|")
				else
					REAL_PWD=$PWD
				fi
				docker run --rm -v $REAL_PWD:/app -w /app python:3-slim-buster bash -c "pip install uv && uv build && uv publish --token $PYPI_TOKEN"
				'''
			}
		}
		stage('Sync github repo') {
				when { branch 'master' }
				steps {
						syncRemoteBranch('git@github.com:nbr23/ydl-podcast.git', 'master')
				}
		}

	}
	post {
		always {
			sh "sudo rm -rf ./dist"
			sh "docker buildx stop \$BUILDX_BUILDER || true"
			sh "docker buildx rm \$BUILDX_BUILDER || true"
		}
	}
}
