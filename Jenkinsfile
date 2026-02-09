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
                    
                    // Flattened copy
                    sh "docker cp pyfrbus/pyfrbus/. ${CONTAINER_NAME}:/home/spark/pyfrbus/"
                    sh "docker cp . ${CONTAINER_NAME}:/source_code"

                    echo "🔍 DEBUG: Probing Container Filesystem..."
                    sh """
                        echo '--- Directory Structure of /home/spark/pyfrbus ---'
                        docker exec ${CONTAINER_NAME} ls -R /home/spark/pyfrbus
                        echo '--- Python Path & Import Check ---'
                        docker exec -e PYTHONPATH=/home/spark ${CONTAINER_NAME} python3 -c "import sys; print('\\n'.join(sys.path)); import pyfrbus; print('SUCCESS: pyfrbus imported from:', pyfrbus.__file__)" || echo "FAILURE: pyfrbus still not found"
                    """

                    sh """
                        docker exec ${CONTAINER_NAME} mkdir -p /home/spark/models /home/spark/data /home/spark/results
                        docker exec ${CONTAINER_NAME} cp /source_code/pyfrbus/models/model.xml /home/spark/models/model.xml
                        docker exec ${CONTAINER_NAME} cp /source_code/data/tealbook_unemployment.csv /home/spark/data/y_unemp.csv
                    """

                    echo "🧪 Running Structural Validation..."
                    sh """
                        docker exec -w /source_code \
                        -e PYTHONPATH=/home/spark/.local/lib/python3.9/site-packages:/home/spark:/source_code \
                        ${CONTAINER_NAME} python3 -m pytest -vv tests/test_model_load.py
                    """
        
                    echo "🚀 Running Engine..."
                    sh """
                        docker exec -w /home/spark \
                        -e PYTHONPATH=/home/spark/.local/lib/python3.9/site-packages:/home/spark:/source_code/src \
                        ${CONTAINER_NAME} python3 /source_code/src/engine.py
                    """
                    
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