properties([
    parameters([
        string(name: 'JENKINS_SERVER_URL', defaultValue:'', description: 'Pass your Jenkins Server URL'),
        string(name: 'USERNAME', defaultValue: '', description: 'Jenkins Username that has view access of jobs'),
        string(name: 'TOKEN', defaultValue: '', description: 'Above Username password or token'),
        string(name: 'SSL_VERIFICATION', defaultValue: 'false', description: 'SSL Verification with APIs')
    ])
])

params.each { k, v -> env[k] = v }

pipeline{

    agent 'any'

    stages{
        stage("Prepare The Reports"){
            steps{
                sh "python -m venv .venv"
                sh "source .venv/bin/activate; python generate_report.py"
            }
        }
        stage("Archive the Artifacts"){
            steps{
                archiveArtifacts 'reports/*.html'
            }
        }
    }
}
