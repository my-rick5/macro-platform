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
                    // hostPath is the Jenkins workspace on the server
                    def hostPath = WORKSPACE 
                    
                    echo "🧪 Running Structural Validation..."
                    // We mount the workspace to /workspace inside the container
                    sh """
                        docker run --rm \
                        -v ${hostPath}:/workspace \
                        -w /workspace \
                        ${DOCKER_IMAGE} python3 -m pytest tests/test_model_load.py
                    """
        
                    echo "🚀 Running Engine..."
                    // We mount only the needed folders so we don't overwrite /home/spark/.local
                    sh """
                        docker run --rm \
                        --memory='6g' \
                        -v ${hostPath}/models:/home/spark/models \
                        -v ${hostPath}/data:/home/spark/data \
                        -v ${hostPath}/results:/home/spark/results \
                        -w /home/spark \
                        ${DOCKER_IMAGE} python3 src/engine.py
                    """
                }
            }
        }

    post {
        always {
            archiveArtifacts artifacts: 'results/*.csv, models/*.xml', allowEmptyArchive: true
        }
    }
}