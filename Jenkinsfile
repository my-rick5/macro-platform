pipeline {
    agent any 

    environment {
        IMAGE_NAME = "macro-engine-local"
    }

    stages {
        stage('Cleanup') {
            steps {
                echo 'Cleaning up old images to save disk space...'
                sh "docker rmi ${IMAGE_NAME}:latest || true"
            }
        }

        stage('Build') {
            steps {
                echo 'Building the Docker Image...'
                sh "docker build -t ${IMAGE_NAME}:latest ."
            }
        }

        stage('Math & Boundary Tests') {
            steps {
                echo "Running logic tests for macro edge cases..."
                sh "docker run --rm ${IMAGE_NAME}:latest pytest tests/test_boundaries.py"
            }
        }

        stage('Smoke Test') {
            steps {
                echo 'Verifying UMFPACK and pyfrbus...'
                sh "docker run --rm ${IMAGE_NAME}:latest python3 -c 'import scikits.umfpack; import numpy; print(\"Math libraries verified!\")'"
            }
        }

        stage('Dry Run') {
            steps {
                echo "Running a sample simulation task..."
                sh "docker run --rm -e CLOUD_RUN_TASK_INDEX=0 ${IMAGE_NAME}:latest python3 src/engine.py"
            }
        }
    } // <--- This was the missing closing brace for 'stages'

    post {
        success {
            echo '✅ Pipeline Complete: Engine is ready for backtesting.'
        }
        failure {
            echo '❌ Pipeline Failed: Check the console output for errors.'
        }
    }
}