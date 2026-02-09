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
                echo "📡 Downloading via Curl with Referer Handshake..."
                sh """
                    curl -L -k \
                    -H "Referer: https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/tealbook-data-set" \
                    -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0" \
                    -o data/tealbook_raw.xlsx \
                    "https://www.philadelphiafed.org/-/media/frbp/assets/surveys-and-data/tealbook/philadelphia_data_set.xlsx"
                """
                
                script {
                    // Fail the build if the file is smaller than 50KB (likely an HTML error page)
                    def fileSize = sh(script: "stat -c%s data/tealbook_raw.xlsx", returnStdout: true).trim().toInteger()
                    if (fileSize < 50000) {
                        error "❌ Downloaded file is only ${fileSize} bytes. The Fed is still blocking us with an HTML page."
                    }
                }

                echo "⚙️ Converting Excel to CSV..."
                sh """
                    docker run --rm --user 0:0 \
                    -v ${WORKSPACE}/data:/home/spark/data \
                    macro-engine-local:latest python3 -c "import pandas as pd; df = pd.read_excel('/home/spark/data/tealbook_raw.xlsx', sheet_name='RUC'); df.to_csv('/home/spark/data/tealbook_unemployment.csv', index=False)"
                """
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
                junit testResults: 'results/*.xml', allowEmptyResults: true
                archiveArtifacts artifacts: 'data/*.csv, results/*.xml', allowEmptyArchive: true
            }
        }
        cleanup {
            sh "rm -rf data/* results/*"
        }
    }
}