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
                echo "📦 Injecting Data via Docker CP..."
                
                // 1. Create the container (but don't start it yet)
                sh "docker create --name macro_processor --user 0:0 macro-engine-local:latest"
                
                // 2. Push the Excel file into the container
                sh "docker cp external_data/GBweb_Row_Format.xlsx macro_processor:/tmp/source_data.xlsx"
                
                // 3. Start the container AND run the python command in one go
                // We use 'docker run' with the volume mapped result or 'docker start' with a trick
                // Actually, the simplest 'bulletproof' way is this:
                sh """
                    docker run --rm --user 0:0 \
                    -v ${WORKSPACE}/external_data/GBweb_Row_Format.xlsx:/tmp/source_data.xlsx \
                    -v ${WORKSPACE}/data:/tmp/output_data \
                    macro-engine-local:latest \
                    python3 -c "import pandas as pd; df = pd.read_excel('/tmp/source_data.xlsx', sheet_name='UNEMP'); df.to_csv('/tmp/output_data/tealbook_unemployment.csv', index=False); print('✅ Success: CSV generated')"
                """
                
                // 4. Clean up the manual container from step 1 just in case
                sh "docker rm -f macro_processor || true"
                
                sh "chown -R \$(id -u):\$(id -g) data results || true"
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