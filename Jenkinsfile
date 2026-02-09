pipeline {
    agent any
    stages {
        stage('Initialize') {
            steps {
                echo "🧹 Deep cleaning workspace..."
                sh "rm -rf ${WORKSPACE}/data ${WORKSPACE}/results"
                sh "mkdir -p ${WORKSPACE}/results ${WORKSPACE}/data"
                // Ensure the directory is wide open for the Docker user
                sh "chmod 777 ${WORKSPACE}/results ${WORKSPACE}/data"
            }
        }
        stage('Process Data') {
            steps {
                echo "📦 Injecting Row Format Excel..."
                // Copy the file into our clean data directory
                sh "cp ${WORKSPACE}/external_data/GBweb_Row_Format.xlsx ${WORKSPACE}/data/tealbook_raw.xlsx"
                sh "chmod 664 ${WORKSPACE}/data/tealbook_raw.xlsx"

                echo "⚙️ Converting 'UNEMP' sheet to CSV..."
                sh """
                    docker run --rm --user 0:0 \
                    -v ${WORKSPACE}/data:/home/spark/data \
                    macro-engine-local:latest \
                    python3 -c "import pandas as pd; df = pd.read_excel('/home/spark/data/tealbook_raw.xlsx', sheet_name='UNEMP'); df.to_csv('/home/spark/data/tealbook_unemployment.csv', index=False); print('✅ Success: CSV generated')"
                """
                sh "chown -R \$(id -u):\$(id -g) ${WORKSPACE}/data ${WORKSPACE}/results || true"
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
                sh "chown -R \$(id -u):\$(id -g) ${WORKSPACE}/results || true"
            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: 'data/*.csv, results/*.csv', allowEmptyArchive: true
        }
    }
}