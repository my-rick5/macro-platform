pipeline {
    agent any

    environment {
        PYTHONPATH = "/home/spark:/home/spark/src"
    }

    stages {
        stage('Initialize') {
            steps {
                script {
                    sh "mkdir -p results data"
                    // Alias Tealbook as Library if needed
                    sh "[ -f data/library.xlsx ] || cp data/tealbook_raw.xlsx data/library.xlsx"
                }
            }
        }

        stage('Build & Run Engine') {
            steps {
                script {
                    sh "docker build -t macro-engine-image:${env.BUILD_NUMBER} ."
                    sh "docker run -d --name engine-${env.BUILD_NUMBER} macro-engine-image:${env.BUILD_NUMBER} sleep 900"
                    
                    try {
                        echo "⚙️ Running Preprocessor & Model..."
                        sh "docker exec -w /home/spark engine-${env.BUILD_NUMBER} python3 src/preprocess.py"
                        sh "docker exec -w /home/spark engine-${env.BUILD_NUMBER} python3 src/engine.py"
                        
                        echo "🧹 Generating Lite Version & Visuals..."
                        sh """
                        docker exec -i engine-${env.BUILD_NUMBER} python3 -u - <<-EOF
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os

file_path = 'results/calibration_residuals_e.csv'
if os.path.exists(file_path):
    df = pd.read_csv(file_path)
    
    # Internal Engine Mapping
    mapping = {
        'anngr': 'GDP Growth Resid',
        'delrff': 'Fed Funds Resid',
        'adjlegrt': 'Labor/Unemp Resid',
        'ddockm': 'Import Resid',
        'ddockx': 'Export Resid'
    }
    
    present = [c for c in mapping.keys() if c in df.columns]

    if present:
        lite_df = df[present].dropna(how='all').tail(40)
        lite_df.rename(columns=mapping, inplace=True)
        lite_df.to_csv('results/lite_residuals.csv', index=False)
        
        print('\\n' + '='*30 + '\\n📊 LITE STATISTICS\\n' + '='*30)
        print(lite_df.describe())
        sys.stdout.flush()

        plt.figure(figsize=(10, 6))
        lite_df.plot(marker='o')
        plt.title('Key Macro Residuals (Engine Internal Names)')
        plt.grid(True)
        plt.savefig('results/residual_plot.png')
        print('\\n✅ Visuals and Lite CSV created.')
    else:
        print(f'⚠️ Warning: No targets found. Columns: {df.columns.tolist()[:10]}')
EOF
                        """

                        echo "🕵️ Running Engine Diagnostics..."
                        sh """
                        docker exec -i engine-${env.BUILD_NUMBER} python3 -u - <<-EOF
import pandas as pd
import os

res_path = 'results/calibration_residuals_e.csv'
if os.path.exists(res_path):
    df = pd.read_csv(res_path)
    print('\\n' + '='*30 + '\\n🕒 TIME-SERIES DIAGNOSTIC\\n' + '='*30)
    print('First 3 dates:\\n', df[['date']].head(3))
    print('Last 3 dates:\\n', df[['date']].tail(3))
    
    # Measure Variation: If this is 0.0, the engine is stuck
    variation = df.iloc[:, 1:].std().sum()
    print(f'\\nTotal Numerical Variation: {variation}')
    if variation < 1e-9:
        print('🚨 ALERT: Residuals are perfectly flat. The solver is not iterating.')
EOF
                        """
                        
                        sh "docker cp engine-${env.BUILD_NUMBER}:/home/spark/results/. ./results/"
                        
                    } finally {
                        sh "docker rm -f engine-${env.BUILD_NUMBER} || true"
                    }
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'results/*', allowEmptyArchive: true
        }
    }
}