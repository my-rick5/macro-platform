pipeline {
    agent any

    environment {
        // PYTHONPATH includes local bin for pip installs and src for module resolution
        PYTHONPATH = "/home/spark/.local/lib/python3.9/site-packages:/home/spark:/home/spark/src"
    }

    stages {
        stage('Initialize') {
            steps {
                echo "🧹 Cleaning workspace and stale containers..."
                // Ensure local results folder exists for the docker cp step later
                sh "mkdir -p results data"
                // || true prevents the build from failing if the container doesn't exist
                sh "docker rm -f engine-run-${env.BUILD_NUMBER} || true"
            }
        }

        stage('Build Image') {
            steps {
                echo "🔨 Building Docker Image (Build #${env.BUILD_NUMBER})..."
                // This uses your multi-stage Dockerfile
                sh "docker build -t macro-engine-image:${env.BUILD_NUMBER} ."
            }
        }

        stage('Run Model Pipeline') {
            steps {
                script {
                    echo "🚀 Starting Isolated Container..."
                    // Detached run to allow multiple exec commands in sequence
                    sh "docker run -d --name engine-run-${env.BUILD_NUMBER} macro-engine-image:${env.BUILD_NUMBER} sleep 600"

                    try {
                        // 1. Ensure the library.xlsx is in the container if not baked into the image
                        echo "📥 Injecting Library Data..."
                        sh "docker cp data/library.xlsx engine-run-${env.BUILD_NUMBER}:/home/spark/data/library.xlsx || echo 'Library already in image'"

                        echo "🔍 STEP 1: Running Preprocessor..."
                        // This generates /home/spark/data/processed/*.csv
                        sh """
                            docker exec -w /home/spark \
                            -e PYTHONPATH=${env.PYTHONPATH} \
                            engine-run-${env.BUILD_NUMBER} \
                            python3 src/preprocess.py
                        """

                        echo "📈 STEP 2: Running Calibration Engine..."
                        // This merges Backbone (external_data) + Targets (data/processed)
                        sh """
                            docker exec -w /home/spark \
                            -e PYTHONPATH=${env.PYTHONPATH} \
                            engine-run-${env.BUILD_NUMBER} \
                            python3 src/engine.py
                        """

                        echo "📥 Extracting Results..."
                        // Pull the solved residuals out of the container for archiving
                        sh "docker cp engine-run-${env.BUILD_NUMBER}:/home/spark/results/. ./results/"

                    } catch (Exception e) {
                        echo "❌ Error during execution: ${e.getMessage()}"
                        currentBuild.result = 'FAILURE'
                        throw e
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                echo "🧹 Final Cleanup..."
                sh "docker rm -f engine-run-${env.BUILD_NUMBER} || true"
            }
            echo "📦 Archiving Results..."
            // allowEmptyArchive: true prevents failure if the engine crashed before saving
            archiveArtifacts artifacts: 'results/*.csv', allowEmptyArchive: true, fingerprint: true
        }
        success {
            echo "🟢 SUCCESS: Build #${env.BUILD_NUMBER} - Residuals generated and archived."
        }
        failure {
            echo "🔴 FAILURE: Build #${env.BUILD_NUMBER}
        }
    }
}



