pipeline {
    agent any

    environment {
        PYTHONPATH = "/home/spark:/home/spark/src"
    }

    stages {
        stage('Initialize') {
            steps {
                script {
                    sh "mkdir -p results data data/processed external_data"
                    // Alias Tealbook as Library if needed
                    sh "[ -f data/library.xlsx ] || cp data/tealbook_raw.xlsx data/library.xlsx"
                }
            }
        }

        stage('Build & Run Engine') {
            steps {
                script {
                    // Build the image using the local context
                    sh "docker build -t macro-engine-image:${env.BUILD_NUMBER} ."
                    
                    // Start container as a daemon
                    sh "docker run -d --name engine-${env.BUILD_NUMBER} macro-engine-image:${env.BUILD_NUMBER} sleep 1200"
                    
                    try {
                        echo "⚙️ Running Preprocessor..."
                        sh "docker exec -w /home/spark engine-${env.BUILD_NUMBER} python3 src/preprocess.py"
                        
                        echo "🚀 Heartbeat: Running Full Calibration Engine (init_trac)..."
                        // We run the script you provided via docker exec
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
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)

    # Internal Engine Mapping (Targets from your logs)
    mapping = {
        'anngr': 'GDP Growth Resid',
        'delrff': 'Fed Funds Resid',
        'adjlegrt': 'Labor/Unemp Resid',
        'ddockm': 'Import Resid',
        'ddockx': 'Export Resid'
    }
    
    present = [c for c in mapping.keys() if c in df.columns]

    if present:
        # Filter for the last 40 quarters to make visuals interpretable
        lite_df = df[present].tail(40)
        lite_df.rename(columns=mapping, inplace=True)
        lite_df.to_csv('results/lite_residuals.csv')
        
        print('\\n' + '='*30 + '\\n📊 LITE STATISTICS (Last 10Y)\\n' + '='*30)
        print(lite_df.describe())
        sys.stdout.flush()

        plt.figure(figsize=(10, 6))
        lite_df.plot(marker='o')
        plt.title('Key Macro Residuals (Historical Calibration Window)')
        plt.ylabel('Residual Value')
        plt.grid(True, alpha=0.3)
        plt.savefig('results/residual_plot.png')
        print('\\n✅ Visuals and Lite CSV created.')
    else:
        print(f'⚠️ Warning: No targets found. Available columns: {df.columns.tolist()[:10]}')
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
    print('\\n' + '='*30 + '\\n🕒 TIME-SERIES BOUNDS\\n' + '='*30)
    print(f'Start Period: {df.iloc[0, 0]}')
    print(f'End Period:   {df.iloc[-1, 0]}')
    
    variation = df.iloc[:, 1:].std().sum()
    print(f'\\nTotal Variation: {variation}')
    if variation < 1e-10:
        print('🚨 ALERT: Residuals are flat. Engine might be solving in steady-state only.')
EOF
                        """
                        
                        // Extract everything to the Jenkins Host
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
            // Archive the raw results, the lite CSV, and the visual PNG
            archiveArtifacts artifacts: 'results/*', allowEmptyArchive: true
        }
    }
}