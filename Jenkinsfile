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
                sh "docker rm -f ${CONTAINER_NAME} || true"
            }
        }

        stage('Run Engine') {
            steps {
                script {
                    echo "🧪 Preparing Container & Data..."
                    sh "docker run -d --name ${CONTAINER_NAME} --user 0:0 --entrypoint tail ${DOCKER_IMAGE} -f /dev/null"
                    sh "docker cp . ${CONTAINER_NAME}:/source_code"

                    echo "📦 Precision Namespace Alignment & Asset Preservation..."
                    sh """
                        # 1. Standard install + explicitly add missing engine dependencies
                        docker exec -w /source_code/pyfrbus ${CONTAINER_NAME} python3 -m pip install . psutil
                        
                        # 2. Move code and models to /opt
                        docker exec ${CONTAINER_NAME} mkdir -p /opt/macro_platform
                        docker exec ${CONTAINER_NAME} cp -r /source_code/pyfrbus/. /opt/macro_platform/
                        
                        # 3. Initialize Spark directories
                        docker exec ${CONTAINER_NAME} mkdir -p /home/spark/models /home/spark/data /home/spark/results
                        
                        # 4. Copy data
                        docker exec ${CONTAINER_NAME} cp /source_code/data/tealbook_unemployment.csv /home/spark/data/y_unemp.csv || \
                        docker exec ${CONTAINER_NAME} cp /source_code/pyfrbus/data/tealbook_unemployment.csv /home/spark/data/y_unemp.csv
                        
                        # 5. Copy model from preserved /opt location
                        docker exec ${CONTAINER_NAME} cp /opt/macro_platform/models/model.xml /home/spark/models/model.xml
                        
                        # 6. Cleanup temporary source folders
                        docker exec ${CONTAINER_NAME} rm -rf /home/spark/pyfrbus
                        docker exec ${CONTAINER_NAME} rm -rf /source_code/pyfrbus
                    """

                    def combinedPath = "/opt/macro_platform:/home/spark/.local/lib/python3.9/site-packages"

                    echo "🔧 Safety Check: Verifying Package Import..."
                    sh "docker exec -e PYTHONPATH=${combinedPath} ${CONTAINER_NAME} python3 -c 'import pyfrbus; from pyfrbus import frbus; print(\"✅ Namespace Import Success!\")'"

                    echo "🧪 Running Structural Validation (Checking endo_names)..."
                    sh """
                        docker exec -e PYTHONPATH=${combinedPath} ${CONTAINER_NAME} \
                        python3 -c "from pyfrbus.frbus import Frbus; m = Frbus('/home/spark/models/model.xml'); print('MODEL ENDO VARS:', m.endo_names[:10], '...')"
                    """

                    echo "🚀 Running Engine..."
                    sh """
                        docker exec -w /home/spark \
                        -e PYTHONPATH=${combinedPath} \
                        ${CONTAINER_NAME} python3 /source_code/src/engine.py
                    """
                    
                    sh "docker cp ${CONTAINER_NAME}:/home/spark/results/. ./results/"
                }
            }
        }
    }

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
}