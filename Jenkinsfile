pipeline {
    agent any

    environment {
        IMAGE_NAME = "macro-engine:${env.BUILD_NUMBER}"
    }

    stages {
        stage('Pre-Flight Cleanup') {
            steps {
                script {
                    echo "🧹 SCORCHED EARTH: Clearing ALL unused Docker images and cache..."
                    // Removes all unused images and volumes to ensure a clean build
                    sh "docker system prune -a -f --volumes || true"
                    
                    echo "📊 Checking available disk space..."
                    sh "df -h /"
                }
            }
        }

        stage('Build & Bake Data') {
            steps {
                sh """
                    # Ensure the base image exists BEFORE we start building
                    docker pull debian:11-slim

                    echo "📂 Verifying context before build..."
                    ls -d data/library.xlsx external_data/longdata.csv
                    
                    echo "🚀 Starting Build ${env.BUILD_NUMBER}..."
                    # --no-cache ensures the Preprocessor runs fresh every time
                    docker build --no-cache -t ${IMAGE_NAME} .
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
                    
                    echo "📥 Extracting artifacts from container..."
                    # Copy final engine results
                    docker cp engine-${env.BUILD_NUMBER}:/home/spark/results/. ./results/
                    
                    # Copy preprocessed CSVs to verify dates and timestamps
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
                
                // Archive both the engine output and our preprocessed debug files
                archiveArtifacts artifacts: 'results/*.csv, debug_data/*.csv', allowEmptyArchive: true
                
                // Remove the specific image to prevent disk bloat
                sh "docker rmi ${IMAGE_NAME} || true"
            }
        }
    }
}