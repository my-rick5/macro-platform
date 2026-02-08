pipeline {
    agent any 

    environment {
        IMAGE_NAME = "macro-engine-local"
    }

    stages {
        stage('Cleanup') {
            steps {
                echo 'Cleaning up old images to save disk space...'
                // Removes the previous build so your hard drive doesn't fill up
                sh "docker rmi ${IMAGE_NAME}:latest || true"
            }
        }

        stage('Build') {
            steps {
                echo 'Building the Docker Image...'
                // This builds your local engine
                sh "docker build -t ${IMAGE_NAME}:latest ."
            }
        }

        stage('Math & Boundary Tests') {
            steps {
                echo "Running logic tests for macro edge cases..."
                // This runs pytest inside the container we just built
                sh "docker run --rm macro-engine-local:latest pytest tests/test_boundaries.py"
            }
        }

        stage('Smoke Test') {
            steps {
                echo 'Verifying UMFPACK and pyfrbus...'
                // This runs a quick internal check to ensure the math libs are alive
                sh "docker run --rm ${IMAGE_NAME}:latest python3 -c 'import scikits.umfpack; import numpy; print(\"Math libraries verified!\")'"
            }
        }

        stage('Dry Run') {
            steps {
                echo "Running a sample simulation task..."
                sh "docker run --rm -e CLOUD_RUN_TASK_INDEX=0 macro-engine-local:latest python3 src/engine.py"
            }
        }

    post {
        success {
            echo '✅ Pipeline Complete: Engine is ready for backtesting.'
        }
        failure {
            echo '❌ Pipeline Failed: Check the console output for errors.'
        }
    }
}
