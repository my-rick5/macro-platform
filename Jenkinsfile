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
                    
                    sh "docker cp . ${CONTAINER_NAME}:/source_code"

                    echo "📦 Final Flattening & System Install..."
                    sh """
                        # Create a completely fresh flat source
                        docker exec ${CONTAINER_NAME} mkdir -p /tmp/flat_lib/pyfrbus
                        docker exec ${CONTAINER_NAME} cp /source_code/pyfrbus/setup.py /tmp/flat_lib/
                        docker exec ${CONTAINER_NAME} cp -r /source_code/pyfrbus/pyfrbus/. /tmp/flat_lib/pyfrbus/
                        
                        # Perform a standard install (NOT editable)
                        docker exec -w /tmp/flat_lib ${CONTAINER_NAME} python3 -m pip install .
                    """

                    echo "🔧 Safety Check: Verifying Import..."
                    // We will now check where Python is actually looking
                    sh """
                        docker exec ${CONTAINER_NAME} python3 -c "import sys; print('Search Paths:', sys.path); import pyfrbus; print('✅ Package found at:', pyfrbus.__file__)"
                    """

                    sh """
                        docker exec ${CONTAINER_NAME} mkdir -p /home/spark/models /home/spark/data /home/spark/results
                        docker exec ${CONTAINER_NAME} cp /source_code/pyfrbus/models/model.xml /home/spark/models/model.xml
                        docker exec ${CONTAINER_NAME} cp /source_code/data/tealbook_unemployment.csv /home/spark/data/y_unemp.csv
                    """

                    echo "🧪 Running Structural Validation..."
                    sh """
                        docker exec -w /source_code \
                        ${CONTAINER_NAME} python3 -m pytest -vv tests/test_model_load.py
                    """
        
                    echo "🚀 Running Engine..."
                    sh """
                        docker exec -w /home/spark \
                        -e PYTHONPATH=/source_code/src \
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