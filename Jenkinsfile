pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'macro-engine-local:latest'
    }

    stages {
        stage('Initialize') {
            steps {
                echo "🧹 Prepping Directories..."
                sh """
                    mkdir -p results models data
                    docker ps -a -q --filter ancestor=${DOCKER_IMAGE} | xargs -r docker rm -f
                """
            }
        }

        stage('Fetch Model Logic') {
            steps {
                echo "🧠 Syncing Model & Data..."
                sh """
                    cp pyfrbus/models/model.xml models/model.xml
                    cp data/tealbook_unemployment.csv data/y_unemp.csv
                """
            }
        }

        stage('Run Engine') {
            steps {
                script {
                    def hostPath = WORKSPACE 
                    
                    echo "🧪 Running Structural Validation..."
                    sh """
                        docker run --rm --user 0:0 \
                        -v ${hostPath}:/workspace \
                        -w /workspace \
                        ${DOCKER_IMAGE} bash -c '
                            echo "👤 User: \$(whoami)" && \
                            echo "📍 Dir: \$(pwd)" && \
                            echo "📂 Files in tests/:" && ls -l tests/ && \
                            python3 -m pytest tests/test_model_load.py
                        '
                    """
        
                    echo "🚀 Running Engine..."
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
    }

    post {
        always {
            echo "📦 Archiving Results..."
            archiveArtifacts artifacts: 'results/*.csv, models/*.xml', allowEmptyArchive: true
        }
    }
}