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
                sh "cp external_data/GBweb_Row_Format.xlsx data/tealbook_raw.xlsx"
                
                // Converting UNEMP sheet and ensuring it exists
                sh """
                    docker run --rm --user 0:0 -v ${WORKSPACE}/data:/home/spark/data macro-engine-local:latest \
                    python3 -c "import pandas as pd; df = pd.read_excel('/home/spark/data/tealbook_raw.xlsx', sheet_name='UNEMP'); df.to_csv('/home/spark/data/tealbook_unemployment.csv', index=False)"
                """
                sh "chown -R \$(id -u):\$(id -g) data results || true"
            }
        }
        stage('Run Engine') {
            steps {
                sh "docker run --rm --user 0:0 -v ${WORKSPACE}/data:/home/spark/data -v ${WORKSPACE}/results:/home/spark/results macro-engine-local:latest python3 src/engine.py"
            }
        }
        stage('Unit Tests') {
            steps {
                sh "docker run --rm --user 0:0 -v ${WORKSPACE}/results:/home/spark/results macro-engine-local:latest pytest tests/test_engine.py --junitxml=results/test-reports.xml"
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