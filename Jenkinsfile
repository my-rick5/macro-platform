pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'macro-engine-local:latest'
        CONTAINER_NAME = "engine-run-${BUILD_NUMBER}"
    }

    stages {
        stage('Initialize') {
            steps {
                sh "mkdir -p results models data"
                // Cleanup any old containers with this build number
                sh "docker rm -f ${CONTAINER_NAME} || true"
            }
        }

        stage('Run Engine') {
            steps {
                script {
                    echo "🧪 Preparing Container & Data..."
                    sh "docker run -d --name ${CONTAINER_NAME} --user 0:0 --entrypoint tail ${DOCKER_IMAGE} -f /dev/null"
                    sh "docker cp . ${CONTAINER_NAME}:/workspace"
                    
                    sh """
                        docker exec ${CONTAINER_NAME} mkdir -p /home/spark/models /home/spark/data /home/spark/results
                        docker exec ${CONTAINER_NAME} cp /workspace/pyfrbus/models/model.xml /home/spark/models/model.xml
                        docker exec ${CONTAINER_NAME} cp /workspace/data/tealbook_unemployment.csv /home/spark/data/y_unemp.csv
                    """

                    echo "🧪 Running Structural Validation..."
                    // We combine the spark user's library path WITH your custom model path
                    sh """
                        docker exec -w /workspace \
                        -e PYTHONPATH=/home/spark/.local/lib/python3.9/site-packages:/home/spark/pyfrbus:/workspace \
                        ${CONTAINER_NAME} python3 -m pytest tests/test_model_load.py
                    """
        
                    echo "🚀 Running Engine..."
                    sh """
                        docker exec -w /home/spark \
                        -e PYTHONPATH=/home/spark/.local/lib/python3.9/site-packages:/home/spark/pyfrbus \
                        ${CONTAINER_NAME} python3 src/engine.py
                    """
                    
                    echo "📥 Pulling Results..."
                    sh "docker cp ${CONTAINER_NAME}:/home/spark/results/. ./results/"
                }
            }
        }
    } // End of Stages

    post {
        always {
            script {
                echo "🧹 Cleaning up container..."
                sh "docker rm -f ${CONTAINER_NAME} || true"
            }
            echo "📦 Archiving Results..."
            archiveArtifacts artifacts: 'results/*.csv, models/*.xml', allowEmptyArchive: true
        }
    }
} // End of Pipeline