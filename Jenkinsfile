pipeline {
    agent any

    environment {
        // Ensuring the container knows where its own code is
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
                    // Build the image using the local context
                    sh "docker build -t macro-engine-image:${env.BUILD_NUMBER} ."
                    
                    // Start container as a daemon
                    sh "docker run -d --name engine-${env.BUILD_NUMBER} macro-engine-image:${env.BUILD_NUMBER} sleep 600"
                    
                    try {
                        echo "⚙️ Preprocessing & Running Model..."
                        sh "docker exec -w /home/spark engine-${env.BUILD_NUMBER} python3 src/preprocess.py"
                        sh "docker exec -w /home/spark engine-${env.BUILD_NUMBER} python3 src/engine.py"
                        
                        echo "🧹 Generating Lite Version & Visuals (Inside Docker)..."
                        sh """
                        docker exec -i engine-${env.BUILD_NUMBER} python3 -u - <<-EOF
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os

file_path = 'results/calibration_residuals_e.csv'
if os.path.exists(file_path):
    df = pd.read_csv(file_path)
    
    # Mapping engine names to readable labels
    mapping = {
        'anngr': 'GDP Growth Resid',
        'delrff': 'Fed Funds Resid',
        'adjlegrt': 'Labor/Unemp Resid',
        'ddockm': 'Import Resid',
        'ddockx': 'Export Resid'
    }
    
    # Filter for what actually exists in the file
    present_targets = [c for c in mapping.keys() if c in df.columns]

    if present_targets:
        # Create Lite Version (Last 40 quarters)
        lite_df = df[present_targets].dropna(how='all').tail(40)
        
        # Rename columns for the Lite CSV and Plot
        lite_df.rename(columns=mapping, inplace=True)
        lite_df.to_csv('results/lite_residuals.csv', index=False)
        
        print('\\n' + '='*30 + '\\n📊 LITE STATISTICS\\n' + '='*30)
        print(lite_df.describe())
        sys.stdout.flush()

        # Create Visuals
        plt.figure(figsize=(12, 7))
        lite_df.plot(marker='o', alpha=0.8)
        plt.title('Key Macro Residuals (Engine Internal Names)')
        plt.ylabel('Residual Value')
        plt.legend(loc='best', fontsize='small')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        plt.savefig('results/residual_plot.png')
        print('\\n✅ Visuals and Lite CSV created.')
    else:
        print(f'⚠️ Warning: No targets found. Columns found: {df.columns.tolist()[:15]}')
else:
    print('❌ Error: Raw results file not found!')
EOF
                        """
                        
                        // Copy everything back to the host before cleaning up
                        sh "docker cp engine-${env.BUILD_NUMBER}:/home/spark/results/. ./results/"
                        
                    } finally {
                        // Ensure container is always removed
                        sh "docker rm -f engine-${env.BUILD_NUMBER} || true"
                    }
                }
            }
        }
    }

    post {
        always {
            // Archive all results, including the large raw file and the new visual plot
            archiveArtifacts artifacts: 'results/*', allowEmptyArchive: true
        }
    }
}