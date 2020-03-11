node('docker') {
    ansiColor('xterm') {
        step([$class: 'WsCleanup'])
        step([$class: 'StashNotifier'])
        def credentials = [
                        jenkins  : '45d976f8-a1fb-4b55-892e-a7add19dc44f',
                        bitbucket: '45d976f8-a1fb-4b55-892e-a7add19dc44f',
                        vault: 'svcJenkinsProdUser',
                        registryCredentialsId: 'svcJenkinsProdUser'
                        ]
         // set credential for get secret from Vault
        withCredentials([usernamePassword(credentialsId: credentials.vault, usernameVariable: 'JenkinsUser', passwordVariable: 'JenkinsPassword')]) {
            env.VAULT_ADDR = 'https://vault.yamoney.ru'
            env.VAULT_AUTHTYPE = 'ldap'
            env.VAULT_USER = "${JenkinsUser}"
            env.VAULT_PASSWORD = "${JenkinsPassword}"
        }
        def helm_image = 'docker-ym.nexus.yamoney.ru/yamoney/helm-kubectl:3.1.1'
        def registry = 'docker-ym.nexus.yamoney.ru'
        def image = 'xerxes-informer'
        def home_dir = '/var/lib/jenkins/workspace/Common/YMreleaseBot-deploy'
        echo repoPath
        echo branchName
        echo projectKey
        echo repoName
        try {
            stage('docker build && push') {
                checkout changelog: false, poll: false, scm: [$class: 'GitSCM', branches: [[name: '*/deploy']],
                extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: '.']],
                userRemoteConfigs: [[credentialsId: credentials.bitbucket, url: repoPath]]]
                //checkout scm
                def commit_id = sh(script:"git rev-parse --short HEAD", returnStdout: true).trim()
                def prepare_tag_yaml = ["ymreleasebot": ["tag": commit_id]]
                writeYaml file: 'tag-values.yaml', data: prepare_tag_yaml
                withDockerRegistry([ url: "https://${registry}", credentialsId: credentials.registryCredentialsId ]) {
                    def image_build = docker.build("${registry}/yamoney/${image}:${commit_id}", "-f Dockerfile --pull .")
                    image_build.push()
                }
            }
            stage('get secret from vault') {
                dir('ansible') {
                    git url: 'ssh://git@bitbucket.yamoney.ru/ansible-playbooks/ymreleasebot_get_secret.git',
                    credentialsId: credentials.bitbucket
                }
                ansiColor('xterm') {
                    ansiblePlaybook credentialsId: credentials.jenkins,
                        playbook: 'ansible/site.yml'
                }
            }
            stage('helm lint') {
                docker.image(helm_image).inside('-v /var/lib/jenkins/workspace/Common/YMreleaseBot-deploy/ansible/secret_vars/kube_config.yml:/opt/ymreleasebot/kube_config.yml -v /var/lib/jenkins/workspace/Common/YMreleaseBot-deploy/ansible/secret_vars/values.yaml:/opt/ymreleasebot/secret_values.yaml -v /var/lib/jenkins/workspace/Common/YMreleaseBot-deploy/deploy/:/opt/ymreleasebot/ -v /var/lib/jenkins/workspace/Common/YMreleaseBot-deploy/tag-values.yaml:/opt/ymreleasebot/tag-values.yaml') {
                 sh '''
                 cd /opt/ymreleasebot &&
                 helm lint . --kubeconfig /opt/ymreleasebot/kube_config.yml -f values.yaml -f tag-values.yaml -f secret_values.yaml
                 '''
                 }
            }
            stage('verify existence ns') {
                docker.image(helm_image).inside('-v /var/lib/jenkins/workspace/Common/YMreleaseBot-deploy/ansible/secret_vars/kube_config.yml:/opt/ymreleasebot/kube_config.yml') {
                sh '''
                kubectl --kubeconfig=/opt/ymreleasebot/kube_config.yml get namespace ymreleasebot || kubectl --kubeconfig=/opt/ymreleasebot/kube_config.yml create namespace ymreleasebot
                '''
                }
            }
            stage('helm install') {
                docker.image(helm_image).inside('-v /var/lib/jenkins/workspace/Common/YMreleaseBot-deploy/ansible/secret_vars/kube_config.yml:/opt/ymreleasebot/kube_config.yml -v /var/lib/jenkins/workspace/Common/YMreleaseBot-deploy/ansible/secret_vars/values.yaml:/opt/ymreleasebot/secret_values.yaml -v /var/lib/jenkins/workspace/Common/YMreleaseBot-deploy/deploy/:/opt/ymreleasebot/ -v /var/lib/jenkins/workspace/Common/YMreleaseBot-deploy/tag-values.yaml:/opt/ymreleasebot/tag-values.yaml') {
                 sh '''
                 cd /opt/ymreleasebot &&
                 helm upgrade --install  ${repoName} . --kubeconfig /opt/ymreleasebot/kube_config.yml -f values.yaml -f tag-values.yaml -f secret_values.yaml --debug -n ymreleasebot
                 '''
                 }
            }
        currentBuild.result = 'SUCCESS'
        currentBuild.displayName += " " + projectKey + "/" + repoName + ":" + branchName
        step([$class: 'StashNotifier'])
        } catch(Exception e) {
        println "Error: ${e.message}"
        currentBuild.result = 'FAILED'
        } finally {
            sh '''
            rm -rf /var/lib/jenkins/workspace/Common/YMreleaseBot-deploy/ansible/secret_vars
            '''
        }
    }
}