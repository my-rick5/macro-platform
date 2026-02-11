pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'macro-engine-local:latest'
        CONTAINER_NAME = "engine-run-${BUILD_NUMBER}"
        COMBINED_PATH = "/opt/macro_platform:/home/spark/.local/lib/python3.9/site-packages"
    }

    stages {
        stage('Initialize') {
            steps {
                sh "mkdir -p results models data"
                sh "docker rm -f ${CONTAINER_NAME} || true"
            }
        }

        stage('Debug File System') {
            steps {
                echo "--- Host View (Jenkins Workspace) ---"
                sh "ls -R"  // Recursively list everything in the workspace
                
                echo "--- Container View ---"
                sh "docker exec engine-run-583 ls -R /home/spark"
            }
        }

        stage('Run Engine') {
            steps {
                script {
                    echo "🧪 Preparing Container & Data..."
                    sh "docker run -d --name ${CONTAINER_NAME} --user 0:0 --entrypoint tail ${DOCKER_IMAGE} -f /dev/null"
                    sh "docker cp . ${CONTAINER_NAME}:/source_code"

                    echo "📦 Precision Namespace Alignment & Package Patching..."
                    sh """
                        docker exec -w /source_code/pyfrbus ${CONTAINER_NAME} python3 -m pip install . psutil openpyxl
                        docker exec ${CONTAINER_NAME} mkdir -p /opt/macro_platform
                        docker exec ${CONTAINER_NAME} cp -r /source_code/pyfrbus/. /opt/macro_platform/
                        docker exec ${CONTAINER_NAME} sed -i 's/data.index, freq=\"Q\"/data.index.astype(str), freq=\"Q\"/g' /opt/macro_platform/pyfrbus/load_data.py
                        
                        # Create directories and move files
                        docker exec ${CONTAINER_NAME} mkdir -p /home/spark/models /home/spark/data/processed /home/spark/results
                        docker exec ${CONTAINER_NAME} cp /source_code/external_data/GBweb_Row_Format.xlsx /home/spark/data/library.xlsx || echo "⚠️ library.xlsx missing"
                        docker exec ${CONTAINER_NAME} cp /opt/macro_platform/models/model.xml /home/spark/models/model.xml
                    """

                    // --- DEBUG SECTION: NOW TRIGGERED AFTER CP COMMANDS ---
                    echo "🔍 Inspecting Container State & XML..."
                    sh "docker exec ${CONTAINER_NAME} ls -R /home/spark/models"
                    sh "docker exec ${CONTAINER_NAME} head -n 20 /home/spark/models/model.xml"
                    sh "docker exec ${CONTAINER_NAME} grep -i 'dmptmax' /home/spark/models/model.xml || echo 'dmptmax string not found'"
                    // -------------------------------------------------------

                    echo "📊 STEP 1: Preprocessing Fed Library..."
                    sh """
                        docker exec -w /home/spark \
                        -e PYTHONPATH=${COMBINED_PATH} \
                        ${CONTAINER_NAME} python3 /source_code/src/preprocess.py
                    """
                    
                    def csvCount = sh(script: "docker exec ${CONTAINER_NAME} ls /home/spark/data/processed | wc -l", returnStdout: true).trim()
                    echo "✅ Preprocessor generated ${csvCount} variables."

                    echo "🚀 STEP 2: Running Structural Engine..."
                    sh """
                        docker exec -w /home/spark \
                        -e PYTHONPATH=${COMBINED_PATH} \
                        ${CONTAINER_NAME} python3 /source_code/src/engine.py
                    """
                    
                    sh "docker cp ${CONTAINER_NAME}:/home/spark/results/. ./results/ || true"
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
        failure {
            echo "🔴 Pipeline Failed. Check the 'Debug' output in the console logs for XML formatting."
        }
    }
}