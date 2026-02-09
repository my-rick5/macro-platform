pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'macro-engine-local:latest'
    }

    stages {
        stage('Initialize') {
            steps {
                echo "🧹 Targeted cleanup: Only killing macro-engine containers..."
                script {
                    // SAFETY FILTER: This specifically only targets the engine image.
                    // It will NOT see or kill the 'jenkins/jenkins' container.
                    sh "docker ps -a -q --filter ancestor=${DOCKER_IMAGE} | xargs -r docker rm -f"
                    
                    sh "docker volume prune -f --filter 'label!=keep'"
                    sh "mkdir -p ${WORKSPACE}/results ${WORKSPACE}/models"
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
                sh "docker run --rm --user 0:0 -v ${WORKSPACE}:/home/spark ${DOCKER_IMAGE} pytest tests/test_model_load.py"
                
                echo "🚀 Running Engine: Solving for Add Factors (e)..."
                sh """
                    docker run --rm --user 0:0 \
                    --memory='6g' --memory-swap='6g' \
                    -v ${WORKSPACE}/data:/home/spark/data \
                    -v ${WORKSPACE}/results:/home/spark/results \
                    -v ${WORKSPACE}/models:/home/spark/models \
                    ${DOCKER_IMAGE} python3 src/engine.py
                """
            }
        }
    } // End of Stages

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
}