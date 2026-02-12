pipeline {
    agent any

    environment {
        // Unique image name based on build number to prevent cache collisions
        IMAGE_NAME = "macro-engine:${env.BUILD_NUMBER}"
    }

    stages {
        stage('Build & Bake Data') {
            steps {
                // The Dockerfile now runs preprocess.py automatically during this step
                sh "docker build -t ${IMAGE_NAME} ."
            }
        }

        stage('Run Engine') {
            steps {
                sh """
                    mkdir -p results
                    docker run -d --name engine-${env.BUILD_NUMBER} ${IMAGE_NAME}
                    
                    echo "⏳ Waiting for Engine to solve..."
                    sleep 30
                    
                    echo "📊 --- ENGINE CONSOLE OUTPUT ---"
                    docker logs engine-${env.BUILD_NUMBER}
                    echo "-------------------------------"
                    
                    docker cp engine-${env.BUILD_NUMBER}:/home/spark/results/. ./results/
                """
            }
        }

    post {
        always {
            // Clean up the container but keep the results
            sh "docker rm -f engine-${env.BUILD_NUMBER} || true"
            
            // Archive the residuals for your review
            archiveArtifacts artifacts: 'results/*.csv', allowEmptyArchive: true
        }
    }
}