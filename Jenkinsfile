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
                // Ensure we use the 'dataprep' naming in the Dockerfile
                sh "docker build --no-cache -t ${IMAGE_NAME} ."
            }
        }

        stage('Run Engine') {
            steps {
                sh """
                    mkdir -p results
                    docker run -d --name engine-${env.BUILD_NUMBER} ${IMAGE_NAME}
                    
                    echo "⏳ Waiting for Engine to solve..."
                    sleep 30
                    
                    echo "📊 --- ENGINE LOGS ---"
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