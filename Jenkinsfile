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
                echo "📡 Downloading directly via Curl..."
                // -L follows redirects, -A mimics Chrome, -o saves the file
                sh """
                    curl -L -k -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36" \
                    -o data/tealbook_raw.xlsx \
                    "https://www.philadelphiafed.org/-/media/frbp/assets/surveys-and-data/tealbook/philadelphia_data_set.xlsx"
                """
                
                echo "🧪 Verifying file type..."
                sh "file data/tealbook_raw.xlsx"

                echo "⚙️ Converting Excel to CSV inside Container..."
                sh """
                    docker run --rm --user 0:0 \
                    -v ${WORKSPACE}/data:/home/spark/data \
                    -v ${WORKSPACE}/results:/home/spark/results \
                    macro-engine-local:latest python3 -c "import pandas as pd; df = pd.read_excel('/home/spark/data/tealbook_raw.xlsx', sheet_name='RUC'); df.to_csv('/home/spark/data/tealbook_unemployment.csv', index=False); print('✅ Conversion Successful')"
                """
                
                // Fix permissions for Jenkins UI
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
            echo "🧹 Workspace cleanup..."
            sh "rm -rf data/* results/*"
        }
    }
}