pipeline {
    agent any
    stages {
        stage('Initialize') {
            steps {
                sh "mkdir -p results data && chmod 777 results data"
                sh "rm -f results/* data/*"
            }
        }
        stage('Process Data') {
            steps {
                // Run as root (0:0) to write to host volumes
                sh "docker run --rm --user 0:0 -v ${WORKSPACE}/data:/home/spark/data -v ${WORKSPACE}/results:/home/spark/results macro-engine-local:latest python3 src/fetch_tealbook.py"
                
                // Fix permissions WITHOUT sudo (Jenkins is usually root or has docker group access)
                sh "chown -R \$(id -u):\$(id -g) data results || true"
            }
        }
        stage('Unit Tests') {
            steps {
                sh "docker run --rm --user 0:0 -v ${WORKSPACE}/results:/home/spark/results macro-engine-local:latest pytest tests/ --junitxml=results/test-reports.xml"
                sh "chown -R \$(id -u):\$(id -g) results || true"
            }
        }
    }
    post {
        always {
            script {
                // Check if files exist before trying to archive to avoid 'match nothing' errors
                junit testResults: 'results/*.xml', allowEmptyResults: true
                archiveArtifacts artifacts: 'data/*.csv, results/*.xml', allowEmptyArchive: true
            }
        }
        cleanup {
            echo "🧹 Safely cleaning up workspace..."
            sh "rm -rf data/* results/*"
        }
    }
}