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

                    echo "📦 Bridging User Paths & Library Setup..."
                    sh """
                        # 1. Install to ensure all niche dependencies are present
                        docker exec -w /source_code/pyfrbus ${CONTAINER_NAME} python3 -m pip install .
                        
                        # 2. Setup the library home
                        docker exec ${CONTAINER_NAME} mkdir -p /opt/pyfrbus_lib
                        docker exec ${CONTAINER_NAME} cp -r /source_code/pyfrbus/pyfrbus/. /opt/pyfrbus_lib/
                        
                        # 3. Cleanup
                        docker exec ${CONTAINER_NAME} rm -rf /source_code/pyfrbus
                    """

                    // Define the magic path string to avoid repetition
                    def combinedPath = "/opt/pyfrbus_lib:/home/spark/.local/lib/python3.9/site-packages"

                    echo "🔧 Safety Check: Verifying Unified Path..."
                    sh """
                        docker exec -e PYTHONPATH=${combinedPath} \
                        ${CONTAINER_NAME} python3 -c 'import pandas; import frbus; print(\"✅ Unified Path Success!\")'
                    """

                    sh """
                        docker exec ${CONTAINER_NAME} mkdir -p /home/spark/models /home/spark/data /home/spark/results
                        docker exec ${CONTAINER_NAME} cp /opt/pyfrbus_lib/models/model.xml /home/spark/models/model.xml
                        docker exec ${CONTAINER_NAME} cp /source_code/data/tealbook_unemployment.csv /home/spark/data/y_unemp.csv
                        docker exec ${CONTAINER_NAME} chmod -R 777 /home/spark /opt/pyfrbus_lib
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