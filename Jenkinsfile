pipeline {
    agent any

    environment {
        PYTHONPATH = "/home/spark/.local/lib/python3.9/site-packages:/home/spark:/home/spark/src"
    }

    stages {
        stage('Initialize & Prepare Data') {
            steps {
                script {
                    echo "🛠️ Preparing data for Docker build..."
                    // If library doesn't exist, create it from the Tealbook file you ALREADY have
                    sh """
                        if [ ! -f data/library.xlsx ]; then
                            echo '📝 library.xlsx not found, aliasing tealbook_raw.xlsx...'
                            cp data/tealbook_raw.xlsx data/library.xlsx
                        fi
                    """
                }
                sh "mkdir -p results"
                sh "docker rm -f engine-run-${env.BUILD_NUMBER} || true"
            }
        }

        stage('Build Image') {
            steps {
                echo "🔨 Building Docker Image (Build #${env.BUILD_NUMBER})..."
                // If library.xlsx was found, Step 21 will now pass
                sh "docker build -t macro-engine-image:${env.BUILD_NUMBER} ."
            }
        }

        stage('Run Model Pipeline') {
            steps {
                script {
                    echo "🚀 Starting Isolated Container..."
                    sh "docker run -d --name engine-run-${env.BUILD_NUMBER} macro-engine-image:${env.BUILD_NUMBER} sleep 600"

                    try {
                        echo "🧪 STEP 1: Preprocessing..."
                        sh "docker exec -w /home/spark -e PYTHONPATH=${env.PYTHONPATH} engine-run-${env.BUILD_NUMBER} python3 src/preprocess.py"
                        
                        echo "📈 STEP 2: Running Engine..."
                        sh "docker exec -w /home/spark -e PYTHONPATH=${env.PYTHONPATH} engine-run-${env.BUILD_NUMBER} python3 src/engine.py"
                        
                        echo "📥 Extracting Results..."
                        sh "docker cp engine-run-${env.BUILD_NUMBER}:/home/spark/results/. ./results/"
                    } finally {
                        sh "docker rm -f engine-run-${env.BUILD_NUMBER} || true"
                    }
                }
            }
        }
    }

    post {
        always {
            echo "📦 Archiving Results..."
            archiveArtifacts artifacts: 'results/*.csv', allowEmptyArchive: true, fingerprint: true
        }
        success {
            echo "🟢 SUCCESS: Build #${env.BUILD_NUMBER} complete."
        }
        failure {
            echo "🔴 FAILURE: Check the 'Initialize & Search' logs to see if library.xlsx was found."
        }
    }
}