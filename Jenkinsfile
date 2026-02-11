pipeline {
    agent any
    stages {
        stage('Initialize') {
            steps {
                sh "mkdir -p results data/processed"
            }
        }
        stage('Run Calibration') {
            steps {
                script {
                    sh "docker build -t macro-engine-image:${env.BUILD_NUMBER} ."
                    sh "docker run -d --name engine-${env.BUILD_NUMBER} macro-engine-image:${env.BUILD_NUMBER} sleep 600"
                    try {
                        echo "🔍 Step 1: Preprocessing Excel..."
                        sh "docker exec engine-${env.BUILD_NUMBER} python3 src/preprocess.py"
                        
                        echo "🚀 Step 2: Running Engine & Scanning for PCE..."
                        // We use a simple sh here; the Python 'print' statements 
                        // will show up in the Jenkins Console Output.
                        sh "docker exec engine-${env.BUILD_NUMBER} python3 src/engine.py"
                        
                        sh "docker cp engine-${env.BUILD_NUMBER}:/home/spark/results/. ./results/"
                    } finally {
                        sh "docker rm -f engine-${env.BUILD_NUMBER}"
                    }
                }
            }
        }
    }
    post {
        always {
            // This ensures we always save whatever residuals were made
            archiveArtifacts artifacts: 'results/*.csv', allowEmptyArchive: true
        }
        failure {
            echo "❌ BUILD FAILED: Check the 'Console Output' above to see the Column List for PCE identification."
        }
    }
}