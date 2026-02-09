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
                // Change ownership back to current Jenkins user (not root)
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
                // Now that the Jenkins user owns the files, it can see them
                junit testResults: 'results/test-reports.xml', allowEmptyResults: true
                archiveArtifacts artifacts: 'data/*.csv, results/*.xml', allowEmptyArchive: true
            }
        }
        cleanup {
            echo "🧹 Safely cleaning up workspace..."
            sh "rm -rf data/* results/*"
        }
    }
}