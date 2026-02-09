pipeline {
    agent any
    stages {
        stage('Initialize') {
            steps {
                echo "🧹 Performing a deep clean for Build #53..."
                script {
                    // 1. Remove any containers still running or exited from previous builds
                    sh "docker ps -a -q -f status=exited -f status=running | xargs -r docker rm -f"
                    
                    // 2. Prune dangling volumes (The most common cause of path conflicts)
                    sh "docker volume prune -f"
                    
                    // 3. Clear out the workspace folders
                    sh "rm -rf ${WORKSPACE}/data ${WORKSPACE}/results ${WORKSPACE}/models ${WORKSPACE}/external_data"
                    sh "mkdir -p ${WORKSPACE}/data ${WORKSPACE}/results ${WORKSPACE}/models ${WORKSPACE}/external_data"
                    
                    // 4. Ensure permissions are wide open for Docker mounting
                    sh "chmod -R 777 ${WORKSPACE}/data ${WORKSPACE}/results ${WORKSPACE}/models"
                }
            }
        }

        stage('Fetch X & Y Data') {
            steps {
                echo "📡 Fetching Definitive X (Structural) and Y (Projections)..."
                dir('external_data') {
                    // Y: Tealbook Unemployment
                    sh "curl -L -o tealbook_unemp.xlsx 'https://www.philadelphiafed.org/-/media/frbp/assets/surveys-and-data/real-time-data-research/philadelphia-data-set/unemp_row_format.xlsx'"
                    
                    // X1: Output Gap (The core driver of the structural model)
                    sh "curl -L -o output_gap.xlsx 'https://www.philadelphiafed.org/-/media/frbp/assets/surveys-and-data/real-time-data-research/gap-and-financial-data-set/gap_vintages.xlsx'"
                    
                    // X2: Financial Assumptions (Rates & Equities)
                    sh "curl -L -o financial_assumptions.xlsx 'https://www.philadelphiafed.org/-/media/frbp/assets/surveys-and-data/real-time-data-research/gap-and-financial-data-set/financial_assumptions_rates_equity.xlsx'"
                }
            }
        }

        stage('Fetch Model Logic') {
            steps {
                echo "🧠 Fetching official FRB/US model equations (model.xml)..."
                // Downloading the Python version of the model package
                sh "curl -L -o frbus_python.zip 'https://www.federalreserve.gov/econres/files/frbus_py.zip'"
                sh "unzip -o frbus_python.zip 'models/model.xml' -d ./"
                sh "rm frbus_python.zip"
            }
        }

        stage('Process Data') {
            steps {
                echo "📦 Converting Excel X/Y matrices to CSV via Docker..."
                
                sh "docker create --name macro_processor --user 0:0 macro-engine-local:latest tail -f /dev/null"
                sh "docker start macro_processor"
                
                // Inject all three definitive files
                sh "docker cp external_data/tealbook_unemp.xlsx macro_processor:/tmp/y_unemp.xlsx"
                sh "docker cp external_data/output_gap.xlsx macro_processor:/tmp/x_gap.xlsx"
                sh "docker cp external_data/financial_assumptions.xlsx macro_processor:/tmp/x_fin.xlsx"
                
                // Multi-file conversion logic
                sh """
                    docker exec macro_processor python3 -c "
import pandas as pd
# Process Y (Unemployment)
pd.read_excel('/tmp/y_unemp.xlsx', sheet_name='UNEMP').to_csv('/tmp/y_unemp.csv', index=False)
# Process X1 (Output Gap)
pd.read_excel('/tmp/x_gap.xlsx').to_csv('/tmp/x_gap.csv', index=False)
# Process X2 (Financials)
pd.read_excel('/tmp/x_fin.xlsx').to_csv('/tmp/x_fin.csv', index=False)
print('✅ X and Y matrices localized')
                    "
                """
                
                // Pull all results back for the Engine stage
                sh "docker cp macro_processor:/tmp/y_unemp.csv data/y_unemp.csv"
                sh "docker cp macro_processor:/tmp/x_gap.csv data/x_gap.csv"
                sh "docker cp macro_processor:/tmp/x_fin.csv data/x_fin.csv"
                
                sh "docker rm -f macro_processor"
            }
        }   

        stage('Run Engine') {
            steps {
                echo "🧪 Running Structural Validation..."
                sh "docker run --rm --user 0:0 -v ${WORKSPACE}:/home/spark macro-engine-local:latest pytest tests/test_model_load.py"
                
                echo "🚀 Running Engine: Solving for Add Factors (e)..."
                sh """
                    docker run --rm --user 0:0 \
                    -v ${WORKSPACE}/data:/home/spark/data \
                    -v ${WORKSPACE}/results:/home/spark/results \
                    -v ${WORKSPACE}/models:/home/spark/models \
                    macro-engine-local:latest python3 src/engine.py
                """
            }
        }
    post {
        always {
            echo "📦 Archiving Build #53 Artifacts..."
            // Archive the residuals report, the structural analysis, and the test results
            archiveArtifacts artifacts: 'results/*.csv, data/*.csv, test-reports/*.xml', 
                             fingerprint: true, 
                             allowEmptyArchive: false
        }
        success {
            echo "✅ Build #53 Successful: Structural residuals isolated."
        }
        failure {
            echo "❌ Build #53 Failed. Checking logs for SolverStalled or PathErrors..."
        }
    }
}