node('docker') {
    ansiColor('xterm') {
        cleanWs()
        def dockerImageUrl = "docker.nexus.yooteam.ru/yamoney/ubuntu-18-04-ym-cloud"
        def registry = 'docker-ym.nexus.yooteam.ru'
        def image = 'releasebot-informer'
        def home_dir = '/var/lib/jenkins/workspace/Common/releasebot/informer'
        def image_version = "0.${BUILD_NUMBER}"
        def credentials = [
                        jenkins  : '45d976f8-a1fb-4b55-892e-a7add19dc44f',
                        bitbucket: '45d976f8-a1fb-4b55-892e-a7add19dc44f',
                        vault: 'svcJenkinsProdUser',
                        registryCredentialsId: 'svcJenkinsProdUser'
                        ]
        try {
            docker.image("${dockerImageUrl}").inside("-v /var/run/docker.sock:/var/run/docker.sock --net=host --group-add docker") {
                stage('docker build && push') {
                    echo 'Fetching repo'
                    checkout ([$class: 'GitSCM',
                        branches: [[name: branchName]],
                        extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: '']],
                        userRemoteConfigs: [[credentialsId: credentials.bitbucket,
                        url: 'ssh://git@bitbucket.yooteam.ru/admin-tools/releasebot-informer.git']]])

                    echo 'Build & push docker image'
                    def commit_id = sh(script:"git rev-parse --short HEAD", returnStdout: true).trim()
                    def prepare_tag_yaml = ["releasebot": ["tag": image_version]]
                    writeYaml file: 'tag-values.yaml', data: prepare_tag_yaml
                    withDockerRegistry([ url: "https://${registry}", credentialsId: credentials.registryCredentialsId ]) {
                        def image_build = docker.build("${registry}/yamoney/${image}", "-f Dockerfile --pull .")
                        image_build.push(image_version)
                        image_build.push('latest')
                    }
                    //notifyBitbucket(buildStatus: 'INPROGRESS')
                }
                stage('get secret from vault') {
                    // set credential for get secret from Vault
                    withCredentials([usernamePassword(credentialsId: credentials.vault, usernameVariable: 'JenkinsUser', passwordVariable: 'JenkinsPassword')]) {
                        env.VAULT_ADDR = 'https://vault.yooteam.ru'
                        env.VAULT_AUTHTYPE = 'ldap'
                        env.VAULT_USER = "${JenkinsUser}"
                        env.VAULT_PASSWORD = "${JenkinsPassword}"
                    }
                    ansiblePlaybook credentialsId: credentials.jenkins,
                                    playbook: './ansible/site.yml',
                                    colorized: true
                    //notifyBitbucket(buildStatus: 'INPROGRESS')
                }
                stage('helm lint') {
                    echo 'Linting helm'
                    sh '''
                    cd ./deploy &&
                    helm lint . --kubeconfig ../ansible/kubeconfig.yml -f values.yaml -f ../ansible/secret_values.yml -n releasebot
                    helm install --dry-run releasebot-informer . --kubeconfig ../ansible/kubeconfig.yml -f ../ansible/secret_values.yml -f ../tag-values.yaml -n releasebot
                    '''
                    notifyBitbucket(buildStatus: 'INPROGRESS')
                }
                stage('helm install') {
                    sh '''
                    cd ./deploy &&
                    helm upgrade --install releasebot-informer . --kubeconfig ../ansible/kubeconfig.yml -f ../ansible/secret_values.yml -f ../tag-values.yaml -n releasebot
                    '''
                }
                //notifyBitbucket(buildStatus: 'SUCCESSFUL')
                currentBuild.result = 'SUCCESS'
            }
        } catch(Exception e) {
                println "Error: ${e.message}"
                //notifyBitbucket(buildStatus: 'FAILED')
                currentBuild.result = 'FAILED'
        } finally {
                sh '''
                rm -rf ${home_dir}/ansible
                '''
        }
    }
}
