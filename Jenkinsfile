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
                    // Mounts the whole workspace so pytest can see everything
                    sh """
                        docker run --rm \
                        -v ${hostPath}:/workspace \
                        -w /workspace \
                        ${DOCKER_IMAGE} python3 -m pytest tests/test_model_load.py
                    """
        
                    echo "🚀 Running Engine..."
                    // Selective mounts to avoid overwriting /home/spark/.local
                    sh """
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