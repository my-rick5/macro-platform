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

                    echo "📦 Precision Namespace Alignment..."
                    sh """
                        # 1. Standard install for dependencies
                        docker exec -w /source_code/pyfrbus ${CONTAINER_NAME} python3 -m pip install .
                        
                        # 2. Setup a clean parent directory
                        docker exec ${CONTAINER_NAME} mkdir -p /opt/macro_platform
                        
                        # 3. Copy the inner package folder to the parent
                        # This creates /opt/macro_platform/pyfrbus/
                        docker exec ${CONTAINER_NAME} cp -r /source_code/pyfrbus/pyfrbus /opt/macro_platform/
                        
                        # 4. Debug: Let's see exactly where things landed
                        echo "--- Container Directory Structure ---"
                        docker exec ${CONTAINER_NAME} ls -d /opt/macro_platform/pyfrbus || echo "❌ Folder missing!"
                        
                        # 5. Cleanup
                        docker exec ${CONTAINER_NAME} rm -rf /source_code/pyfrbus
                    """

                    def combinedPath = "/opt/macro_platform:/home/spark/.local/lib/python3.9/site-packages"

                    echo "🔧 Safety Check: Verifying Package Import..."
                    sh """
                        docker exec -e PYTHONPATH=${combinedPath} \
                        ${CONTAINER_NAME} python3 -c 'import pyfrbus; from pyfrbus import frbus; print(\"✅ Namespace Import Success!\")'
                    """

                    sh """
                        docker exec ${CONTAINER_NAME} mkdir -p /home/spark/models /home/spark/data /home/spark/results
                        # Updated path for model.xml based on the new structure
                        docker exec ${CONTAINER_NAME} cp /opt/macro_platform/pyfrbus/models/model.xml /home/spark/models/model.xml
                        docker exec ${CONTAINER_NAME} cp /source_code/data/tealbook_unemployment.csv /home/spark/data/y_unemp.csv
                        docker exec ${CONTAINER_NAME} chmod -R 777 /home/spark /opt/macro_platform
                    """

                    echo "🧪 Running Structural Validation..."
                    sh """
                        docker exec -w /source_code \
                        -e PYTHONPATH=${combinedPath}:/source_code \
                        ${CONTAINER_NAME} python3 -m pytest -vv tests/test_model_load.py
                    """
        
                    echo "🚀 Running Engine..."
                    sh """
                        docker exec -w /home/spark \
                        -e PYTHONPATH=${combinedPath}:/source_code/src \
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