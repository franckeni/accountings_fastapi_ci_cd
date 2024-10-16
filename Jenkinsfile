def CONFIG = getConfig(env.BUILD_NUMBER, env.BRANCH_NAME)
def ENV_NAME = CONFIG['envName']
def CONTAINER_TAG = CONFIG['tag']
def HTTP_PORT = CONFIG['httPort']
def CURRENT_USER = CONFIG['currentUser']
def DYNAMODB_URL = CONFIG['dynamodbUrl']
def defaultHost = CONFIG['defaultHost']

def CONTAINER_NAME = "accountings-api-" + ENV_NAME
def POETRY_VERSION = "1.8.2"
def EMAIL_RECIPIENTS = "franckafosoule@gmail.com"


properties([
  parameters([
    choice(
      name: 'PYTHON',
      description: 'Choose Python version',
      choices: ["3.12", "3.11", "3.10"].join("\n"),
    ),
    base64File(
      name: 'REQUIREMENTS_FILE',
      description: 'Upload requirements file (Optional)'
    )
  ])
])


pipeline {
    environment {
        DOCKERHUB_ID = credentials('DOCKERHUB_ID')
        dockerHome = tool "DockerLocalhost"
        terraform = tool "terraformAccountings"
        pysonarCredential = credentials('sonarqubeToken')
        PATH = "$terraform:$dockerHome/bin:$PATH"
        ADMIN_EMAIL = "franckafosoule@gmail.com"
        APP_VERSION = "0.1.0"
        API_PATH_VERSION_PREFIX = "/api/v1"
        ALLOWED_ORIGINS ='http://localhost:4200,http://localhost:4000'
        TABLE_NAME = "accounting-erp-${ENV_NAME}"
        DOCKER_NETWORK = "haen_stam_network"
        ANSIBLE_RESOURCES = 'src/shared/infrastructure/ansible_resources'
        DOCKER_RESOURCES = 'src/shared/infrastructure/docker'
        ANSIBLE_CONFIG = "${WORKSPACE}/ansible.cfg"
        API_CONTAINER_NAME = "$DOCKERHUB_ID-${CONTAINER_NAME}"
        DOCKER_CURRENT_IMAGE = "$DOCKERHUB_ID/${CONTAINER_NAME}:${CONTAINER_TAG}"

        AWS_USERPOOLID = "${env.BRANCH_NAME == 'main' ? credentials('AWS_USERPOOLID') : 'devAwsCred'}"
        AWS_USERPOOLWEBCLIENTID = "${env.BRANCH_NAME == 'main' ? credentials('AWS_USERPOOLWEBCLIENTID') : 'devAwsCred'}"
        AWS_ACCESS_KEY_ID = "${env.BRANCH_NAME == 'main' ? credentials('AWS_ACCESS_KEY_ID') : 'devAwsCred'}"
        AWS_SECRET_ACCESS_KEY = "${env.BRANCH_NAME == 'main' ? credentials('AWS_SECRET_ACCESS_KEY') : 'devAwsCred'}"
        AWS_DEFAULT_REGION = "eu-west-3"
    }
    agent any
    options {
        buildDiscarder(logRotator(numToKeepStr: '5'))
        timeout(time: 60, unit:'MINUTES')
        timestamps()
    }
    stages {
        stage("Initialize") {
            steps {
                script {
                    echo "${BUILD_NUMBER} - ${env.BUILD_ID} on ${env.JENKINS_URL}"
                    echo "branch Specifier :: ${env.BRANCH_NAME}"
                }
            }
        }

        stage('Checkout') {
            steps {
                checkout scm
                sh 'ls -la'
            }
        }

        stage ('Clean Working directory before') {
            steps {
                imagePrune(CONTAINER_NAME, DOCKERHUB_ID)
                imagePruneWithPlaybook(CONTAINER_NAME, DOCKERHUB_ID)
            }
        }

        // Both PROD and DEV or UAT 
        stage ('Install Ansible role dependencies') {
            steps {
                sh '''
                    export ANSIBLE_CONFIG=${WORKSPACE}/ansible.cfg
                '''
                sh "ansible-galaxy install -r ${WORKSPACE}/${ANSIBLE_RESOURCES}/roles/requirements.yml"
            }
        }

        // Both PROD and DEV or UAT 
        stage('Make Virtual Env and run the Test') {
            steps {
                withPythonEnv("/usr/bin/python${params.PYTHON}") {
                    script {
                        poetryConfigAndInstall(params.PYTHON, POETRY_VERSION, WORKSPACE)
                        runTest(WORKSPACE)
                    }
                }
            }
        }

        stage("Sonarqube Analysis"){
            steps{
                withPythonEnv("/usr/bin/python${params.PYTHON}") {
                    script {
                        def sonarqubeScannerHome = tool 'sonarqubeScanner'
                        echo "SonarQube Scanner installation directory: ${sonarqubeScannerHome}"
                        withSonarQubeEnv('sonaqubeServer') {
                            sh "${sonarqubeScannerHome}/bin/sonar-scanner"
                        }
                        timeout(time: 1, unit: 'MINUTES') {
                            def wfqg = waitForQualityGate()
                            if (wfqg.status != 'OK') {
                                error "Pipeline aborted due to quality gate failure: ${wfqg.status}"
                            }
                        }
                    }
                }
            }
        }
        
        // Only DEV or UAT
        stage ('Ping hosts before installing Docker on Dev or UAT') {
            when {
                branch 'develop'
            }
            stages {
                stage ('Test ping on current hosts') {
                    steps {
                        ansiblePlaybook credentialsId: '',
                            disableHostKeyChecking: true,
                            installation: 'Ansible',
                            inventory: '${WORKSPACE}/${ANSIBLE_RESOURCES}/hosts.yml', 
                            playbook: '${WORKSPACE}/${ANSIBLE_RESOURCES}/playbooks/ping_servers.yml',
                            limit: "${defaultHost}"
                    }
                }

                // Only DEV or UAT
                stage ('Install docker on hosts') {
                    steps {
                        ansiblePlaybook credentialsId: '',
                            disableHostKeyChecking: true,
                            installation: 'Ansible',
                            inventory: '${WORKSPACE}/${ANSIBLE_RESOURCES}/hosts.yml',
                            playbook: '${WORKSPACE}/${ANSIBLE_RESOURCES}/playbooks/install_docker.yml',
                            limit: "${defaultHost}"
                    }
                }

                // Only DEV or UAT
                stage ('Create network') {
                    steps {
                        ansiblePlaybook credentialsId: '',
                            disableHostKeyChecking: true, 
                            extras:
                                "-e APP_ENVIRONMENT=${ENV_NAME} -e AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION} " +
                                "-e DOCKER_NETWORK=${DOCKER_NETWORK}",
                            installation: 'Ansible',
                            inventory: '${WORKSPACE}/${ANSIBLE_RESOURCES}/hosts.yml', 
                            playbook: '${WORKSPACE}/${ANSIBLE_RESOURCES}/playbooks/create_network.yml',
                            limit: "${defaultHost}"
                    }
                }
            }
        }

        // Both PROD and DEV or UAT 
        stage ('Build Python FAstAPI Image and Push It to DockerHUB') {
            steps {
                script {
                    docker.withRegistry('', 'DOCKERHUB_CREDENTIAL') {
                        def dockerImage = docker.build("${DOCKER_CURRENT_IMAGE}", 
                            "--build-arg CURRENT_USER=${CURRENT_USER} --network=host --pull --no-cache \
                            -f ${env.WORKSPACE}/${DOCKER_RESOURCES}/Dockerfile  .")
                        dockerImage.push();
                        dockerImage.push('latest');
                    }
                }
            }
        }

        // Only DEV or UAT
        stage ('Deploy Python FastAPI on DEv or UAT') {
            when {
                branch 'develop'
            }
            steps {
                ansiblePlaybook credentialsId: '',
                    disableHostKeyChecking: true,
                    extras: 
                        "-e DOCKER_CURRENT_IMAGE=${DOCKER_CURRENT_IMAGE} " + 
                        "-e APP_ENVIRONMENT=${ENV_NAME} -e AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} " + 
                        "-e APP_VERSION=${APP_VERSION} -e API_PATH_VERSION_PREFIX=${API_PATH_VERSION_PREFIX} " +
                        "-e API_CONTAINER_NAME=${API_CONTAINER_NAME} -e ADMIN_EMAIL=${ADMIN_EMAIL} " +
                        "-e AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} -e AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION} " +
                        "-e AWS_USERPOOLID=${AWS_USERPOOLID} -e AWS_USERPOOLWEBCLIENTID=${AWS_USERPOOLWEBCLIENTID}",
                    installation: 'Ansible',
                    inventory: '${WORKSPACE}/${ANSIBLE_RESOURCES}/hosts.yml', 
                    playbook: '${WORKSPACE}/${ANSIBLE_RESOURCES}/playbooks/deploy_api.yml',
                    limit: "${defaultHost}"
            }
        }
        
        // Only DEV or UAT
        stage ('Test UAT image') {
            when {
                branch 'develop'
            }
            agent any
            steps {
                script {
                    sh "curl -I -X 'GET' http://192.168.56.11:8080/api/v1/health-check | grep -i '200'"
                }
            }
        }

        // Only PROD
        stage ('Deploy FastAPI to PROD env') {
            when {
                branch 'main'
            }
            stages {
                stage ('Provision EC2 on AWS with terraform') {
                    environment {
                        AWS_ACCESS_KEY_ID = credentials('AWS_ACCESS_KEY_ID')
                        AWS_SECRET_ACCESS_KEY = credentials('AWS_SECRET_ACCESS_KEY')
                        AWS_DEFAULT_REGION = "${AWS_DEFAULT_REGION}"
                        AWS_PRIVATE_EC2_KEY = credentials('AWS_PRIVATE_EC2_KEY')
                    }
                    steps {
                        script {
                            sh '''
                                echo "Delete older and Generate new aws credentials"
                                rm -rf ~/.ssh/accountings.pem ~/.aws
                                mkdir -p ~/.aws
                                echo "[default]" > ~/.aws/credentials
                                echo AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID >> ~/.aws/credentials
                                echo AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY >> ~/.aws/credentials
                                echo AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION >> ~/.aws/credentials
                                chmod 400 ~/.aws/credentials
                                echo "Copy aws private key"
                                cp $AWS_PRIVATE_EC2_KEY ~/.ssh/accountings.pem
                                chmod 400 ~/.ssh/accountings.pem
                                ssh-agent bash
                                ssh-add ~/.ssh/accountings.pem
                                cd "./src/shared/infrastructure/terraform_resources/prod"
                                terraform init
                                terraform apply --auto-approve
                            '''
                        }
                    }
                }

                stage ('Prepare Ansible environment for Prod') {
                    steps {
                        script {
                            sh '''
                                echo "Generating host_vars for EC2 servers"
                                echo "ansible_host: $(awk '{print $2}' ${WORKSPACE}/public_ip.txt)" > ${ANSIBLE_RESOURCES}/host_vars/api_prod.yml
                                echo "ansible_ssh_private_key_file: './accountings.pem'" >> ${ANSIBLE_RESOURCES}/host_vars/api_prod.yml
                            '''
                        }
                    }
                }

                stage ('Test ping on AWS hosts') {
                    steps {
                        dir('/var/jenkins_home/.ssh/') {
                            sh 'ls -la'
                            ansiblePlaybook credentialsId: '',
                                disableHostKeyChecking: true,
                                installation: 'Ansible',
                                inventory: '${WORKSPACE}/${ANSIBLE_RESOURCES}/hosts.yml', 
                                playbook: '${WORKSPACE}/${ANSIBLE_RESOURCES}/playbooks/ping_servers.yml',
                                limit: "${defaultHost}"
                        }
                    }
                }

                stage ('Install docker on hosts') {
                    steps {
                        ansiblePlaybook credentialsId: '',
                            disableHostKeyChecking: true,
                            installation: 'Ansible',
                            inventory: '${WORKSPACE}/${ANSIBLE_RESOURCES}/hosts.yml',
                            playbook: '${WORKSPACE}/${ANSIBLE_RESOURCES}/playbooks/install_docker.yml',
                            limit: "${defaultHost}"
                    }
                }

                stage ('Create network') {
                    steps {
                        ansiblePlaybook credentialsId: '',
                            disableHostKeyChecking: true, 
                            extras:
                                "-e APP_ENVIRONMENT=${ENV_NAME} -e AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION} " +
                                "-e DOCKER_NETWORK=${DOCKER_NETWORK}",
                            installation: 'Ansible',
                            inventory: '${WORKSPACE}/${ANSIBLE_RESOURCES}/hosts.yml', 
                            playbook: '${WORKSPACE}/${ANSIBLE_RESOURCES}/playbooks/create_network.yml',
                            limit: "${defaultHost}"
                    }
                }

                stage ('Deploy Python FastAPI to Prod') {
                    steps {
                        ansiblePlaybook credentialsId: '',
                            disableHostKeyChecking: true,
                            extras:
                                "-e DOCKER_CURRENT_IMAGE=${DOCKER_CURRENT_IMAGE} " + 
                                "-e APP_ENVIRONMENT=${ENV_NAME} -e AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} " + 
                                "-e APP_VERSION=${APP_VERSION} -e API_PATH_VERSION_PREFIX=${API_PATH_VERSION_PREFIX} " +
                                "-e API_CONTAINER_NAME=${API_CONTAINER_NAME} -e ADMIN_EMAIL=${ADMIN_EMAIL} " +
                                "-e AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} -e AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION} " +
                                "-e AWS_USERPOOLID=${AWS_USERPOOLID} -e AWS_USERPOOLWEBCLIENTID=${AWS_USERPOOLWEBCLIENTID}",
                            installation: 'Ansible',
                            inventory: '${WORKSPACE}/${ANSIBLE_RESOURCES}/hosts.yml', 
                            playbook: '${WORKSPACE}/${ANSIBLE_RESOURCES}/playbooks/deploy_api.yml',
                            limit: "${defaultHost}"
                    }
                }
            }
        }

        stage ('Clean Working directory after') {
            steps {
                imagePrune(CONTAINER_NAME, DOCKERHUB_ID)
                imagePruneWithPlaybook(CONTAINER_NAME, DOCKERHUB_ID)
            }
        }

        stage ('Delete EC2 resources on AWS') {
            when {
                branch 'main'
            }
            steps {
                script {
                    timeout(time: 30, unit: "MINUTES") {
                        input message: "Confirmer la suppression dans AWS ?", ok: 'Yes'
                    }
                    sh '''
                        cd "./src/shared/infrastructure/terraform_resources/prod"
                        terraform destroy --auto-approve
                        rm -rf ~/.ssh/accountings.pem
                        rm  /.terraform.lock.hcl
                    '''
                }
            }
        }

    }
    post {
        always {
            echo 'Backend FAstAPI build'
        }
        success {
            echo 'Backend FAstAPI build Done Successfully'
        }
        failure {
            echo 'Backend FAstAPI build Done with failure'
        }
    }
}

def terraformBefore() {
    try {
        sh "terraform destroy --auto-approve"
    } catch (ignored) {}
}

def imagePruneWithPlaybook(containerName, dockerHubId) {
    try {
        ansiblePlaybook credentialsId: '', 
            disableHostKeyChecking: true, 
            extras: "-e DELETE_IMAGES_REFERENCE=$dockerHubId/$containerName", 
            installation: 'Ansible',
            inventory: '${WORKSPACE}/${ANSIBLE_RESOURCES}/hosts.yml', 
            playbook: '${WORKSPACE}/${ANSIBLE_RESOURCES}/playbooks/docker_rmi_unused.yml',
            limit: 'api_dev'
    } catch (ignored) {}
}

def imagePrune(containerName, dockerHubId) {
    try {
        sh "docker images -q -f dangling=true | xargs --no-run-if-empty docker rmi -f"
        sh "docker images -q -f reference=$dockerHubId/$containerName | xargs --no-run-if-empty docker rmi -f"
        sh "docker images -q -f reference=none | xargs --no-run-if-empty docker rmi -f"
        sh 'docker ps -q -f status=exited | xargs --no-run-if-empty docker rm'
        sh 'docker volume ls -qf dangling=true | xargs -r docker volume rm'
        sh "docker stop $dockerHubId-$containerName"
        sh "docker system prune -f -a"
    } catch (ignored) {}
}

def runTest(workspace) {
    sh "envsubst < $workspace/.env.temp > $workspace/.env"
    sh "poetry run pytest -v --cov=./ --cov-report=xml"
}

def poetryConfigAndInstall(pythonVersion, poetryVersion, workspace) {
    sh "pip$pythonVersion install poetry==$poetryVersion \
        && poetry config virtualenvs.in-project true \
        && poetry config virtualenvs.path $workspace \
        && poetry install --no-root --no-ansi --no-interaction"
}

def sendEmail(recipients) {
    mail(
        to: recipients,
        subject: "Build ${env.BUILD_NUMBER} - ${currentBuild.currentResult} - (${currentBuild.fullDisplayNames})",
        body: "Check console output at: ${env.BUILD_URL}/console" + "\n"
    )
}

def getConfig(builderNumber, branchName) {
    if (branchName == 'main') {
        return [
            tag: 'latest',
            currentUSer: 'ec2-user',
            httPort: '8080',
            envName: 'prod',
            dynamodbUrl: '',
            defaultHost: 'api_prod'
        ]
    }

    return [
            tag: builderNumber + '-unstable',
            currentUSer: 'vagrant',
            httPort: (branchName == 'develop') ? '8082' : '8083',
            envName: (branchName == 'develop') ? 'dev' : 'uat',
            dynamodbUrl: (branchName == 'develop') ? 'http://192.165.56.11:8000' : 'http://localhost:8000',
            defaultHost: 'api_dev'
    ]
}
