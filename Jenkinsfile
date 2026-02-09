pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'macro-engine-local:latest'
    }

    stages {
        stage('Initialize') {
            steps {
                echo "🧹 Targeted cleanup..."
                script {
                    sh "docker ps -a -q --filter ancestor=${DOCKER_IMAGE} | xargs -r docker rm -f"
                    sh "mkdir -p results models"
                }
            }
        }

        stage('Fetch Model Logic') {
            steps {
                echo "🧠 Isolating model.xml..."
                // Based on your tree: pyfrbus/models/model.xml exists
                sh "cp pyfrbus/models/model.xml ./model.xml"
            }
        }

        stage('Run Engine') {
            steps {
                echo "🧪 Running Structural Validation..."
                sh """
                    docker run --rm --user 0:0 \
                    -v ${WORKSPACE}:/home/spark \
                    -w /home/spark \
                    ${DOCKER_IMAGE} bash -c 'ls -R && pip install pytest && python3 -m pytest tests/test_model_load.py'
                """
                
                echo "🚀 Running Engine: Solving for Add Factors (e)..."
                sh """
                    docker run --rm --user 0:0 \
                    --memory='6g' --memory-swap='6g' \
                    -v ${WORKSPACE}:/home/spark \
                    -w /home/spark \
                    ${DOCKER_IMAGE} python3 src/engine.py
                """
            }
        }
    }

    post {
        always {
            echo "📦 Archiving Build Artifacts..."
            archiveArtifacts artifacts: 'results/*.csv, models/*.xml', allowEmptyArchive: true
        }
    }
}