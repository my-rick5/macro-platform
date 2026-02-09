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
                echo "📦 Injecting Row Format Excel..."
                // Copy the file
                sh "cp external_data/GBweb_Row_Format.xlsx data/tealbook_raw.xlsx"
                
                // CRITICAL: Ensure permissions allow the Docker daemon to read it
                sh "chmod 644 data/tealbook_raw.xlsx"

                echo "⚙️ Converting 'UNEMP' sheet to CSV..."
                sh """
                    docker run --rm --user 0:0 \
                    -v ${WORKSPACE}/data:/home/spark/data \
                    macro-engine-local:latest \
                    python3 -c "import pandas as pd; import os; print(f'Directory content: {os.listdir(\"/home/spark/data\")}'); df = pd.read_excel('/home/spark/data/tealbook_raw.xlsx', sheet_name='UNEMP'); df.to_csv('/home/spark/data/tealbook_unemployment.csv', index=False)"
                """
                
                // Fix ownership so Jenkins can archive it
                sh "chown -R \$(id -u):\$(id -g) data results || true"
            }
        }
        stage('Run Engine') {
            steps {
                sh """
                    docker run --rm --user 0:0 \
                    -v ${WORKSPACE}/data:/home/spark/data \
                    -v ${WORKSPACE}/results:/home/spark/results \
                    macro-engine-local:latest python3 src/engine.py
                """
                sh "chown -R \$(id -u):\$(id -g) results || true"
            }
        }
    }
    post {
        always {
            junit testResults: 'results/*.xml', allowEmptyResults: true
            archiveArtifacts artifacts: 'results/*.csv, data/*.csv', allowEmptyArchive: true
        }
    }
}