pipeline {
    agent any
    stages {
        stage('Initialize') {
            steps {
                echo "🧹 Deep cleaning workspace and resetting Docker volumes..."
                // Use a fresh directory name to bypass any Docker cache issues
                sh "rm -rf ${WORKSPACE}/processing_zone ${WORKSPACE}/results"
                sh "mkdir -p ${WORKSPACE}/results ${WORKSPACE}/processing_zone"
                sh "chmod 777 ${WORKSPACE}/results ${WORKSPACE}/processing_zone"
            }
        }
        stage('Process Data') {
            steps {
                echo "📦 Injecting Row Format Excel..."
                // Rename the destination file slightly to force a fresh file handle
                sh "cp ${WORKSPACE}/external_data/GBweb_Row_Format.xlsx ${WORKSPACE}/processing_zone/source_data.xlsx"
                sh "chmod 664 ${WORKSPACE}/processing_zone/source_data.xlsx"

                echo "⚙️ Converting 'UNEMP' sheet to CSV..."
                sh """
                    docker run --rm --user 0:0 \
                    -v ${WORKSPACE}/processing_zone:/home/spark/data \
                    macro-engine-local:latest \
                    python3 -c "import pandas as pd; df = pd.read_excel('/home/spark/data/source_data.xlsx', sheet_name='UNEMP'); df.to_csv('/home/spark/data/tealbook_unemployment.csv', index=False); print('✅ Success: CSV generated')"
                """
                sh "chown -R \$(id -u):\$(id -g) ${WORKSPACE}/processing_zone ${WORKSPACE}/results || true"
            }
        }
        stage('Run Engine') {
            steps {
                // Update engine to look in the new directory
                sh """
                    docker run --rm --user 0:0 \
                    -v ${WORKSPACE}/processing_zone:/home/spark/data \
                    -v ${WORKSPACE}/results:/home/spark/results \
                    macro-engine-local:latest python3 src/engine.py
                """
                sh "chown -R \$(id -u):\$(id -g) ${WORKSPACE}/results || true"
            }
        }
    }
    post {
        always {
            // Archive from the new directory name
            archiveArtifacts artifacts: 'processing_zone/*.csv, results/*.csv', allowEmptyArchive: true
        }
    }
}