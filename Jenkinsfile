pipeline {
    agent any

    environment {
        // We use the internal container path for PYTHONPATH
        PYTHONPATH = "/home/spark/.local/lib/python3.9/site-packages:/home/spark/src"
    }

    stages {
        stage('Initialize') {
            steps {
                // Cleanup any stale containers from this build number
                sh "docker rm -f engine-run-${env.BUILD_NUMBER} || true"
            }
        }

        stage('Build Image') {
            steps {
                echo "🔨 Building Image (including external_data and src)..."
                sh "docker build -t macro-engine-image:${env.BUILD_NUMBER} ."
            }
        }

        stage('Debug & Run') {
            steps {
                // 1. Start the container WITHOUT the -v mount. 
                // This forces it to use the files INSIDE the image.
                sh "docker run -d --name engine-run-${env.BUILD_NUMBER} macro-engine-image:${env.BUILD_NUMBER} sleep 300"
                
                echo "--- Internal Container View ---"
                sh "docker exec engine-run-${env.BUILD_NUMBER} ls -R /home/spark"
                
                echo "🚀 Running Model Calibration..."
                // Execute the engine using the internal path
                sh "docker exec -w /home/spark -e PYTHONPATH=${env.PYTHONPATH} engine-run-${env.BUILD_NUMBER} python3 src/engine.py"
                
                echo "📥 Extracting Results from Container..."
                // Since we aren't mounting a volume, we must manually copy the results out to the Jenkins host
                sh "mkdir -p results"
                sh "docker cp engine-run-${env.BUILD_NUMBER}:/home/spark/results/. ./results/"
            }
        }
    }

    post {
        always {
            script {
                echo "🧹 Cleaning up container..."
                sh "docker rm -f engine-run-${env.BUILD_NUMBER} || true"
            }
            echo "📦 Archiving Results..."
            archiveArtifacts artifacts: 'results/*.csv', allowEmptyArchive: true
        }
        success {
            echo "🟢 Calibration Successful!"
        }
        failure {
            echo "🔴 Pipeline Failed. If 'external_data' is missing above, check Dockerfile COPY."
        }
    }
}