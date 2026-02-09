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

                    echo "📦 Installing & De-conflicting..."
                    sh """
                        # Install the package formally
                        docker exec -w /source_code/pyfrbus ${CONTAINER_NAME} python3 -m pip install .
                        
                        # RENAME the repo folder to prevent shadowing/confusion
                        docker exec ${CONTAINER_NAME} mv /source_code/pyfrbus /source_code/pyfrbus_repo_folder
                    """

                    echo "🔧 Safety Check: Verifying Global Import..."
                    sh "docker exec ${CONTAINER_NAME} python3 -c 'import pyfrbus.frbus; print(\"✅ Global Import Success!\")'"

                    sh """
                        docker exec ${CONTAINER_NAME} mkdir -p /home/spark/models /home/spark/data /home/spark/results
                        # Note the new path for the model file
                        docker exec ${CONTAINER_NAME} cp /source_code/pyfrbus_repo_folder/models/model.xml /home/spark/models/model.xml
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