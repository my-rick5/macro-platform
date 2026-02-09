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
                echo "📦 Injecting Data via Docker CP (No Volumes)..."
                
                // 1. Clean up and create fresh
                sh "docker rm -f macro_processor || true"
                sh "docker create --name macro_processor --user 0:0 macro-engine-local:latest tail -f /dev/null"
                
                // 2. Push the file into the container
                sh "docker cp external_data/GBweb_Row_Format.xlsx macro_processor:/tmp/source_data.xlsx"
                
                // 3. Start it and run the conversion logic
                sh "docker start macro_processor"
                sh """
                    docker exec macro_processor python3 -c "import pandas as pd; df = pd.read_excel('/tmp/source_data.xlsx', sheet_name='UNEMP'); df.to_csv('/tmp/tealbook_unemployment.csv', index=False); print('✅ Success: CSV generated')"
                """
                
                // 4. Pull the result back out to the host
                sh "docker cp macro_processor:/tmp/tealbook_unemployment.csv data/tealbook_unemployment.csv"
                
                // 5. Cleanup
                sh "docker rm -f macro_processor"
                
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