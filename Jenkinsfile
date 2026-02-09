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
                sh "docker run --rm --user 0:0 -v ${WORKSPACE}/data:/home/spark/data -v ${WORKSPACE}/results:/home/spark/results macro-engine-local:latest python3 src/fetch_tealbook.py"
                // FIX: Give files back to Jenkins user so it can archive them
                sh "sudo chown -R \$(id -u):\$(id -g) data results"
            }
        }
        stage('Unit Tests') {
            steps {
                sh "docker run --rm --user 0:0 -v ${WORKSPACE}/results:/home/spark/results macro-engine-local:latest pytest tests/ --junitxml=results/test-reports.xml"
                sh "sudo chown -R \$(id -u):\$(id -g) results"
            }
        }
    }
    post {
        success {
            script {
                // Archive using exact relative paths
                junit testResults: 'results/test-reports.xml', allowEmptyResults: true
                archiveArtifacts artifacts: 'data/tealbook_unemployment.csv, results/test-reports.xml', allowEmptyArchive: true
            }
        }
        cleanup {
            echo "🧹 Safely cleaning up workspace..."
            sh "rm -rf data/* results/*"
        }
    }
}