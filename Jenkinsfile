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

                    echo "📦 Manual Library Deployment..."
                    sh """
                        # Create a permanent system home for the library
                        docker exec ${CONTAINER_NAME} mkdir -p /usr/local/lib/macro_platform
                        
                        # Copy only the internal pyfrbus source folder to the system path
                        # This puts 'frbus.py' at /usr/local/lib/macro_platform/pyfrbus/frbus.py
                        docker exec ${CONTAINER_NAME} cp -r /source_code/pyfrbus/pyfrbus /usr/local/lib/macro_platform/
                        
                        # Remove the source folder from /source_code to prevent ANY shadowing
                        docker exec ${CONTAINER_NAME} rm -rf /source_code/pyfrbus
                    """

                    echo "🔧 Safety Check: Verifying Manual Path..."
                    sh """
                        docker exec -e PYTHONPATH=/usr/local/lib/macro_platform \
                        ${CONTAINER_NAME} python3 -c 'import pyfrbus.frbus; print(\"✅ Manual Import Success!\")'
                    """

                    sh """
                        docker exec ${CONTAINER_NAME} mkdir -p /home/spark/models /home/spark/data /home/spark/results
                        # Source code for the model was in the folder we just deleted, let's restore just the XML
                        docker exec ${CONTAINER_NAME} mkdir -p /source_code/temp_models
                        docker exec ${CONTAINER_NAME} cp /usr/local/lib/macro_platform/pyfrbus/models/model.xml /home/spark/models/model.xml
                        docker exec ${CONTAINER_NAME} cp /source_code/data/tealbook_unemployment.csv /home/spark/data/y_unemp.csv
                    """

                    echo "🧪 Running Structural Validation..."
                    sh """
                        docker exec -w /source_code \
                        -e PYTHONPATH=/usr/local/lib/macro_platform:/source_code \
                        ${CONTAINER_NAME} python3 -m pytest -vv tests/test_model_load.py
                    """
        
                    echo "🚀 Running Engine..."
                    sh """
                        docker exec -w /home/spark \
                        -e PYTHONPATH=/usr/local/lib/macro_platform:/source_code/src \
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