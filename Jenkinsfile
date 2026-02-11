pipeline {
    agent any

    environment {
        PYTHONPATH = "/home/spark:/home/spark/src"
    }

    stages {
        stage('Initialize') {
            steps {
                script {
                    sh "mkdir -p results data data/processed external_data"
                    sh "[ -f data/library.xlsx ] || cp data/tealbook_raw.xlsx data/library.xlsx"
                }
            }
        }

        stage('Build & Run Engine') {
            steps {
                script {
                    sh "docker build -t macro-engine-image:${env.BUILD_NUMBER} ."
                    sh "docker run -d --name engine-${env.BUILD_NUMBER} macro-engine-image:${env.BUILD_NUMBER} sleep 1200"
                    
                    try {
                        echo "⚙️ Running Preprocessor..."
                        sh "docker exec -w /home/spark engine-${env.BUILD_NUMBER} python3 src/preprocess.py"
                        
                        echo "🚀 Heartbeat: Running Full Calibration Engine (init_trac)..."
                        // Run engine but allow failure so we can still run diagnostics
                        sh "docker exec -w /home/spark engine-${env.BUILD_NUMBER} python3 src/engine.py || echo '⚠️ Engine failed, proceeding to diagnostics...'"
                        
                        echo "🔍 DIAGNOSTIC: Inspecting Target CSV Content..."
                        sh """
                        docker exec -w /home/spark engine-${env.BUILD_NUMBER} ls -l data/processed/
                        if docker exec engine-${env.BUILD_NUMBER} [ -f data/processed/adjlegrt.csv ]; then
                            echo "--- Content of adjlegrt.csv ---"
                            docker exec engine-${env.BUILD_NUMBER} cat data/processed/adjlegrt.csv | head -n 10
                            echo "-------------------------------"
                        else
                            echo "❌ ERROR: adjlegrt.csv was NOT created."
                        fi
                        """
                        
                        sh "docker cp engine-${env.BUILD_NUMBER}:/home/spark/results/. ./results/ || true"
                        
                    } finally {
                        sh "docker rm -f engine-${env.BUILD_NUMBER} || true"
                    }
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'results/*', allowEmptyArchive: true
        }
    }
}