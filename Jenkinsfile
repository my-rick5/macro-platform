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
                    // '-a' removes all unused images, not just dangling ones
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
                    docker pull debian:12-slim

                    echo "📂 Verifying context before build..."
                    ls -d data/library.xlsx external_data/longdata.csv
                    
                    echo "🚀 Starting Build #748 (Legacy Mode)..."
                    # Removed --progress=plain for compatibility
                    docker build --no-cache -t ${IMAGE_NAME} .
                """
            }
        }

        stage('Run Engine') {
            steps {
                sh """
                    mkdir -p results
                    # DEBUG: List exactly what is inside the data folders in the image
                    docker run --rm ${IMAGE_NAME} ls -R /home/spark/external_data
                    
                    docker run --name engine-${env.BUILD_NUMBER} ${IMAGE_NAME}
                    sleep 30
                    docker logs engine-${env.BUILD_NUMBER}
                    docker cp engine-${env.BUILD_NUMBER}:/home/spark/results/. ./results/
                """
            }
        }
    }

    post {
        always {
            sh "docker rm -f engine-${env.BUILD_NUMBER} || true"
            archiveArtifacts artifacts: 'results/*.csv', allowEmptyArchive: true
            
            // Clean up the specific image we just built to save space for the NEXT run
            sh "docker rmi ${IMAGE_NAME} || true"
        }
    }
}