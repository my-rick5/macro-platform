pipeline {
    agent any
    stages {
        stage('Initialize') {
            steps {
                echo "🧹 Cleaning workspace and removing ghost directories..."
                // Nuke the data/ folder to get rid of that 'pdfs' ghost folder
                sh "rm -rf data results"
                sh "mkdir -p results data && chmod 777 results data"
            }
        }
        stage('Process Data') {
            steps {
                echo "📦 Injecting Row Format Excel..."
                // Copy from the repo to our fresh data folder
                sh "cp external_data/GBweb_Row_Format.xlsx data/tealbook_raw.xlsx"
                sh "chmod 644 data/tealbook_raw.xlsx"

                echo "⚙️ Converting 'UNEMP' sheet to CSV..."
                // Mount the file DIRECTLY to the container root to bypass folder-mount bugs
                sh """
                    docker run --rm --user 0:0 \
                    -v ${WORKSPACE}/data/tealbook_raw.xlsx:/home/spark/tealbook_raw.xlsx \
                    -v ${WORKSPACE}/data:/home/spark/data \
                    macro-engine-local:latest \
                    python3 -c "import pandas as pd; df = pd.read_excel('/home/spark/tealbook_raw.xlsx', sheet_name='UNEMP'); df.to_csv('/home/spark/data/tealbook_unemployment.csv', index=False); print('✅ Success: CSV generated')"
                """
                sh "chown -R \$(id -u):\$(id -g) data results || true"
            }
        }
        stage('Run Engine') {
            steps {
                echo "🚀 Running Macro Engine..."
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
            archiveArtifacts artifacts: 'data/*.csv, results/*.csv', allowEmptyArchive: true
        }
    }
}