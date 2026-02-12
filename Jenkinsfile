pipeline {
    agent any

    environment {
        IMAGE_NAME = "macro-engine:${env.BUILD_NUMBER}"
    }

    stages {
        stage('Smart Cleanup') {
            steps {
                script {
                    env.START_TIME = System.currentTimeMillis()
                    echo "🧹 SMART CLEANUP: Pruning dangling objects..."
                    sh "docker container prune -f"
                    sh "docker image prune -f"
                }
            }
        }

        stage('Build & Bake Data') {
            steps {
                script {
                    def buildStart = System.currentTimeMillis()
                    sh "docker build -t ${IMAGE_NAME} ."
                    def buildEnd = System.currentTimeMillis()
                    env.BUILD_TIME = "${((buildEnd - buildStart) / 1000).toString()}s"
                }
            }
        }

        stage('Run Engine') {
            steps {
                sh """
                    mkdir -p results debug_data
                    docker run --name engine-${env.BUILD_NUMBER} ${IMAGE_NAME}
                    docker cp engine-${env.BUILD_NUMBER}:/home/spark/results/. ./results/
                    docker cp engine-${env.BUILD_NUMBER}:/home/spark/external_data/. ./debug_data/
                """
            }
        }
    }

    post {
        always {
            script {
                // Calculate Total Duration
                def totalTimeMs = System.currentTimeMillis() - env.START_TIME.toLong()
                def durationMin = (totalTimeMs / 1000) / 60
                def summary = "Build: ${env.BUILD_TIME} | Total: ${String.format('%.2f', durationMin)}m"
                
                // This puts the timing info directly on the Jenkins Build History sidebar
                currentBuild.description = summary
                
                echo "--------------------------------------------------"
                echo "🏁 FINAL STATS: ${summary}"
                echo "--------------------------------------------------"

                sh "docker rm -f engine-${env.BUILD_NUMBER} || true"
                archiveArtifacts artifacts: 'results/*.csv, debug_data/*.csv', allowEmptyArchive: true
                sh "docker rmi ${IMAGE_NAME} || true"
            }
        }
    }
}