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

                    echo "📦 Final Structural Alignment..."
                    sh """
                        # Create the library home
                        docker exec ${CONTAINER_NAME} mkdir -p /opt/macro_platform
                        
                        # Move the MIDDLE pyfrbus folder (the one containing the actual code) 
                        # to the library home.
                        # This makes /opt/macro_platform/pyfrbus the package root.
                        docker exec ${CONTAINER_NAME} cp -r /source_code/pyfrbus/pyfrbus /opt/macro_platform/
                        
                        # Remove the messy source folder
                        docker exec ${CONTAINER_NAME} rm -rf /source_code/pyfrbus
                    """

                    echo "🔧 Safety Check: Verifying Global Import..."
                    # We point PYTHONPATH to /opt/macro_platform. 
                    # Python will find the 'pyfrbus' folder inside it and treat it as a package.
                    sh """
                        docker exec -e PYTHONPATH=/opt/macro_platform \
                        ${CONTAINER_NAME} python3 -c 'import pyfrbus.frbus; print(\"✅ Global Import Success!\")'
                    """

                    sh """
                        docker exec ${CONTAINER_NAME} mkdir -p /home/spark/models /home/spark/data /home/spark/results
                        # The model.xml was in the top-level repo folder which we just deleted, 
                        # but it's also inside the inner package structure.
                        docker exec ${CONTAINER_NAME} cp /opt/macro_platform/pyfrbus/models/model.xml /home/spark/models/model.xml
                        docker exec ${CONTAINER_NAME} cp /source_code/data/tealbook_unemployment.csv /home/spark/data/y_unemp.csv
                    """

                    echo "🧪 Running Structural Validation..."
                    sh """
                        docker exec -w /source_code \
                        -e PYTHONPATH=/opt/macro_platform:/source_code \
                        ${CONTAINER_NAME} python3 -m pytest -vv tests/test_model_load.py
                    """
        
                    echo "🚀 Running Engine..."
                    sh """
                        docker exec -w /home/spark \
                        -e PYTHONPATH=/opt/macro_platform:/source_code/src \
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