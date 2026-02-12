pipeline {
    agent any

    environment {
        IMAGE_NAME = "macro-engine:${env.BUILD_NUMBER}"
    }

    stages {
        stage('Smart Cleanup') {
            steps {
                script {
                    echo "🧹 SMART CLEANUP: Removing old containers and dangling images..."
                    // Removes stopped containers and 'dangling' images, but KEEPS the base debian image and cache
                    sh "docker container prune -f"
                    sh "docker image prune -f"
                    
                    echo "📊 Checking available disk space..."
                    sh "df -h /"
                }
            }
        }

        stage('Build & Bake Data') {
            steps {
                sh """
                    echo "📂 Verifying context before build..."
                    ls -d data/library.xlsx external_data/longdata.csv
                    
                    echo "🚀 Starting Build ${env.BUILD_NUMBER}..."
                    # Removed --no-cache to allow Docker to reuse compiled layers (like UMFPACK)
                    docker build -t ${IMAGE_NAME} .
                """
            }
        }

        stage('Run Engine') {
            steps {
                sh """
                    mkdir -p results
                    mkdir -p debug_data
                    
                    echo "🏃 Running Engine Container..."
                    docker run --name engine-${env.BUILD_NUMBER} ${IMAGE_NAME}
                    
                    echo "📥 Extracting artifacts..."
                    docker cp engine-${env.BUILD_NUMBER}:/home/spark/results/. ./results/
                    docker cp engine-${env.BUILD_NUMBER}:/home/spark/external_data/. ./debug_data/
                """
            }
        }
    }

    post {
        always {
            script {
                echo "🧹 Post-build cleanup..."
                sh "docker rm -f engine-${env.BUILD_NUMBER} || true"
                
                // Archive artifacts from the successful run
                archiveArtifacts artifacts: 'results/*.csv, debug_data/*.csv', allowEmptyArchive: true
                
                // Optional: keep the last 3 build images, or remove current one
                sh "docker rmi ${IMAGE_NAME} || true"
            }
        }
    }
}