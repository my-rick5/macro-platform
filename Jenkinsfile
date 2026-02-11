pipeline {
    agent any

    environment {
        // Internal container path for dependencies and source code
        PYTHONPATH = "/home/spark/.local/lib/python3.9/site-packages:/home/spark:/home/spark/src"
    }

    stages {
        stage('Initialize') {
            steps {
                echo "🧹 Cleaning workspace and stale containers..."
                // ONLY create results. Git provides the 'data' folder.
                sh "mkdir -p results"
                sh "docker rm -f engine-run-${env.BUILD_NUMBER} || true"
            }
        }

        stage('Build Image') {
            steps {
                echo "🔨 Building Docker Image (Build #${env.BUILD_NUMBER})..."
                sh "docker build -t macro-engine-image:${env.BUILD_NUMBER} ."
            }
        }

        stage('Run Model Pipeline') {
            steps {
                script {
                    echo "🚀 Starting Isolated Container..."
                    sh "docker run -d --name engine-run-${env.BUILD_NUMBER} macro-engine-image:${env.BUILD_NUMBER} sleep 600"

                    try {
                        echo "🔍 STEP 1: Running Preprocessor..."
                        // This uses library.xlsx already baked into the image at Step 21
                        sh """
                            docker exec -w /home/spark \
                            -e PYTHONPATH=${env.PYTHONPATH} \
                            engine-run-${env.BUILD_NUMBER} \
                            python3 src/preprocess.py
                        """

                        echo "📈 STEP 2: Running Calibration Engine..."
                        sh """
                            docker exec -w /home/spark \
                            -e PYTHONPATH=${env.PYTHONPATH} \
                            engine-run-${env.BUILD_NUMBER} \
                            python3 src/engine.py
                        """

                        echo "📥 Extracting Results..."
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
            archiveArtifacts artifacts: 'results/*.csv', allowEmptyArchive: true, fingerprint: true
        }
        success {
            echo "🟢 SUCCESS: Build #${env.BUILD_NUMBER} - Residuals generated and archived."
        }
        failure {
            echo "🔴 FAILURE: Build #${env.BUILD_NUMBER} - Check Step 21 in the Docker build logs."
        }
    }
}