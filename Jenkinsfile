pipeline {
    agent any

    environment {
        IMAGE_NAME = "macro-engine:${env.BUILD_NUMBER}"
    }

    stages {
        stage('Pre-Flight Cleanup') {
            steps {
                script {
                    echo "🧹 Clearing old Docker junk to free up space..."
                    // This clears unused containers, networks, and images
                    // '|| true' ensures the build doesn't fail if there's nothing to clean
                    sh "docker system prune -f || true"
                    sh "docker builder prune -f || true"
                    
                    echo "📊 Checking available disk space..."
                    sh "df -h /var/lib/docker || df -h /"
                }
            }
        }

        stage('Build & Bake Data') {
            steps {
                // Building the image now handles the Preprocessor bake-in
                sh "docker build -t ${IMAGE_NAME} ."
            }
        }

        stage('Run Engine') {
            steps {
                sh """
                    mkdir -p results
                    
                    # Start container (runs the internal CMD: python3 src/engine.py)
                    docker run -d --name engine-${env.BUILD_NUMBER} ${IMAGE_NAME}
                    
                    echo "⏳ Waiting for Engine to solve quarters..."
                    sleep 30
                    
                    echo "📊 --- ENGINE LOGS ---"
                    docker logs engine-${env.BUILD_NUMBER}
                    
                    # Grab the results
                    docker cp engine-${env.BUILD_NUMBER}:/home/spark/results/. ./results/
                """
            }
        }
    }

    post {
        always {
            sh "docker rm -f engine-${env.BUILD_NUMBER} || true"
            archiveArtifacts artifacts: 'results/*.csv', allowEmptyArchive: true
        }
    }
}