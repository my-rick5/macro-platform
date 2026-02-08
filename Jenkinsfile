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
                // Create results dir and run as current user to avoid Permission Denied
                sh "mkdir -p results"
                sh """
                    docker run --rm \
                    -u \$(id -u):\$(id -g) \
                    -v ${WORKSPACE}/results:/home/spark/results \
                    -e CLOUD_RUN_TASK_INDEX=0 \
                    ${IMAGE_NAME}:latest python3 src/engine.py
                """
            }
        }
    }

    post {
        success {
            echo '✅ Pipeline Complete: Engine is ready for backtesting.'
            // This makes your CSVs downloadable from the Jenkins Build page
            archiveArtifacts artifacts: 'results/*.csv', fingerprint: true
        }
        failure {
            echo '❌ Pipeline Failed: Check the console output for errors.'
        }
    }
}