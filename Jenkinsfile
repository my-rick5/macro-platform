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
                    sh "[ -f data/library.xlsx ] || cp data/tealbook_raw.xlsx data/library.xlsx"
                }
            }
        }
        stage('Build & Run Engine') {
            steps {
                script {
                    sh "docker build -t macro-engine-image:${env.BUILD_NUMBER} ."
                    sh "docker run -d --name engine-${env.BUILD_NUMBER} macro-engine-image:${env.BUILD_NUMBER} sleep 1200"
                    try {
                        echo "⚙️ Running Preprocessor..."
                        sh "docker exec -w /home/spark engine-${env.BUILD_NUMBER} python3 src/preprocess.py"
                        
                        echo "🚀 Heartbeat: Running Full Calibration Engine (init_trac)..."
                        sh "docker exec -w /home/spark engine-${env.BUILD_NUMBER} python3 src/engine.py"
                        
                        echo "🧹 Generating Lite Version & Visuals..."
                        sh """
                        docker exec -i engine-${env.BUILD_NUMBER} python3 -u - <<-EOF
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os

# FIX: Force Pandas to show all columns without "..." truncation
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

file_path = 'results/calibration_residuals_e.csv'
if os.path.exists(file_path):
    df = pd.read_csv(file_path)
    if 'date' in df.columns:
        df.index = pd.PeriodIndex(df['date'], freq='Q').to_timestamp()
        df.drop(columns=['date'], inplace=True)

    mapping = {
        'anngr': 'GDP Growth Resid',
        'delrff': 'Fed Funds Resid',
        'adjlegrt': 'Labor/Unemp Resid',
        'ddockm': 'Import Resid',
        'ddockx': 'Export Resid'
    }
    
    present = [c for c in mapping.keys() if c in df.columns]

    if present:
        lite_df = df[present].tail(40).rename(columns=mapping)
        lite_df.to_csv('results/lite_residuals.csv')
        
        print('\\n' + '='*30 + '\\n📊 FULL TARGET STATISTICS\\n' + '='*30)
        print(lite_df.describe())
        sys.stdout.flush()

        plt.figure(figsize=(12, 7))
        lite_df.plot(ax=plt.gca(), marker='o', alpha=0.7)
        plt.title('Macro Residuals: Historical Fit (1989-2019)')
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.savefig('results/residual_plot.png')
        print('\\n✅ Visuals and Lite CSV created.')
    else:
        print('⚠️ Warning: No target variables found.')
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