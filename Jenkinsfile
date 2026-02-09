pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'macro-engine-local:latest'
    }

    stages {
        stage('Initialize') {
            steps {
                echo "🧹 Performing a deep clean for Build #53..."
                script {
                    // Remove existing containers and prune volumes to ensure a clean room
                    sh "docker ps -a -q -f status=exited -f status=running | xargs -r docker rm -f"
                    sh "docker volume prune -f"
                    
                    // Recreate workspace directories
                    sh "rm -rf ${WORKSPACE}/data ${WORKSPACE}/results ${WORKSPACE}/models ${WORKSPACE}/external_data"
                    sh "mkdir -p ${WORKSPACE}/data ${WORKSPACE}/results ${WORKSPACE}/models ${WORKSPACE}/external_data"
                    sh "chmod -R 777 ${WORKSPACE}/data ${WORKSPACE}/results ${WORKSPACE}/models"
                }
            }
        }

        stage('Fetch Model Logic') {
            steps {
                echo "🧠 Fetching official FRB/US model equations (model.xml)..."
                script {
                    sh "curl -L -o frbus_python.zip 'https://www.federalreserve.gov/econres/files/frbus_py.zip'"
                    sh "unzip -o frbus_python.zip 'models/model.xml' -d ./"
                    sh "rm frbus_python.zip"
                }
            }
        }

        stage('Run Engine') {
            steps {
                echo "🧪 Running Structural Validation..."
                // Validate the XML before starting the heavy simulation
                sh "docker run --rm --user 0:0 -v ${WORKSPACE}:/home/spark ${DOCKER_IMAGE} pytest tests/test_model_load.py"
                
                echo "🚀 Running Engine: Solving for Add Factors (e)..."
                sh """
                    docker run --rm --user 0:0 \
                    --memory='4g' --memory-swap='4g' \
                    -v ${WORKSPACE}/data:/home/spark/data \
                    -v ${WORKSPACE}/results:/home/spark/results \
                    -v ${WORKSPACE}/models:/home/spark/models \
                    ${DOCKER_IMAGE} python3 src/engine.py
                """
            }
        }
    }

    post {
        always {
            echo "📦 Archiving Build Artifacts..."
            archiveArtifacts artifacts: 'results/*.csv, data/*.csv, test-reports/*.xml', 
                             fingerprint: true, 
                             allowEmptyArchive: false
        }
        success {
            echo "✅ Build Successful: Structural residuals isolated."
        }
        failure {
            echo "❌ Build Failed. Check console for SolverStalled or Hardware Guard errors."
        }
    }
} // This is the final brace that was missing in build #54