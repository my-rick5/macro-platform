pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'macro-engine-local:latest'
    }

    stages {
        stage('Initialize') {
            steps {
                sh "mkdir -p results models"
                // Clean up any dangling containers from previous failed runs
                sh "docker ps -a -q --filter ancestor=${DOCKER_IMAGE} | xargs -r docker rm -f"
            }
        }

        stage('Fetch Model Logic') {
            steps {
                echo "🧠 Preparing model.xml..."
                sh "cp pyfrbus/models/model.xml ./model.xml"
            }
        }

        stage('Run Engine') {
            steps {
                script {
                    def workspaceRelPath = WORKSPACE.replace("/var/jenkins_home/", "")
                    
                    // We run as the 'spark' user defined in your Dockerfile. 
                    // We only mount the WORKSPACE to /home/spark/data so we don't 
                    // overwrite the pre-installed code in /home/spark/src or /home/spark/.local
                    
                    echo "🧪 Running Structural Validation..."
                    sh """
                        docker run --rm \
                        -v jenkins_home:/var/jenkins_home \
                        -w /home/spark \
                        ${DOCKER_IMAGE} python3 -m pytest tests/test_model_load.py
                    """

                    echo "🚀 Running Engine..."
                    sh """
                        docker run --rm \
                        --memory='6g' \
                        -v jenkins_home:/var/jenkins_home \
                        -v ${WORKSPACE}/results:/home/spark/results \
                        -w /home/spark \
                        ${DOCKER_IMAGE} python3 src/engine.py
                    """
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'results/*.csv, models/*.xml', allowEmptyArchive: true
        }
    }
}