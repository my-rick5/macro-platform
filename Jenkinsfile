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
                    sh "docker system prune -a -f --volumes || true"
                    sh "df -h /"
                }
            }
        }

        stage('Build & Bake Data') {
            steps {
                sh """
                    docker pull debian:12-slim
                    echo "📂 Verifying context before build..."
                    ls -d data/library.xlsx external_data/longdata.csv
                    
                    echo "🚀 Starting Build ${env.BUILD_NUMBER}..."
                    docker build --no-cache -t ${IMAGE_NAME} .
                """
            }
        }

        stage('Run Engine') {
            steps {
                sh """
                    mkdir -p results
                    mkdir -p debug_data
                    
                    # 1. Run the container
                    docker run --name engine-${env.BUILD_NUMBER} ${IMAGE_NAME}
                    
                    # 2. Extract Final Results
                    docker cp engine-${env.BUILD_NUMBER}:/home/spark/results/. ./results/
                    
                    # 3. NEW: Extract Preprocessed Data (to verify the 'unemp.csv' timestamps)
                    docker cp engine-${env.BUILD_NUMBER}:/home/spark/external_data/. ./debug_data/
                """
            }
        }
    }

    post {
        always {
            script {
                // Remove the container
                sh "docker rm -f engine-${env.BUILD_NUMBER} || true"
                
                # Archive both the final results and the preprocessed debug files
                archiveArtifacts artifacts: 'results/*.csv, debug_data/*.csv', allowEmptyArchive: true
                
                // Clean up the specific image
                sh "docker rmi ${IMAGE_NAME} || true"
            }
        }
    }
}