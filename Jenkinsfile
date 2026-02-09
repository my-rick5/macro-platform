pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'macro-engine-local:latest'
    }

    stages {
        stage('Initialize') {
            steps {
                echo "🧹 Prepping Host Directories & Debugging Layout..."
                sh """
                    mkdir -p results models data
                    echo "--- Workspace Tree ---"
                    ls -R
                    docker ps -a -q --filter ancestor=${DOCKER_IMAGE} | xargs -r docker rm -f
                """
            }
        }

        stage('Fetch Model Logic') {
            steps {
                echo "🧠 Preparing model.xml..."
                // Ensures the model is in the folder we are about to mount
                sh "cp pyfrbus/models/model.xml models/model.xml"
            }
        }

        stage('Run Engine') {
            steps {
                script {
                    def hostPath = WORKSPACE 
                    
                    echo "🧪 Running Structural Validation..."
                    // Added --user 0:0 to fix the Permission Denied/Errno 13 issue
                    sh """
                        docker run --rm --user 0:0 \
                        -v ${hostPath}:/workspace \
                        -w /workspace \
                        ${DOCKER_IMAGE} python3 -m pytest /workspace/tests/test_model_load.py
                    """
        
                    echo "🚀 Running Engine..."
                    // The engine runs as the default 'spark' user 
                    // We also ensure the data file name matches your engine.py (y_unemp.csv)
                    sh """
                        cp data/tealbook_unemployment.csv data/y_unemp.csv
                        
                        docker run --rm \
                        --memory='6g' \
                        -v ${hostPath}/models:/home/spark/models \
                        -v ${hostPath}/data:/home/spark/data \
                        -v ${hostPath}/results:/home/spark/results \
                        -w /home/spark \
                        ${DOCKER_IMAGE} python3 src/engine.py
                    """
                }
            }
        }
    } // <--- Added missing closing brace for stages

    post {
        always {
            echo "📦 Archiving Results..."
            archiveArtifacts artifacts: 'results/*.csv, models/*.xml', allowEmptyArchive: true
        }
    }
} // <--- Added missing closing brace for pipeline