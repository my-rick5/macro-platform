pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'macro-engine-local:latest'
    }

    stages {
        stage('Initialize') {
            steps {
                sh """
                    mkdir -p results models data
                    docker ps -a -q --filter ancestor=${DOCKER_IMAGE} | xargs -r docker rm -f
                """
            }
        }

        stage('Fetch Model Logic') {
            steps {
                sh """
                    cp pyfrbus/models/model.xml models/model.xml
                    cp data/tealbook_unemployment.csv data/y_unemp.csv
                """
            }
        }

        stage('Run Engine') {
            steps {
                script {
                    echo "🧪 Running Structural Validation..."
                    
                    // Using $(pwd) inside the shell string is more reliable for 
                    // Docker-in-Docker setups than the Jenkins WORKSPACE variable.
                    sh """
                        docker run --rm --user 0:0 \
                        -v \$(pwd):/workspace \
                        -w /workspace \
                        ${DOCKER_IMAGE} python3 -m pytest tests/test_model_load.py
                    """
        
                    echo "🚀 Running Engine..."
                    sh """
                        docker run --rm \
                        --memory='6g' \
                        -v \$(pwd)/models:/home/spark/models \
                        -v \$(pwd)/data:/home/spark/data \
                        -v \$(pwd)/results:/home/spark/results \
                        -w /home/spark \
                        ${DOCKER_IMAGE} python3 src/engine.py
                    """
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'results/*.csv, models/*.xml', allowEmptyArchive: true
        }
    }
}